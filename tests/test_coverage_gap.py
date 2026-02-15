import errno
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.core.flow import (
    AnyNode,
    DataSchema,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    HumanNode,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.diff import ManifestDiff
from coreason_manifest.utils.integrity import (
    _recursive_sort_and_sanitize,
    compute_hash,
    reconstruct_payload,
    to_canonical_timestamp,
    verify_merkle_proof,
)
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError
from coreason_manifest.utils.loader import load_flow_from_file
from coreason_manifest.utils.visualizer import to_mermaid, to_react_flow


# --- Integrity Coverage ---
def test_canonical_timestamp_naive() -> None:
    # Line 15: if dt.tzinfo is None
    naive_dt = datetime(2023, 1, 1, 12, 0, 0)  # No tzinfo
    canonical = to_canonical_timestamp(naive_dt)
    assert canonical == "2023-01-01T12:00:00Z"


def test_recursive_sanitize_datetime() -> None:
    # Line 52: elif isinstance(obj, datetime)
    dt = datetime(2023, 1, 1, 12, 0, 0)
    data = {"date": dt}
    sanitized = _recursive_sort_and_sanitize(data)
    assert sanitized["date"] == "2023-01-01T12:00:00Z"


def test_recursive_sanitize_list() -> None:
    # Coverage for list handling
    data = [1, {"a": 2}]
    sanitized = _recursive_sort_and_sanitize(data)
    assert sanitized == [1, {"a": 2}]


def test_recursive_sanitize_set() -> None:
    # Coverage for set handling (Instruction 3)
    data = {3, 1, 2}
    sanitized = _recursive_sort_and_sanitize(data)
    # Must be sorted list
    assert sanitized == [1, 2, 3]


def test_recursive_sanitize_pydantic() -> None:
    # Coverage for Pydantic v2 (model_dump)
    class MyModel(BaseModel):
        x: int

    m = MyModel(x=1)
    sanitized = _recursive_sort_and_sanitize(m)
    assert sanitized == {"x": 1}


def test_recursive_sanitize_pydantic_v1() -> None:
    # Coverage for Pydantic v1 (dict) - Mocking since we are on v2
    class MockV1:
        def dict(self, exclude_none: bool = False) -> dict[str, Any]:
            if exclude_none:
                return {"v1": True}
            return {"v1": True}

    sanitized = _recursive_sort_and_sanitize(MockV1())
    assert sanitized == {"v1": True}


def test_recursive_sanitize_json_exception() -> None:
    # Coverage for .json() raising exception or returning invalid json
    class BrokenJson:
        def json(self) -> str:
            return "invalid-json{"

    # Should fall through and return the object itself (or str(obj) later)
    obj = BrokenJson()
    sanitized = _recursive_sort_and_sanitize(obj)
    assert sanitized is obj


def test_compute_hash_method() -> None:
    class HasHash:
        def compute_hash(self) -> str:
            return "custom_hash"

    assert compute_hash(HasHash()) == "custom_hash"


def test_reconstruct_payload_coverage() -> None:
    # Test branches in reconstruct_payload
    # Timestamp as datetime
    node1 = {"node_id": "1", "timestamp": datetime(2023, 1, 1, 12, 0, 0)}
    p1 = reconstruct_payload(node1)
    assert p1["timestamp"] == "2023-01-01T12:00:00Z"

    # Timestamp as str
    node2 = {"node_id": "2", "timestamp": "2023-01-01T12:00:00Z"}
    p2 = reconstruct_payload(node2)
    assert p2["timestamp"] == "2023-01-01T12:00:00Z"

    # Timestamp as other
    node3 = {"node_id": "3", "timestamp": 12345}
    p3 = reconstruct_payload(node3)
    assert p3["timestamp"] == "12345"


def test_verify_merkle_empty() -> None:
    assert verify_merkle_proof([]) is False


def test_verify_merkle_strict_object_attributes() -> None:
    # Test with objects having attributes instead of dicts
    # So we must use Pydantic models or mocks with model_dump
    class MockModel:
        def __init__(self, d: dict[str, Any]) -> None:
            self.d = d
            self.execution_hash = d.get("execution_hash")
            self.previous_hashes = d.get("previous_hashes", [])

        def model_dump(self) -> dict[str, Any]:
            return self.d

    # Valid chain
    # Note: reconstruct_payload adds default "attributes": {} which compute_hash includes.
    # So we must include it in our payload for hash computation to match.
    p1 = {"node_id": "1", "state": "s", "previous_hashes": [], "attributes": {}}
    h1 = compute_hash(p1)
    n1 = MockModel({**p1, "execution_hash": h1})

    assert verify_merkle_proof([n1]) is True

    # Trusted root mismatch
    assert verify_merkle_proof([n1], trusted_root_hash="wrong") is False

    # Trusted root match
    assert verify_merkle_proof([n1], trusted_root_hash=h1) is True


def test_verify_merkle_strict_trusted_parent_skip() -> None:
    # If prev_hash == trusted_root, we skip verification of it being in verified set
    # Genesis
    p1 = {"node_id": "1", "previous_hashes": [], "attributes": {}}
    h1 = compute_hash(p1)

    # Child
    p2 = {"node_id": "2", "previous_hashes": [h1], "attributes": {}}
    h2 = compute_hash(p2)
    n2 = {"execution_hash": h2, **p2}

    # Verify child only, with trusted root = h1
    # Note: Genesis logic at i=0 checks `if not previous_hashes`.
    # Here previous_hashes is NOT empty. So it goes to else.
    # So yes, we can verify a child block if we trust its parent.

    assert verify_merkle_proof([n2], trusted_root_hash=h1) is True


def test_verify_merkle_legacy_object_attributes() -> None:
    # Test legacy object with attributes
    class LegacyObj:
        def __init__(self, data: str, prev: str | None = None) -> None:
            self.data = data
            self.prev_hash = prev

        def compute_hash(self) -> str:
            return compute_hash(str(self))

        def __str__(self) -> str:
            return self.data

    # Genesis
    n1 = LegacyObj("gen")
    h1 = compute_hash("gen")

    # Child
    n2 = LegacyObj("child", h1)

    # verify_merkle_proof for legacy computes hash of node.
    # if node is object, compute_hash uses str(obj).

    assert verify_merkle_proof([n1, n2]) is True

    # Genesis trusted root match
    assert verify_merkle_proof([n1], trusted_root_hash=h1) is True

    # Genesis trusted root mismatch
    assert verify_merkle_proof([n1], trusted_root_hash="wrong") is False

    # Chain mismatch
    n2_bad = LegacyObj("child", "wrong")
    assert verify_merkle_proof([n1, n2_bad]) is False

    # Chain trusted root mismatch (if i > 0, it checks against prev node)
    # Case: Single node with prev_hash matching trusted root
    n_cont = LegacyObj("cont", h1)
    assert verify_merkle_proof([n_cont], trusted_root_hash=h1) is True

    # Case: Single node with prev_hash mismatching trusted root
    assert verify_merkle_proof([n_cont], trusted_root_hash="wrong") is False


# --- Loader Coverage ---
def test_loader_generic_exception(tmp_path: Path) -> None:
    # Test generic exception propagation
    # We mock ManifestIO.load to raise a generic Exception
    # Using tmp_path to avoid mocking Path resolution which was problematic

    f = tmp_path / "dummy.yaml"
    f.touch()

    with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io:
        instance = mock_io.return_value
        instance.load.side_effect = Exception("Generic Error")

        with pytest.raises(Exception, match="Generic Error"):
            load_flow_from_file(str(f))


def test_loader_with_custom_root(tmp_path: Path) -> None:
    # Test loading with explicit root_dir (Instruction 4)
    # Create structure: /tmp/jail/manifest.yaml
    jail = tmp_path / "jail"
    jail.mkdir()
    manifest = jail / "manifest.yaml"
    manifest.write_text(
        "kind: LinearFlow\nmetadata:\n  name: test\n  version: '1'\n  description: d\n  tags: []\nsequence: []"
    )

    # Pass explicit root
    flow = load_flow_from_file(str(manifest), root_dir=jail)
    assert flow.kind == "LinearFlow"


def test_loader_outside_root(tmp_path: Path) -> None:
    # Test loading a file that is outside the provided root_dir
    # This triggers the ValueError in relative_to and falls back to filename
    # ManifestIO then tries to load it from root_dir, which fails if not present there
    jail = tmp_path / "jail"
    jail.mkdir()

    outside = tmp_path / "outside.yaml"
    outside.touch()

    # The loader is confined to 'jail', but we ask it to load 'outside.yaml'
    # It will try to load 'jail/outside.yaml' and fail with FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_flow_from_file(str(outside), root_dir=jail)


# --- IO Coverage (Anti-TOCTOU) ---
def test_io_symlink_loop(tmp_path: Path) -> None:
    # Test ELOOP
    # Create dummy file to pass resolve check BEFORE patching
    (tmp_path / "dummy.yaml").touch()

    with patch("os.open") as mock_open:
        mock_open.side_effect = OSError(errno.ELOOP, "Loop")

        loader = ManifestIO(root_dir=tmp_path)

        with pytest.raises(SecurityViolationError, match="Symlink loop detected"):
            loader.load("dummy.yaml")


def test_io_generic_oserror(tmp_path: Path) -> None:
    # Test generic OSError (e.g. EACCES)
    (tmp_path / "dummy.yaml").touch()

    with patch("os.open") as mock_open:
        mock_open.side_effect = OSError(errno.EACCES, "Permission denied")

        loader = ManifestIO(root_dir=tmp_path)

        with pytest.raises(OSError, match="Permission denied"):
            loader.load("dummy.yaml")


def test_io_enoent(tmp_path: Path) -> None:
    # Test ENOENT during os.open (e.g., race condition)
    (tmp_path / "dummy.yaml").touch()

    with patch("os.open") as mock_open:
        mock_open.side_effect = OSError(errno.ENOENT, "Not found")

        loader = ManifestIO(root_dir=tmp_path)

        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            loader.load("dummy.yaml")


def test_io_exception_after_open(tmp_path: Path) -> None:
    # Test exception after open ensures close is called
    (tmp_path / "dummy.yaml").touch()

    # We need to simulate os.open returning a valid fd, then os.fstat raising
    with (
        patch("os.open", return_value=123),
        patch("os.close") as mock_close,
        patch("os.fstat", side_effect=RuntimeError("Boom")),
        patch("os.name", "posix"),
    ):
        loader = ManifestIO(root_dir=tmp_path)

        with pytest.raises(RuntimeError, match="Boom"):
            loader.load("dummy.yaml")

        mock_close.assert_called_with(123)


def test_io_not_dict(tmp_path: Path) -> None:
    # Test loading a file that parses but is not a dict
    f = tmp_path / "not_dict.yaml"
    f.write_text("- item1\n- item2")

    loader = ManifestIO(root_dir=tmp_path)
    with pytest.raises(ValueError, match="Manifest content must be a dictionary"):
        loader.load("not_dict.yaml")


def test_io_invalid_yaml(tmp_path: Path) -> None:
    # Test loading a file with invalid YAML
    f = tmp_path / "invalid.yaml"
    f.write_text(": invalid")

    loader = ManifestIO(root_dir=tmp_path)
    with pytest.raises(ValueError, match="Failed to parse manifest file"):
        loader.load("invalid.yaml")


def test_io_path_traversal(tmp_path: Path) -> None:
    # Test path traversal (Lines 57-58)
    jail = tmp_path / "jail"
    jail.mkdir()

    loader = ManifestIO(root_dir=jail)

    with pytest.raises(SecurityViolationError, match="Path Traversal Detected"):
        loader.load("../outside.yaml")


# --- Diff Coverage ---
def test_diff_edge_changes() -> None:
    # Cover edge addition and removal
    meta = FlowMetadata(name="DiffTest", version="1.0", description="T", tags=[])

    node_a = AgentNode(
        id="a",
        metadata={},
        supervision=None,
        type="agent",
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )
    node_b = AgentNode(
        id="b",
        metadata={},
        supervision=None,
        type="agent",
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )

    nodes: dict[str, AnyNode] = {"a": node_a, "b": node_b}

    # Graph 1: No edges
    graph1 = Graph(nodes=nodes, edges=[])
    flow1 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs=DataSchema(json_schema={}), outputs=DataSchema(json_schema={})),
        blackboard=None,
        graph=graph1,
    )

    # Graph 2: Edge a->b
    graph2 = Graph(nodes=nodes, edges=[Edge(source="a", target="b")])
    flow2 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs=DataSchema(json_schema={}), outputs=DataSchema(json_schema={})),
        blackboard=None,
        graph=graph2,
    )

    # Compare 1 -> 2 (Edge Added)
    changes_add = ManifestDiff.compare(flow1, flow2)
    assert any(c.field == "edges" and "added" in c.description for c in changes_add)

    # Compare 2 -> 1 (Edge Removed)
    changes_remove = ManifestDiff.compare(flow2, flow1)
    assert any(c.field == "edges" and "removed" in c.description for c in changes_remove)


