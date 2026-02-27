# tests/test_middleware_integration_v2.py

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import load_middleware_from_ref
from coreason_manifest.utils.validator import validate_flow

# Mock content for middlewares
VALID_MIDDLEWARE_CODE = """
class MyMiddleware:
    async def intercept_request(self, context, request):
        pass
"""

INVALID_MIDDLEWARE_CODE = """
class MyInvalidMiddleware:
    pass
"""

SYNC_REQUEST_MIDDLEWARE_CODE = """
class MySyncMiddleware:
    def intercept_request(self, context, request):
        pass
"""

SYNC_STREAM_MIDDLEWARE_CODE = """
class MySyncStreamMiddleware:
    def intercept_stream(self, packet):
        pass
"""

NOT_A_CLASS_CODE = """
def MyMiddleware():
    pass
"""

MISSING_CLASS_CODE = """
class OtherClass:
    pass
"""

FAILING_MODULE_CODE = """
raise ValueError("Module load failed")
"""

DEPENDENCY_CODE = """
def helper():
    return True
"""

MIDDLEWARE_WITH_DEP_CODE = """
import dependency
class MyMiddleware:
    async def intercept_request(self, context, request):
        dependency.helper()
"""

FAIL_DEP_CODE = """
raise ValueError("Dependency failed")
"""

MIDDLEWARE_FAIL_DEP_CODE = """
import fail_dep
class MyMiddleware:
    async def intercept_request(self, context, request):
        pass
"""

IMPORT_BAD_LINK_CODE = """
import bad_link
class MyMiddleware:
    async def intercept_request(self, context, request):
        pass
"""

IMPORT_BAD_PKG_CODE = """
import bad_pkg
class MyMiddleware:
    async def intercept_request(self, context, request):
        pass
"""

IMPORT_LOOP_CODE = """
import loop_link
class MyMiddleware:
    async def intercept_request(self, context, request):
        pass
"""


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    # Create a workspace with some files
    (tmp_path / "middlewares").mkdir()

    # Standard middlewares in subdirectory
    files = {
        "valid.py": VALID_MIDDLEWARE_CODE,
        "invalid.py": INVALID_MIDDLEWARE_CODE,
        "sync_request.py": SYNC_REQUEST_MIDDLEWARE_CODE,
        "sync_stream.py": SYNC_STREAM_MIDDLEWARE_CODE,
        "not_class.py": NOT_A_CLASS_CODE,
        "missing_class.py": MISSING_CLASS_CODE,
        "failing.py": FAILING_MODULE_CODE,
        "with_dep.py": MIDDLEWARE_WITH_DEP_CODE,
        "with_fail_dep.py": MIDDLEWARE_FAIL_DEP_CODE,
        "import_bad_link.py": IMPORT_BAD_LINK_CODE,
        "import_bad_pkg.py": IMPORT_BAD_PKG_CODE,
        "import_loop.py": IMPORT_LOOP_CODE,
    }

    for name, content in files.items():
        p = tmp_path / "middlewares" / name
        p.write_text(content)
        p.chmod(0o600)

    # Dependencies in ROOT (jail root) so they are found by SandboxedPathFinder
    (tmp_path / "dependency.py").write_text(DEPENDENCY_CODE)
    (tmp_path / "fail_dep.py").write_text(FAIL_DEP_CODE)

    # Ensure files are not world-writable to pass security checks
    for p in tmp_path.glob("*.py"):
        p.chmod(0o600)

    # loop_link.py needed for symlink loop test - mock creates symlink logic but file needs to exist for importlib
    (tmp_path / "loop_link.py").touch()

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
definitions:
  middlewares: {}
governance:
  active_middlewares:
    - missing_mw
"""
    data = yaml.safe_load(manifest_yaml)
    flow = GraphFlow.model_validate(data)
    errors = validate_flow(flow)
    assert any(
        e.code == "ERR_CAP_MISSING_MIDDLEWARE" and e.details.get("middleware_id") == "missing_mw" for e in errors
    )


def test_validation_no_definitions() -> None:
    # Test case where 'definitions' is completely missing
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
# definitions block omitted
governance:
  active_middlewares:
    - missing_mw
"""
    data = yaml.safe_load(manifest_yaml)
    flow = GraphFlow.model_validate(data)
    errors = validate_flow(flow)
    assert any(
        e.code == "ERR_CAP_MISSING_MIDDLEWARE" and e.details.get("middleware_id") == "missing_mw" for e in errors
    )


