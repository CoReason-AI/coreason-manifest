import pytest

from coreason_manifest.spec.ontology import (
    ExecutionNodeReceipt,
    StateDifferentialManifest,
    StateMutationIntent,
    TamperFaultEvent,
)
from coreason_manifest.utils.algebra import apply_state_differential, verify_ast_safety, verify_merkle_proof


def test_verify_ast_safety_extra() -> None:
    assert verify_ast_safety("1 + 1")
    assert verify_ast_safety("[1, 2, 3]")
    assert verify_ast_safety("{'a': 1, 'b': 2}")
    with pytest.raises(ValueError, match="Payload is not valid syntax"):
        verify_ast_safety("a = 1")
    with pytest.raises(ValueError, match="Payload is not valid syntax"):
        verify_ast_safety("def f(): pass")


def test_apply_state_differential_extra() -> None:
    base_state = {"a": [1, 2], "b": {"c": 3}}

    # test copy
    manifest1 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="copy", path="/a/2", value="/b/c")],
    )
    new_state1 = apply_state_differential(base_state, manifest1)
    assert new_state1 == {"a": [1, 2, 3], "b": {"c": 3}}

    # test move
    manifest2 = StateDifferentialManifest(
        diff_id="did:web:patch-2",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="move", path="/a/2", value="/b/c")],
    )
    new_state2 = apply_state_differential(base_state, manifest2)
    assert new_state2 == {"a": [1, 2, 3], "b": {}}

    # test test
    manifest3 = StateDifferentialManifest(
        diff_id="did:web:patch-3",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="test", path="/b/c", value=3)],
    )
    new_state3 = apply_state_differential(base_state, manifest3)
    assert new_state3 == base_state

    manifest4 = StateDifferentialManifest(
        diff_id="did:web:patch-4",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="test", path="/b/c", value=4)],
    )
    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential(base_state, manifest4)

    # missing path
    manifest5 = StateDifferentialManifest(
        diff_id="did:web:patch-5",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="test", path="/b/x", value=4)],
    )
    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential(base_state, manifest5)

    # from path missing
    manifest6 = StateDifferentialManifest(
        diff_id="did:web:patch-6",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="copy", path="/a/2", value="/b/x")],
    )
    with pytest.raises(ValueError, match="Invalid from_path operation"):
        apply_state_differential(base_state, manifest6)

    # invalid path array index
    manifest7 = StateDifferentialManifest(
        diff_id="did:web:patch-7",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="remove", path="/a/x", value=4)],
    )
    with pytest.raises(ValueError, match="Cannot remove from path"):
        apply_state_differential(base_state, manifest7)

    # append array
    manifest8 = StateDifferentialManifest(
        diff_id="did:web:patch-8",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="add", path="/a/-", value=5)],
    )
    assert apply_state_differential(base_state, manifest8)["a"] == [1, 2, 5]


def test_apply_state_differential_exceptions() -> None:
    base_state = {"a": [1, 2], "b": {"c": 3}}

    # Non / path
    manifest1 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="add", path="a/2", value=4)],
    )
    with pytest.raises(ValueError, match="Invalid JSON pointer"):
        apply_state_differential(base_state, manifest1)

    # invalid op at root
    manifest2 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="add", path="", value=4)],
    )
    with pytest.raises(ValueError, match="Invalid path or root operation not supported"):
        apply_state_differential(base_state, manifest2)

    # copy to non dict/list
    base_state_bad = {"a": 1}
    manifest3 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="copy", path="/a/2", value="/a")],
    )
    with pytest.raises(ValueError, match="Cannot copy/move to path"):
        apply_state_differential(base_state_bad, manifest3)

    # replace missing
    manifest4 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="replace", path="/a/x", value=4)],
    )
    with pytest.raises(ValueError, match="Cannot replace at path"):
        apply_state_differential(base_state, manifest4)

    manifest5 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="replace", path="/c", value=4)],
    )
    with pytest.raises(ValueError, match="Cannot replace at path"):
        apply_state_differential(base_state, manifest5)

    # extract bad list index
    manifest6 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="test", path="/a/99", value=4)],
    )
    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential(base_state, manifest6)

    manifest7 = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="remove", path="/a/99", value=4)],
    )
    with pytest.raises(ValueError, match="Cannot remove from path"):
        apply_state_differential(base_state, manifest7)

    # invalid op
    manifest8 = StateDifferentialManifest(
        diff_id="did:web:patch-8",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[StateMutationIntent(op="test", path="", value={"a": [1, 2], "b": {"c": 3}})],
    )
    assert apply_state_differential(base_state, manifest8) == base_state


def test_verify_merkle_proof() -> None:
    node1 = ExecutionNodeReceipt(request_id="req1", inputs="in", outputs="out", root_request_id="req1")
    node2 = ExecutionNodeReceipt(
        request_id="req2",
        parent_request_id="req1",
        root_request_id="req1",
        inputs="in2",
        outputs="out2",
        parent_hashes=[node1.node_hash],  # type: ignore
    )
    node3 = ExecutionNodeReceipt(
        request_id="req3",
        parent_request_id="req1",
        root_request_id="req1",
        inputs="in3",
        outputs="out3",
        parent_hashes=["bad_hash"],
    )
    node4 = ExecutionNodeReceipt(
        request_id="req4",
        parent_request_id="req1",
        root_request_id="req1",
        inputs="in4",
        outputs="out4",
        parent_hashes=[node1.node_hash],  # type: ignore
    )
    object.__setattr__(node4, "node_hash", "wrong")
    assert verify_merkle_proof([node1, node2])
    with pytest.raises(TamperFaultEvent, match="Missing parent hash"):
        verify_merkle_proof([node1, node3])
    with pytest.raises(TamperFaultEvent, match="Node hash mismatch"):
        verify_merkle_proof([node1, node4])