def test_integrity_hash_mismatch_failure() -> None:
    # Strict mode hash mismatch (Line 142)
    p1 = {"node_id": "1", "state": "s", "previous_hashes": [], "attributes": {}}
    # Tamper with hash
    n1 = {"execution_hash": "bad_hash", **p1}
    assert verify_merkle_proof([n1]) is False


def test_integrity_linkage_failure() -> None:
    # Strict mode linkage failure (Line 158)
    p1 = {"node_id": "1", "state": "s", "previous_hashes": [], "attributes": {}}
    h1 = compute_hash(p1)
    n1 = {"execution_hash": h1, **p1}

    p2 = {"node_id": "2", "state": "s", "previous_hashes": ["missing_parent"], "attributes": {}}
    h2 = compute_hash(p2)
    n2 = {"execution_hash": h2, **p2}

    # n2 refers to "missing_parent" which is not in verified_hashes (only h1 is)
    assert verify_merkle_proof([n1, n2]) is False


def test_integrity_legacy_genesis_mismatch() -> None:
    # Legacy genesis mismatch (Line 183)
    # prev_hash is None (genesis), but trusted_root mismatch
    n1 = {"data": "gen"}
    # Pass wrong root
    assert verify_merkle_proof([n1], trusted_root_hash="wrong") is False