def test_validation_no_middlewares() -> None:
    # Test case where 'definitions' exists but 'middlewares' is missing (default empty dict in model)
    # Actually, if we omit it in YAML, Pydantic defaults it to empty dict.
    # To hit `elif not definitions.middlewares:` we need definitions object but empty middlewares dict.
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
    # middlewares omitted
    tools: {}
governance:
  active_middlewares:
    - missing_mw
"""
    data = yaml.safe_load(manifest_yaml)
    flow = GraphFlow.model_validate(data)
    errors = validate_flow(flow)
    assert any(
        e.code == "ERR_CAP_MISSING_MIDDLEWARE" and e.details.get("middleware_id") == "missing_mw" for e in errors
    )


def test_validation_missing_key_with_existing_middlewares() -> None:
    # Test case where 'definitions.middlewares' exists and is not empty,
    # but 'active_middlewares' references a key that is missing.
    # This hits the `else` block in `_validate_middleware_references` for patch generation.
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
    existing_mw:
      ref: middlewares/valid.py:MyMiddleware
governance:
  active_middlewares:
    - missing_mw
"""
    data = yaml.safe_load(manifest_yaml)
    flow = GraphFlow.model_validate(data)
    errors = validate_flow(flow)

    error = next(
        (
            e
            for e in errors
            if e.code == "ERR_CAP_MISSING_MIDDLEWARE" and e.details.get("middleware_id") == "missing_mw"
        ),
        None,
    )
    assert error is not None

    # Verify remediation
    assert error.remediation is not None
    assert error.remediation.type == "update_field"
    # patch_data is typically list of dicts for JSON Patch
    assert isinstance(error.remediation.patch_data, list)
    assert error.remediation.patch_data[0]["path"] == "/definitions/middlewares/missing_mw"


def test_loader_valid_middleware(workspace: Path) -> None:
    # Use context manager to capture warnings
    with pytest.warns(RuntimeWarning) as record:
        cls = load_middleware_from_ref("middlewares/valid.py:MyMiddleware", workspace)

    assert len(record) > 0
    assert cls.__name__ == "MyMiddleware"
    assert hasattr(cls, "intercept_request")


def test_loader_duck_typing_failure(workspace: Path) -> None:
    with pytest.warns(RuntimeWarning):
        with pytest.raises(TypeError) as exc:
            load_middleware_from_ref("middlewares/invalid.py:MyInvalidMiddleware", workspace)
        assert "must implement at least one protocol method" in str(exc.value)


def test_loader_sync_request_method(workspace: Path) -> None:
    with pytest.warns(RuntimeWarning):
        with pytest.raises(TypeError, match="must be an asynchronous coroutine"):
            load_middleware_from_ref("middlewares/sync_request.py:MySyncMiddleware", workspace)


def test_loader_sync_stream_method(workspace: Path) -> None:
    with pytest.warns(RuntimeWarning):
        with pytest.raises(TypeError, match="must be an asynchronous coroutine"):
            load_middleware_from_ref("middlewares/sync_stream.py:MySyncStreamMiddleware", workspace)


def test_loader_security_violation(workspace: Path) -> None:
    # Create a file outside the workspace
    outside = workspace.parent / "outside.py"
    outside.write_text(VALID_MIDDLEWARE_CODE)
    outside.chmod(0o600)

    # Try to load it using ..
    # No warning here because validation happens before execution
    with pytest.raises(SecurityJailViolationError):
        load_middleware_from_ref(f"../{outside.name}:MyMiddleware", workspace)


def test_loader_file_not_found(workspace: Path) -> None:
    # Add match parameter to make pytest.raises more specific
    with pytest.raises(ValueError, match="Middleware file not found"):
        load_middleware_from_ref("middlewares/nonexistent.py:MyMiddleware", workspace)


def test_loader_not_a_class(workspace: Path) -> None:
    with pytest.warns(RuntimeWarning):
        with pytest.raises(TypeError, match="is not a class"):
            load_middleware_from_ref("middlewares/not_class.py:MyMiddleware", workspace)


def test_loader_class_not_found_in_module(workspace: Path) -> None:
    with pytest.warns(RuntimeWarning):
        with pytest.raises(ValueError, match="Middleware class 'MyMiddleware' not found"):
            load_middleware_from_ref("middlewares/missing_class.py:MyMiddleware", workspace)


def test_loader_execution_failure(workspace: Path) -> None:
    with pytest.warns(RuntimeWarning):
        with pytest.raises(ValueError, match="Failed to execute middleware code"):
            load_middleware_from_ref("middlewares/failing.py:MyMiddleware", workspace)


