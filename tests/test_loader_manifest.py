from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from coreason_manifest.spec.core.flow import LinearFlow
from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import (
    SecurityViolationError,
    UniqueKeyLoader,
    _resolve_refs,
    _scan_for_dynamic_references,
    load_flow_from_file,
    SandboxedPathFinder,
    _jail_root_var
)


def test_unique_key_loader():
    yaml_str = """
    key1: value1
    key1: value2
    """
    with pytest.raises(yaml.constructor.ConstructorError, match="found duplicate key"):
        yaml.load(yaml_str, Loader=UniqueKeyLoader)


def test_unique_key_loader_valid():
    yaml_str = """
    key1: value1
    key2: value2
    """
    data = yaml.load(yaml_str, Loader=UniqueKeyLoader)
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"


def test_scan_for_dynamic_references():
    data = {"key": "path/to/script.py:ClassName"}
    assert _scan_for_dynamic_references(data) is True

    data_list = ["path/to/script.py:ClassName"]
    assert _scan_for_dynamic_references(data_list) is True

    data_nested = {"key": {"inner": "path/to/script.py:ClassName"}}
    assert _scan_for_dynamic_references(data_nested) is True

    data_safe = {"key": "safe_string"}
    assert _scan_for_dynamic_references(data_safe) is False


def test_resolve_refs_circular(tmp_path):
    # Setup circular ref files
    file1 = tmp_path / "file1.yaml"
    file2 = tmp_path / "file2.yaml"

    file1.write_text('{"$ref": "file2.yaml"}')
    file2.write_text('{"$ref": "file1.yaml"}')

    loader = MagicMock()
    loader.read_text.side_effect = lambda x: (tmp_path / x).read_text()

    with pytest.raises(RecursionError, match="Circular dependency"):
        # We need to load initial data
        data = {"$ref": "file2.yaml"}
        _resolve_refs(data, tmp_path, loader)


def test_resolve_refs_escape(tmp_path):
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("{}")

    loader = MagicMock()

    data = {"$ref": "../outside.yaml"}

    with pytest.raises(SecurityJailViolationError, match="escapes the root directory"):
        _resolve_refs(data, jail, loader)


def test_load_flow_from_file_valid(tmp_path):
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

    flow = load_flow_from_file(str(flow_file))
    assert isinstance(flow, LinearFlow)


def test_load_flow_from_file_dynamic_check(tmp_path):
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
        load_flow_from_file(str(flow_file))


def test_sandboxed_path_finder_stdlib():
    finder = SandboxedPathFinder()
    assert finder.find_spec("os") is None


def test_sandboxed_path_finder_no_root():
    finder = SandboxedPathFinder()
    # Ensure no context var set
    token = _jail_root_var.set(None)
    try:
        assert finder.find_spec("mymodule") is None
    finally:
        _jail_root_var.reset(token)


def test_construct_mapping_not_mapping():
    # Helper to test construct_mapping_unique failure
    loader = UniqueKeyLoader("")
    # Pass a scalar node
    node = yaml.ScalarNode(tag="tag:yaml.org,2002:str", value="foo")
    with pytest.raises(yaml.constructor.ConstructorError, match="expected a mapping node"):
        # We access the static method added to loader class, but it's bound as constructor
        # We can call the function directly
        from coreason_manifest.utils.loader import construct_mapping_unique
        construct_mapping_unique(loader, node)


from coreason_manifest.utils.loader import sandbox_context

def test_loader_symlink_init_py(tmp_path):
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

def test_loader_symlink_module_py(tmp_path):
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
