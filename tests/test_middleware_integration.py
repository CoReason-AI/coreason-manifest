# tests/test_middleware_integration.py

import pytest
import yaml
from pathlib import Path
from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.interop.exceptions import ManifestError, SecurityJailViolationError
from coreason_manifest.utils.loader import load_middleware_from_ref

# Mock content for middlewares
VALID_MIDDLEWARE_CODE = """
class MyMiddleware:
    def intercept_request(self, context, request):
        pass
"""

INVALID_MIDDLEWARE_CODE = """
class MyInvalidMiddleware:
    pass
"""

@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    # Create a workspace with some files
    (tmp_path / "middlewares").mkdir()
    valid_file = tmp_path / "middlewares" / "valid.py"
    valid_file.write_text(VALID_MIDDLEWARE_CODE)
    # Secure permissions: read/write for user only (600)
    valid_file.chmod(0o600)

    invalid_file = tmp_path / "middlewares" / "invalid.py"
    invalid_file.write_text(INVALID_MIDDLEWARE_CODE)
    invalid_file.chmod(0o600)

    return tmp_path

def test_valid_manifest_loading() -> None:
    manifest_yaml = """
kind: GraphFlow
metadata:
  name: test-flow
  version: 1.0.0
interface: {}
graph:
  nodes:
    start:
      type: placeholder
      id: start
  edges: []
  entry_point: start
definitions:
  middlewares:
    my_mw:
      ref: middlewares/valid.py:MyMiddleware
governance:
  active_middlewares:
    - my_mw
"""
    data = yaml.safe_load(manifest_yaml)
    flow = GraphFlow.model_validate(data)

    # Assertions with type narrowing for Mypy
    assert flow.definitions is not None
    assert "my_mw" in flow.definitions.middlewares
    assert flow.definitions.middlewares["my_mw"].ref == "middlewares/valid.py:MyMiddleware"

    assert flow.governance is not None
    assert "my_mw" in flow.governance.active_middlewares

def test_missing_definition_validation() -> None:
    manifest_yaml = """
kind: GraphFlow
metadata:
  name: test-flow
  version: 1.0.0
interface: {}
graph:
  nodes:
    start:
      type: placeholder
      id: start
  edges: []
  entry_point: start
governance:
  active_middlewares:
    - missing_mw
"""
    data = yaml.safe_load(manifest_yaml)
    with pytest.raises(ManifestError) as exc:
        GraphFlow.model_validate(data)
    assert "Active middleware 'missing_mw' is not defined" in str(exc.value)

def test_loader_valid_middleware(workspace: Path) -> None:
    cls = load_middleware_from_ref("middlewares/valid.py:MyMiddleware", workspace)
    assert cls.__name__ == "MyMiddleware"
    assert hasattr(cls, "intercept_request")

def test_loader_duck_typing_failure(workspace: Path) -> None:
    with pytest.raises(TypeError) as exc:
        load_middleware_from_ref("middlewares/invalid.py:MyInvalidMiddleware", workspace)
    assert "must implement 'intercept_request' or 'intercept_stream'" in str(exc.value)

def test_loader_security_violation(workspace: Path) -> None:
    # Create a file outside the workspace
    # Since tmp_path is a temp directory, workspace.parent is the base temp dir.
    # We create a file there.
    outside = workspace.parent / "outside.py"
    outside.write_text(VALID_MIDDLEWARE_CODE)
    outside.chmod(0o600)

    # Try to load it using ..
    with pytest.raises(SecurityJailViolationError):
        load_middleware_from_ref(f"../{outside.name}:MyMiddleware", workspace)

def test_loader_file_not_found(workspace: Path) -> None:
    # Add match parameter to make pytest.raises more specific
    with pytest.raises(ValueError, match="Middleware file not found"):
        load_middleware_from_ref("middlewares/nonexistent.py:MyMiddleware", workspace)
