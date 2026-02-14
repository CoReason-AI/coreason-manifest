from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.diff import ChangeType, ManifestDiff
from coreason_manifest.utils.integrity import (
    _recursive_sort_and_sanitize,
    compute_hash,
    reconstruct_payload,
    to_canonical_timestamp,
    verify_merkle_proof,
)
from coreason_manifest.utils.loader import load_flow_from_file
from coreason_manifest.utils.v2.io import ManifestIO


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
            return {"v1": True}

    sanitized = _recursive_sort_and_sanitize(MockV1())
    assert sanitized == {"v1": True}


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
    class NodeExec:
        def __init__(self, h: str, prev: list[str]) -> None:
            self.execution_hash = h
            self.previous_hashes = prev
            self.node_id = "n"
            self.state = "s"
            # reconstruct uses .get(), so object usually needs to be dict-like or Model?
            # integrity.py L78: d = node if isinstance(node, dict) else node.model_dump()
            # So if it's not dict, it assumes model_dump exists.

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
    n1 = {"execution_hash": h1, **p1}

    # Child
    p2 = {"node_id": "2", "previous_hashes": [h1], "attributes": {}}
    h2 = compute_hash(p2)
    n2 = {"execution_hash": h2, **p2}

    # Verify child only, with trusted root = h1
    # Trace starts at child? No, trace is full usually.
    # But verify_merkle_proof allows verifying a segment if trusted root connects?
    # If trace=[n2] (i=0).
    # previous_hashes=[h1].
    # trusted_root_hash=h1.
    # loop prev_hash in [h1]:
    # if prev_hash == trusted_root_hash: continue (Skips check against verified_hashes)

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
    h2 = compute_hash("child")

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
    # The elif trusted_root_hash branch in legacy is for when i=0 but prev_hash is present?
    # No, line 198: elif trusted_root_hash: if prev_hash != trusted: return False.
    # This is reached if i=0 (genesis check failed? no, genesis checks i=0 first).
    # Wait, line 193: if i > 0.
    # So line 198 is for i=0.

    # Case: Single node with prev_hash matching trusted root
    n_cont = LegacyObj("cont", h1)
    assert verify_merkle_proof([n_cont], trusted_root_hash=h1) is True

    # Case: Single node with prev_hash mismatching trusted root
    assert verify_merkle_proof([n_cont], trusted_root_hash="wrong") is False


# --- Loader Coverage ---
def test_loader_generic_exception(tmp_path) -> None:
    # Line 45: except Exception as e: raise e
    # We mock ManifestIO.load to raise a generic Exception
    # Using tmp_path to avoid mocking Path resolution which was problematic

    f = tmp_path / "dummy.yaml"
    f.touch()

    with patch("coreason_manifest.utils.loader.ManifestIO") as MockIO:
        instance = MockIO.return_value
        instance.load.side_effect = Exception("Generic Error")

        with pytest.raises(Exception, match="Generic Error"):
            load_flow_from_file(str(f))


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
        tools=[]
    )
    node_b = AgentNode(
        id="b",
        metadata={},
        supervision=None,
        type="agent",
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[]
    )

    nodes = {"a": node_a, "b": node_b}

    # Graph 1: No edges
    graph1 = Graph(nodes=nodes, edges=[])
    flow1 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(
            inputs=DataSchema(fields={}, required=[]),
            outputs=DataSchema(fields={}, required=[])
        ),
        blackboard=None,
        graph=graph1
    )

    # Graph 2: Edge a->b
    graph2 = Graph(nodes=nodes, edges=[Edge(source="a", target="b")])
    flow2 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(
            inputs=DataSchema(fields={}, required=[]),
            outputs=DataSchema(fields={}, required=[])
        ),
        blackboard=None,
        graph=graph2
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
    h1 = compute_hash(p1)
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
    h1 = compute_hash(n1)
    # Pass wrong root
    assert verify_merkle_proof([n1], trusted_root_hash="wrong") is False


def test_integrity_legacy_chain_mismatch() -> None:
    # Legacy chain mismatch (Line 196)
    n1 = {"data": "gen"}
    h1 = compute_hash(n1)

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
