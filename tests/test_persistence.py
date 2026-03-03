import pytest
from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp


def test_validate_restricted_paths_valid():
    op = JSONPatchOperation(op=PatchOp.ADD, path="/valid/path", value="test")
    assert op.path == "/valid/path"

def test_validate_restricted_paths_invalid_exact():
    with pytest.raises(ValueError, match="Security Violation: Access or mutation of restricted namespace '/system' is forbidden."):
        JSONPatchOperation(op=PatchOp.ADD, path="/system", value="test")

def test_validate_restricted_paths_invalid_subpath():
    with pytest.raises(ValueError, match="Security Violation: Access or mutation of restricted namespace '/auth' is forbidden."):
        JSONPatchOperation(op=PatchOp.ADD, path="/auth/token", value="test")

def test_validate_restricted_paths_from_valid():
    op = JSONPatchOperation(op=PatchOp.COPY, path="/valid/path", from_="/valid/source")
    assert op.path == "/valid/path"
    assert op.from_ == "/valid/source"

def test_validate_restricted_paths_from_invalid():
    with pytest.raises(ValueError, match="Security Violation: Access or mutation of restricted namespace '/_internal' is forbidden."):
        JSONPatchOperation(op=PatchOp.COPY, path="/valid/path", from_="/_internal/data")

def test_validate_restricted_paths_prefix_false_positive():
    # Should not raise ValueError because it's not exactly /system and not a subpath
    op = JSONPatchOperation(op=PatchOp.ADD, path="/systematic_review", value="test")
    assert op.path == "/systematic_review"
