from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml

from coreason_manifest.spec.core.flow import LinearFlow
from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import (
    RuntimeSecurityWarning,
    SandboxedPathFinder,
    UniqueKeyLoader,
    _jail_root_var,
    _resolve_includes,
    _scan_for_dynamic_references,
    load_flow_from_file,
    sandbox_context,
)


def test_unique_key_loader() -> None:
    yaml_str = """
    key1: value1
    key1: value2
    """
    with pytest.raises(yaml.constructor.ConstructorError, match="found duplicate key"):
        yaml.load(yaml_str, Loader=UniqueKeyLoader)


def test_unique_key_loader_valid() -> None:
    yaml_str = """
    key1: value1
    key2: value2
    """
    data = yaml.load(yaml_str, Loader=UniqueKeyLoader)
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"


def test_scan_for_dynamic_references() -> None:
    data: dict[str, Any] = {"key": "path/to/script.py:ClassName"}
    assert _scan_for_dynamic_references(data) is True

    data_list: list[Any] = ["path/to/script.py:ClassName"]
    assert _scan_for_dynamic_references(data_list) is True

    data_nested: dict[str, Any] = {"key": {"inner": "path/to/script.py:ClassName"}}
    assert _scan_for_dynamic_references(data_nested) is True

    data_safe: dict[str, Any] = {"key": "safe_string"}
    assert _scan_for_dynamic_references(data_safe) is False


def test_resolve_refs_circular(tmp_path: Path) -> None:
    # Setup circular ref files
    file1 = tmp_path / "file1.yaml"
    file2 = tmp_path / "file2.yaml"

    file1.write_text('{"$include": "file2.yaml"}')
    file2.write_text('{"$include": "file1.yaml"}')

    loader = MagicMock()
    loader.read_text.side_effect = lambda x: (tmp_path / x).read_text()

    # Use match="Circular dependency" to verify exact error
    data = {"$include": "file2.yaml"}
    with pytest.raises(RecursionError, match="Circular dependency"):
        _resolve_includes(data, tmp_path, loader)


def test_resolve_refs_escape(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("{}")

    loader = MagicMock()

    data = {"$include": "../outside.yaml"}

    with pytest.raises(SecurityJailViolationError, match="escapes the root directory"):
        _resolve_includes(data, jail, loader)


def test_load_flow_from_file_valid(tmp_path: Path) -> None:
    flow_file = tmp_path / "flow.yaml"
    flow_content = """
    kind: LinearFlow
    metadata:
      name: Test
      version: 1.0.0
      description: Test
    sequence: []
    """
    flow_file.write_text(flow_content)

    flow = load_flow_from_file(str(flow_file), strict_security=False)
    assert isinstance(flow, LinearFlow)


def test_load_flow_from_file_dynamic_check(tmp_path: Path) -> None:
    flow_file = tmp_path / "flow.yaml"
    # Contains a dynamic ref-like string, though seemingly innocent, the regex matches file.py:Class
    flow_content = """
    kind: LinearFlow
    metadata:
      name: Test
      version: 1.0.0
      description: some/file.py:Class
    sequence: []
    """
    flow_file.write_text(flow_content)

    # By default allows it? No, default allow_dynamic_execution=False
    # But _scan checks for specific regex.
    # Regex: ^[a-zA-Z0-9_\-\./]+\.py:[a-zA-Z_]\w+$

    with pytest.raises(SecurityJailViolationError, match="Dynamic code execution references"):
        load_flow_from_file(str(flow_file), strict_security=False)


def test_sandboxed_path_finder_stdlib() -> None:
    finder = SandboxedPathFinder()
    assert finder.find_spec("os") is None


def test_sandboxed_path_finder_no_root() -> None:
    finder = SandboxedPathFinder()
    # Ensure no context var set
    token = _jail_root_var.set(None)
    try:
        assert finder.find_spec("mymodule") is None
    finally:
        _jail_root_var.reset(token)


def test_construct_mapping_not_mapping() -> None:
    # Helper to test construct_mapping_unique failure
    loader = UniqueKeyLoader("")
    # Pass a scalar node
    node = yaml.ScalarNode(tag="tag:yaml.org,2002:str", value="foo")

    # We access the static method added to loader class, but it's bound as constructor
    # We can call the function directly
    from coreason_manifest.utils.loader import construct_mapping_unique

    with pytest.raises(yaml.constructor.ConstructorError, match="expected a mapping node"):
        construct_mapping_unique(loader, node)


def test_loader_symlink_init_py(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("class Agent: pass")

    # pkg/__init__.py -> outside.py
    pkg = jail / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").symlink_to(outside)

    finder = SandboxedPathFinder()
    with sandbox_context(jail), pytest.raises(SecurityJailViolationError, match="outside jail"):
        finder.find_spec("pkg")


def test_loader_symlink_module_py(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("class Agent: pass")

    # mod.py -> outside.py
    # mod (dir) does not exist
    (jail / "mod.py").symlink_to(outside)

    finder = SandboxedPathFinder()
    with sandbox_context(jail), pytest.raises(SecurityJailViolationError, match="outside jail"):
        finder.find_spec("mod")


def test_loader_ref_passthrough(tmp_path: Path) -> None:
    # Test that $ref is passed through and not resolved as file
    import yaml

    from coreason_manifest.utils.loader import load_flow_from_file

    manifest = {
        "kind": "LinearFlow",
        "metadata": {"name": "Test", "version": "1.0.0", "description": "d", "tags": []},
        "sequence": [
            {"type": "agent", "id": "step1", "profile": "p", "tools": [], "metadata": {"ref": {"$ref": "#/foo"}}}
        ],
        "definitions": {},
    }

    (tmp_path / "main.yaml").write_text(yaml.dump(manifest))

    # Should not raise ValueError or FileNotFoundError (Anchor Crash check)
    flow = load_flow_from_file(str(tmp_path / "main.yaml"), strict_security=False)

    assert isinstance(flow, LinearFlow)
    assert flow.sequence[0].metadata["ref"] == {"$ref": "#/foo"}


def test_loader_include_sibling_warning(tmp_path: Path) -> None:
    # Test that a warning is issued when sibling keys are present with $include
    import yaml

    from coreason_manifest.utils.loader import load_flow_from_file

    manifest = {
        "kind": "LinearFlow",
        "metadata": {"name": "Test", "version": "1.0.0", "description": "d", "tags": []},
        "sequence": [{"$include": "step1.yaml", "ignored_key": "value"}],
        "definitions": {},
    }

    step1 = {"type": "agent", "id": "step1", "profile": "p", "tools": []}

    (tmp_path / "main.yaml").write_text(yaml.dump(manifest))
    (tmp_path / "step1.yaml").write_text(yaml.dump(step1))

    with pytest.warns(RuntimeSecurityWarning, match="Sibling keys alongside \\$include are ignored"):
        flow = load_flow_from_file(str(tmp_path / "main.yaml"), strict_security=False)

    # Verify the included content is loaded
    assert isinstance(flow, LinearFlow)
    assert flow.sequence[0].id == "step1"