def test_loader_cleanup_coverage(workspace: Path) -> None:
    # Capture warnings to prevent failure from RuntimeSecurityWarning
    with pytest.warns(RuntimeWarning):
        cls = load_middleware_from_ref("middlewares/with_dep.py:MyMiddleware", workspace)
    assert cls.__name__ == "MyMiddleware"


def test_loader_cleanup_exception_coverage(workspace: Path) -> None:
    # Import fail dependency. Covers exception cleanup loop.
    # fail_dep.py is in root.
    # load_middleware_from_ref raises ValueError if execution fails, but
    # SandboxedPathFinder might raise SecurityJailViolationError if imports are wonky?
    # No, with_fail_dep.py just raises ValueError.

    # We expect `RuntimeWarning` from `_execute_jailed_module`.
    # We ALSO expect the `ValueError` from the execution failure.

    with pytest.warns(RuntimeWarning):
        with pytest.raises(ValueError, match="Failed to execute middleware code"):
            load_middleware_from_ref("middlewares/with_fail_dep.py:MyMiddleware", workspace)


def test_loader_symlink_file_escape(workspace: Path) -> None:
    if os.name == "nt":
        pytest.skip("Symlinks not reliable on Windows tests")

    outside = workspace.parent / "target.py"
    outside.write_text("x = 1")
    outside.chmod(0o600)

    # Symlink at ROOT so it's found by SandboxedPathFinder as 'bad_link'
    link = workspace / "bad_link.py"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks not supported")

    with pytest.warns(RuntimeWarning):
        with pytest.raises(SecurityJailViolationError, match="outside jail"):
            load_middleware_from_ref("middlewares/import_bad_link.py:MyMiddleware", workspace)


def test_loader_symlink_pkg_escape(workspace: Path) -> None:
    if os.name == "nt":
        pytest.skip("Symlinks not reliable on Windows tests")

    outside_dir = workspace.parent / "outside_pkg"
    outside_dir.mkdir()
    (outside_dir / "__init__.py").write_text("y = 1")

    # Package at ROOT
    pkg_dir = workspace / "bad_pkg"
    pkg_dir.mkdir()
    link = pkg_dir / "__init__.py"
    try:
        link.symlink_to(outside_dir / "__init__.py")
    except OSError:
        pytest.skip("Symlinks not supported")

    with pytest.warns(RuntimeWarning):
        with pytest.raises(SecurityJailViolationError, match="outside jail"):
            load_middleware_from_ref("middlewares/import_bad_pkg.py:MyMiddleware", workspace)


def test_loader_symlink_loop(workspace: Path) -> None:
    # We use mocking to ensure we hit the exact exception handler line in the loader
    # regardless of OS-specific symlink behavior.

    original_resolve = Path.resolve

    def mock_resolve(self: Path, strict: bool = False) -> Path:
        # If trying to resolve 'loop_link' inside our workspace, raise error
        if "loop_link" in self.name:
            raise RuntimeError("Symlink loop detected")
        return original_resolve(self, strict=strict)

    # We need to ensure find_spec returns something so resolve is called on it
    # Import machinery will try to find 'loop_link'

    # But SandboxedPathFinder logic calls resolve on potential path BEFORE calling standard finder?
    # No, it calls find_spec (standard finder) -> if None -> manual check.
    # If standard finder finds it (because it is a file), then it calls resolve on origin.

    # So 'loop_link.py' must exist (it does in fixture).

    # But we patch Path.resolve.
    # When SandboxedPathFinder calls origin_path.resolve(), it should hit our mock.

    with (
        patch("pathlib.Path.resolve", side_effect=mock_resolve, autospec=True),
        pytest.warns(RuntimeWarning),
        pytest.raises(SecurityJailViolationError, match="Symlink loop"),
    ):
        # We expect SecurityJailViolationError because SandboxedPathFinder catches RuntimeError
        # and raises SecurityJailViolationError, which load_middleware_from_ref now unwraps.
        load_middleware_from_ref("middlewares/import_loop.py:MyMiddleware", workspace)


def test_loader_invalid_reference_format(workspace: Path) -> None:
    with pytest.raises(ValueError, match="Invalid reference format"):
        load_middleware_from_ref("invalid_format", workspace)


def test_loader_invalid_file_extension(workspace: Path) -> None:
    with pytest.raises(ValueError, match=r"must end with '\.py'"):
        load_middleware_from_ref("middlewares/valid.txt:MyMiddleware", workspace)


def test_loader_invalid_class_identifier(workspace: Path) -> None:
    with pytest.raises(ValueError, match="not a valid Python identifier"):
        load_middleware_from_ref("middlewares/valid.py:My-Middleware", workspace)
