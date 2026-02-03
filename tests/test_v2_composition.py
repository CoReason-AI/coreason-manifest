# tests/test_v2_composition.py


from pathlib import Path
from typing import Any, Dict, cast

import pytest
import yaml

from coreason_manifest.v2.io import dump_to_yaml, load_from_yaml
from coreason_manifest.v2.spec.definitions import ManifestV2, ToolDefinition


@pytest.fixture
def manifest_dir(tmp_path: Path) -> Path:
    d = tmp_path / "manifests"
    d.mkdir()
    return d


def test_simple_import(manifest_dir: Path) -> None:
    """Test loading a manifest that references an external tool definition."""

    # Create tool definition file
    tool_def = {
        "id": "weather-tool",
        "name": "Weather Tool",
        "uri": "mcp://weather.com",
        "risk_level": "safe",
        "description": "Get weather info",
    }
    tool_path = manifest_dir / "tool.yaml"
    with open(tool_path, "w") as f:
        yaml.dump(tool_def, f)

    # Create main manifest
    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Weather Agent"},
        "definitions": {"my_tool": {"$ref": "tool.yaml"}},
        "workflow": {"start": "step1", "steps": {"step1": {"type": "agent", "id": "step1", "agent": "some-agent"}}},
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    # Load
    manifest = load_from_yaml(main_path)

    assert isinstance(manifest, ManifestV2)
    assert "my_tool" in manifest.definitions
    tool = manifest.definitions["my_tool"]

    # ManifestV2 definitions is Dict[str, Union[ToolDefinition, AgentDefinition, GenericDefinition]]
    # Pydantic might resolve it as a dict (Any) instead of ToolDefinition model.
    if isinstance(tool, ToolDefinition):
        assert tool.id == "weather-tool"
        assert tool.name == "Weather Tool"
    else:
        # Fallback to model_dump for generic comparison to satisfy mypy strictness
        tool_dict = tool.model_dump() if hasattr(tool, "model_dump") else tool
        assert isinstance(tool_dict, dict)
        assert tool_dict["id"] == "weather-tool"
        assert tool_dict["name"] == "Weather Tool"


def test_security_jailbreak(manifest_dir: Path) -> None:
    """Test that referencing a file outside the root directory raises an error."""

    # Create file outside root
    outside_dir = manifest_dir.parent / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "secret.yaml"
    with open(outside_file, "w") as f:
        yaml.dump({"secret": "data"}, f)

    # Create main manifest trying to access it
    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Hacker Agent"},
        "definitions": {"hack": {"$ref": "../outside/secret.yaml"}},
        "workflow": {"start": "step1", "steps": {"step1": {"type": "logic", "id": "step1", "code": "pass"}}},
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    # Load should fail
    with pytest.raises(ValueError, match="Security Error"):
        load_from_yaml(main_path)


def test_cycles(manifest_dir: Path) -> None:
    """Test detection of circular dependencies."""

    # a.yaml refs b.yaml
    a_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "A"},
        "definitions": {"b": {"$ref": "b.yaml"}},
        "workflow": {"start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}},
    }

    # b.yaml refs a.yaml
    b_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "B"},
        "definitions": {"a": {"$ref": "a.yaml"}},
        "workflow": {"start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}},
    }

    with open(manifest_dir / "a.yaml", "w") as f:
        yaml.dump(a_manifest, f)

    with open(manifest_dir / "b.yaml", "w") as f:
        yaml.dump(b_manifest, f)

    with pytest.raises(RecursionError, match="Circular dependency"):
        load_from_yaml(manifest_dir / "a.yaml")


def test_recursive_disabled(manifest_dir: Path) -> None:
    """Test that recursive=False does not resolve refs."""

    tool_def = {"id": "t", "name": "T", "uri": "u", "risk_level": "safe"}
    with open(manifest_dir / "tool.yaml", "w") as f:
        yaml.dump(tool_def, f)

    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Agent"},
        "definitions": {"my_tool": {"$ref": "tool.yaml"}},
        "workflow": {"start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}},
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    # Since we are not resolving, the dict value for my_tool will be {"$ref": "tool.yaml"}
    manifest = load_from_yaml(main_path, recursive=False)
    # It will be parsed as GenericDefinition because it has no known 'type'
    tool_def = manifest.definitions["my_tool"]

    # Force cast to Dict[str, Any] to avoid bidirectional type inference conflict
    # where mypy thinks it must be Dict[str, str] due to the assert below.
    raw_data = tool_def.model_dump() if hasattr(tool_def, "model_dump") else tool_def

    # Explicitly annotated variable
    tool_ref_data: Dict[str, Any]
    tool_ref_data = raw_data  # type: ignore[assignment]

    assert tool_ref_data == {"$ref": "tool.yaml"}


def test_invalid_yaml_content(manifest_dir: Path) -> None:
    """Test handling of invalid YAML content."""
    invalid_path = manifest_dir / "invalid.yaml"
    with open(invalid_path, "w") as f:
        f.write(":: invalid yaml ::")

    with pytest.raises(ValueError, match="Invalid YAML"):
        load_from_yaml(invalid_path)


def test_non_dict_content(manifest_dir: Path) -> None:
    """Test handling of valid YAML that is not a dictionary."""
    list_path = manifest_dir / "list.yaml"
    with open(list_path, "w") as f:
        yaml.dump(["item1", "item2"], f)

    with pytest.raises(ValueError, match="Expected a dictionary"):
        load_from_yaml(list_path)


def test_missing_file(manifest_dir: Path) -> None:
    """Test that referencing a non-existent file raises FileNotFoundError."""
    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Missing Agent"},
        "definitions": {"missing": {"$ref": "does_not_exist.yaml"}},
        "workflow": {"start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}},
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    with pytest.raises(FileNotFoundError, match="Referenced file not found"):
        load_from_yaml(main_path)


def test_load_missing_file(manifest_dir: Path) -> None:
    """Test that loading a non-existent file raises FileNotFoundError."""
    missing_path = manifest_dir / "non_existent.yaml"
    with pytest.raises(FileNotFoundError, match="Manifest file not found"):
        load_from_yaml(missing_path)


def test_dump_roundtrip(manifest_dir: Path) -> None:
    """Test that we can dump a manifest back to YAML."""
    manifest_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Dump Agent"},
        "workflow": {"start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}},
    }
    path = manifest_dir / "dump.yaml"
    with open(path, "w") as f:
        yaml.dump(manifest_data, f)

    manifest = load_from_yaml(path)
    dumped_yaml = dump_to_yaml(manifest)

    # Simple check that it's valid YAML and contains key fields
    data = yaml.safe_load(dumped_yaml)
    assert data["apiVersion"] == "coreason.ai/v2"
    assert data["kind"] == "Agent"
    assert data["metadata"]["name"] == "Dump Agent"
    # Ensure order (check if apiVersion is first in string)
    assert dumped_yaml.strip().startswith("apiVersion:")