def test_integrity_legacy_chain_mismatch() -> None:
    # Legacy chain mismatch (Line 196)
    n1 = {"data": "gen"}
    # Compute hash is implicit in verification

    n2 = {"data": "child", "prev_hash": "wrong"}

    assert verify_merkle_proof([n1, n2]) is False


def test_integrity_legacy_trusted_root_mismatch_at_genesis_continuation() -> None:
    # Line 200: elif trusted_root_hash: if prev_hash != trusted ...
    # This happens when we have a chain start (i=0) that has a prev_hash (continuation),
    # but that prev_hash doesn't match the trusted root we provided.

    n1 = {"data": "cont", "prev_hash": "some_hash"}

    # Mismatch
    assert verify_merkle_proof([n1], trusted_root_hash="other_hash") is False

    # Match (for coverage of success path falling through to add)
    assert verify_merkle_proof([n1], trusted_root_hash="some_hash") is True


def test_integrity_missing_prev_hash() -> None:
    # Element without prev_hash in middle of chain (Line 183)
    chain = [{"a": 1}, {"b": 2}]  # No prev_hash key
    assert verify_merkle_proof(chain) is False


def test_verify_merkle_legacy_genesis_continuation_loose() -> None:
    # Coverage for lines 209-212: Chain start with prev_hash but no trusted root
    n1 = {"data": "cont", "prev_hash": "some_hash"}
    assert verify_merkle_proof([n1], trusted_root_hash=None) is True


