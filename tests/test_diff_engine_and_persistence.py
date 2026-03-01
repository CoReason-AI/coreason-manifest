import pytest

from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp, StateCheckpoint
from coreason_manifest.toolkit.diff_engine import apply_rewind, generate_inverse_patches


def test_json_patch_operation_add_replace_test() -> None:
    op = JSONPatchOperation.model_construct(op=PatchOp.ADD, path="/test", value=1, from_=None)
    assert op.op == PatchOp.ADD
    assert op.path == "/test"
    assert op.value == 1

    op = JSONPatchOperation.model_construct(op=PatchOp.REPLACE, path="/test", value=1, from_=None)
    assert op.op == PatchOp.REPLACE

    op = JSONPatchOperation.model_construct(op=PatchOp.TEST, path="/test", value=1, from_=None)
    assert op.op == PatchOp.TEST


def test_json_patch_operation_add_replace_test_requires_value() -> None:
    with pytest.raises(ValueError, match="requires a 'value' field"):
        JSONPatchOperation(op=PatchOp.ADD, path="/test")  # type: ignore[call-arg]


def test_json_patch_operation_move_copy() -> None:
    op = JSONPatchOperation.model_construct(op=PatchOp.MOVE, path="/test2", from_="/test", value=None)
    assert op.op == PatchOp.MOVE
    assert op.path == "/test2"
    assert op.from_ == "/test"

    op = JSONPatchOperation.model_construct(op=PatchOp.COPY, path="/test2", from_="/test", value=None)
    assert op.op == PatchOp.COPY


def test_json_patch_operation_move_copy_requires_from() -> None:
    with pytest.raises(ValueError, match="requires a 'from' path"):
        JSONPatchOperation(op=PatchOp.MOVE, path="/test2")  # type: ignore[call-arg]


def test_state_checkpoint() -> None:
    sc = StateCheckpoint(
        checkpoint_id="cp1", parent_id=None, forward_patches=[], reverse_patches=[], trigger_source="TEST"
    )
    assert sc.checkpoint_id == "cp1"


def test_generate_inverse_patches_and_apply_rewind() -> None:
    state = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}

    patches = [
        JSONPatchOperation.model_construct(op=PatchOp.ADD, path="/e", value=4, from_=None),
        JSONPatchOperation.model_construct(op=PatchOp.REPLACE, path="/a", value=10, from_=None),
        JSONPatchOperation.model_construct(op=PatchOp.REMOVE, path="/b/c", value=None, from_=None),
        JSONPatchOperation.model_construct(op=PatchOp.MOVE, path="/f", from_="/b", value=None),
        JSONPatchOperation.model_construct(op=PatchOp.COPY, path="/d/1", from_="/d/0", value=None),
        JSONPatchOperation.model_construct(op=PatchOp.TEST, path="/d/2", value=2, from_=None),
    ]

    inverse_patches = generate_inverse_patches(state, patches)

    # manually apply forward patches
    current_state = {"a": 10, "d": [1, 1, 2, 3], "e": 4, "f": {}}

    rewound_state = apply_rewind(current_state, inverse_patches)
    assert rewound_state == state
