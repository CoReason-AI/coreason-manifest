import pytest
from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp, StateCheckpoint
from coreason_manifest.toolkit.diff_engine import generate_inverse_patches, apply_rewind

def test_json_patch_operation_add_replace_test():
    op = JSONPatchOperation(op=PatchOp.ADD, path="/test", value=1)
    assert op.op == PatchOp.ADD
    assert op.path == "/test"
    assert op.value == 1

    op = JSONPatchOperation(op=PatchOp.REPLACE, path="/test", value=1)
    assert op.op == PatchOp.REPLACE

    op = JSONPatchOperation(op=PatchOp.TEST, path="/test", value=1)
    assert op.op == PatchOp.TEST

def test_json_patch_operation_add_replace_test_requires_value():
    with pytest.raises(ValueError):
        JSONPatchOperation(op=PatchOp.ADD, path="/test")

def test_json_patch_operation_move_copy():
    op = JSONPatchOperation(op=PatchOp.MOVE, path="/test2", from_="/test")
    assert op.op == PatchOp.MOVE
    assert op.path == "/test2"
    assert op.from_ == "/test"

    op = JSONPatchOperation(op=PatchOp.COPY, path="/test2", from_="/test")
    assert op.op == PatchOp.COPY

def test_json_patch_operation_move_copy_requires_from():
    with pytest.raises(ValueError):
        JSONPatchOperation(op=PatchOp.MOVE, path="/test2")


def test_state_checkpoint():
    sc = StateCheckpoint(
        checkpoint_id="cp1",
        parent_id=None,
        forward_patches=[],
        reverse_patches=[],
        trigger_source="TEST"
    )
    assert sc.checkpoint_id == "cp1"

def test_generate_inverse_patches_and_apply_rewind():
    state = {
        "a": 1,
        "b": {"c": 2},
        "d": [1, 2, 3]
    }

    patches = [
        JSONPatchOperation(op=PatchOp.ADD, path="/e", value=4),
        JSONPatchOperation(op=PatchOp.REPLACE, path="/a", value=10),
        JSONPatchOperation(op=PatchOp.REMOVE, path="/b/c"),
        JSONPatchOperation(op=PatchOp.MOVE, path="/f", from_="/b"),
        JSONPatchOperation(op=PatchOp.COPY, path="/d/1", from_="/d/0"),
        JSONPatchOperation(op=PatchOp.TEST, path="/d/2", value=2)
    ]

    inverse_patches = generate_inverse_patches(state, patches)

    # manually apply forward patches
    current_state = {
        "a": 10,
        "d": [1, 1, 2, 3],
        "e": 4,
        "f": {}
    }

    rewound_state = apply_rewind(current_state, inverse_patches)
    assert rewound_state == state
