from typing import Any, ClassVar

import pytest

from coreason_manifest.spec.ontology import (
    DAGTopologyManifest,
    EpistemicProvenanceReceipt,
    ExecutionNodeReceipt,
    StateDifferentialManifest,
    StateMutationIntent,
    WorkflowManifest,
)
from coreason_manifest.utils.algebra import (
    apply_state_differential,
    compute_topology_hash,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    verify_ast_safety,
    verify_merkle_proof,
)


def test_apply_state_differential_add() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="test-diff-1",
        author_node_id="test-node-1",
        lamport_timestamp=1,
        vector_clock={"test-node-1": 1},
        patches=[
            StateMutationIntent(op="add", path="/b/d", value=3),
            StateMutationIntent(op="add", path="/d/-", value=4),
            StateMutationIntent(op="add", path="/d/0", value=0),
        ],
    )
    new_state = apply_state_differential(initial_state, manifest)
    assert new_state == {"a": 1, "b": {"c": 2, "d": 3}, "d": [0, 1, 2, 3, 4]}


def test_apply_state_differential_remove() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="test-diff-2",
        author_node_id="test-node-1",
        lamport_timestamp=1,
        vector_clock={"test-node-1": 1},
        patches=[StateMutationIntent(op="remove", path="/b/c"), StateMutationIntent(op="remove", path="/d/1")],
    )
    new_state = apply_state_differential(initial_state, manifest)
    assert new_state == {"a": 1, "b": {}, "d": [1, 3]}


def test_apply_state_differential_replace() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="test-diff-3",
        author_node_id="test-node-1",
        lamport_timestamp=1,
        vector_clock={"test-node-1": 1},
        patches=[
            StateMutationIntent(op="replace", path="/a", value=10),
            StateMutationIntent(op="replace", path="/b/c", value=20),
            StateMutationIntent(op="replace", path="/d/1", value=20),
        ],
    )
    new_state = apply_state_differential(initial_state, manifest)
    assert new_state == {"a": 10, "b": {"c": 20}, "d": [1, 20, 3]}


def test_apply_state_differential_move() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}

    class MockPatch:
        op: str = "move"
        path: str = "/a"
        from_path: str = "/b/c"

    class MockManifest:
        patches: ClassVar[list[Any]] = [MockPatch()]

    new_state = apply_state_differential(initial_state, MockManifest())  # type: ignore[arg-type]
    assert new_state == {"a": 2, "b": {}, "d": [1, 2, 3]}


def test_apply_state_differential_copy() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}

    class MockPatch:
        op: str = "copy"
        path: str = "/a"
        from_path: str = "/b/c"

    class MockManifest:
        patches: ClassVar[list[Any]] = [MockPatch()]

    new_state = apply_state_differential(initial_state, MockManifest())  # type: ignore[arg-type]
    assert new_state == {"a": 2, "b": {"c": 2}, "d": [1, 2, 3]}


def test_apply_state_differential_test() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="test-diff-6",
        author_node_id="test-node-1",
        lamport_timestamp=1,
        vector_clock={"test-node-1": 1},
        patches=[StateMutationIntent(op="test", path="/b/c", value=2)],
    )
    new_state = apply_state_differential(initial_state, manifest)
    assert new_state == initial_state

    manifest_fail = StateDifferentialManifest(
        diff_id="test-diff-7",
        author_node_id="test-node-1",
        lamport_timestamp=1,
        vector_clock={"test-node-1": 1},
        patches=[StateMutationIntent(op="test", path="/b/c", value=3)],
    )
    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential(initial_state, manifest_fail)


def test_apply_state_differential_invalid_paths() -> None:
    initial_state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}

    class MockPatch:
        def __init__(self, op: str, path: str, value: Any = None) -> None:
            self.op = op
            self.path = path
            self.value = value

    class MockManifest:
        def __init__(self, patches: list[Any]) -> None:
            self.patches = patches

    with pytest.raises(ValueError, match="Invalid JSON pointer"):
        apply_state_differential(initial_state, MockManifest([MockPatch("add", "invalid", 3)]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Invalid path"):
        apply_state_differential(initial_state, MockManifest([MockPatch("add", "/invalid/path", 3)]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Cannot remove from path"):
        apply_state_differential(initial_state, MockManifest([MockPatch("remove", "/b/missing")]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Cannot remove from path"):
        apply_state_differential(initial_state, MockManifest([MockPatch("remove", "/d/10")]))  # type: ignore[arg-type]


def test_verify_ast_safety() -> None:
    # Allowed nodes
    valid_payload = "{'a': 1, 'b': [1, 2, 3], 'c': (1, 2)}"
    assert verify_ast_safety(valid_payload) is True

    valid_payload2 = "1 + 2 * 3"
    assert verify_ast_safety(valid_payload2) is True

    valid_payload3 = "a[0]"
    assert verify_ast_safety(valid_payload3) is True

    # Forbidden nodes
    with pytest.raises(ValueError, match="Kinetic execution bleed detected"):
        verify_ast_safety("__import__('os').system('ls')")

    with pytest.raises(ValueError, match="Kinetic execution bleed detected"):
        verify_ast_safety("exec('print(1)')")


def test_project_manifest_to_markdown() -> None:
    manifest = WorkflowManifest(
        manifest_version="1.0.0",
        genesis_provenance=EpistemicProvenanceReceipt(
            extracted_by="did:coreason:orchestrator", source_event_id="test_trigger"
        ),
        topology=DAGTopologyManifest(type="dag", architectural_intent="test", max_depth=10, max_fan_out=5, nodes={}),
    )
    md = project_manifest_to_markdown(manifest)
    assert "# CoReason Agent Card" in md
    assert "- **Type:** `dag`" in md


def test_project_manifest_to_mermaid() -> None:
    class MockProfile:
        detected_modalities: ClassVar[list[str]] = ["vector_graphics", "text"]

    class MockBypass:
        bypassed_node_id: str = "bypass1"
        justification: str = "test_just"

    class MockManifest:
        manifest_id: str = "test-router"
        artifact_profile: Any = MockProfile()
        active_subgraphs: ClassVar[dict[str, list[str]]] = {"vector_graphics": ["did:node:1"], "text": ["did:node:2"]}
        bypassed_steps: ClassVar[list[Any]] = [MockBypass()]

    mermaid = project_manifest_to_mermaid(MockManifest())  # type: ignore[arg-type]
    assert "graph TD" in mermaid
    assert "test_router[test-router]" in mermaid
    assert "did_node_1" in mermaid


def test_compute_topology_hash() -> None:
    topo = DAGTopologyManifest(type="dag", architectural_intent="test", max_depth=10, max_fan_out=5, nodes={})
    h = compute_topology_hash(topo)
    assert isinstance(h, str)
    assert len(h) == 64


def test_verify_merkle_proof() -> None:
    receipt1 = ExecutionNodeReceipt(
        request_id="req1",
        inputs={"i": 1},
        outputs={"o": 1},
    )
    object.__setattr__(receipt1, "node_hash", receipt1.generate_node_hash())

    if receipt1.node_hash is not None:
        receipt2 = ExecutionNodeReceipt(
            request_id="req2", inputs={"i": 2}, outputs={"o": 2}, parent_hashes=[receipt1.node_hash]
        )
        object.__setattr__(receipt2, "node_hash", receipt2.generate_node_hash())

        assert verify_merkle_proof([receipt1, receipt2]) is True