# --- Visualizer Coverage ---
def test_visualizer_invalid_type() -> None:
    # Test invalid type passed to to_mermaid
    assert to_mermaid("invalid") == ""  # type: ignore


def test_visualizer_full_coverage() -> None:
    # Create nodes of various types
    node1 = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        presentation=PresentationHints(label='Agent "One"', group="Agents"),
    )
    node2 = PlannerNode(
        id="planner_1",
        metadata={},
        supervision=None,
        type="planner",
        goal="g",
        optimizer=None,
        output_schema={},
        presentation=PresentationHints(group="Planners"),
    )
    node3 = SwitchNode(
        id="switch-1",
        metadata={},
        supervision=None,
        type="switch",
        variable="var",
        cases={"cond1": "agent-1"},
        default="planner_1",
    )
    node4 = HumanNode(
        id="human 1",
        metadata={},
        supervision=None,
        type="human",
        prompt="Confirm?",
        timeout_seconds=60,
        options=["yes", "no"],
    )

    # Edges
    edges = [
        Edge(source="switch-1", target="agent-1"),  # Case condition implied
        Edge(source="switch-1", target="planner_1"),  # Default implied
        Edge(source="agent-1", target="human 1", condition="done"),
        Edge(source="planner_1", target="switch-1"),  # Cycle
    ]

    graph = Graph(nodes={n.id: n for n in [node1, node2, node3, node4]}, edges=edges)

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="VizTest", version="1", description="", tags=[]),
        interface=FlowInterface(inputs=DataSchema(json_schema={}), outputs=DataSchema(json_schema={})),
        blackboard=None,
        graph=graph,
    )

    # 1. Mermaid Generation
    mm = to_mermaid(flow)
    assert "subgraph Agents" in mm
    assert "subgraph Planners" in mm
    assert 'agent_1["Agent &quot;One&quot;"]' in mm  # Check escaping
    assert "human_1[/" in mm
    assert "|cond1|" in mm  # inferred switch label
    assert "|default|" in mm  # inferred switch default

    # 2. React Flow Generation
    rf = to_react_flow(flow)
    assert len(rf["nodes"]) == 4
    assert len(rf["edges"]) == 4

    # Check layout logic happened (positions assigned)
    # We have a cycle, so layout needs to handle it
    n_map = {n["id"]: n for n in rf["nodes"]}
    assert n_map["agent-1"]["position"]["x"] >= 0
    assert n_map["planner_1"]["position"]["x"] >= 0


def test_visualizer_linear_flow() -> None:
    # Test LinearFlow visualization
    node1 = AgentNode(
        id="a",
        type="agent",
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        metadata={},
    )
    node2 = AgentNode(
        id="b",
        type="agent",
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        metadata={},
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="LinTest", version="1", description="", tags=[]),
        sequence=[node1, node2],
    )

    mm = to_mermaid(flow)
    assert "graph TD" in mm
    assert "a --> b" in mm

    rf = to_react_flow(flow)
    assert len(rf["nodes"]) == 2
    assert len(rf["edges"]) == 1


def test_visualizer_with_snapshot() -> None:
    # Test visualizer with execution snapshot
    node1 = AgentNode(
        id="a",
        type="agent",
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        metadata={},
    )

    flow = LinearFlow(
        kind="LinearFlow", metadata=FlowMetadata(name="LinTest", version="1", description="", tags=[]), sequence=[node1]
    )

    snapshot = ExecutionSnapshot(node_states={"a": NodeState.RUNNING}, active_path=[])

    mm = to_mermaid(flow, snapshot)
    assert ":::running" in mm

    rf = to_react_flow(flow, snapshot)
    assert rf["nodes"][0]["data"]["state"] == NodeState.RUNNING
