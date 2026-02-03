# tests/test_v2_composition.py

import pytest
import yaml
from pathlib import Path
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.spec.definitions import ManifestV2, ToolDefinition
from pydantic import ValidationError

@pytest.fixture
def manifest_dir(tmp_path):
    d = tmp_path / "manifests"
    d.mkdir()
    return d

def test_simple_import(manifest_dir):
    """Test loading a manifest that references an external tool definition."""

    # Create tool definition file
    tool_def = {
        "id": "weather-tool",
        "name": "Weather Tool",
        "uri": "mcp://weather.com",
        "risk_level": "safe",
        "description": "Get weather info"
    }
    tool_path = manifest_dir / "tool.yaml"
    with open(tool_path, "w") as f:
        yaml.dump(tool_def, f)

    # Create main manifest
    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {
            "name": "Weather Agent"
        },
        "definitions": {
            "my_tool": {"$ref": "tool.yaml"}
        },
        "workflow": {
            "start": "step1",
            "steps": {
                "step1": {
                    "type": "agent",
                    "id": "step1",
                    "agent": "some-agent"
                }
            }
        }
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    # Load
    manifest = load_from_yaml(main_path)

    assert isinstance(manifest, ManifestV2)
    assert "my_tool" in manifest.definitions
    tool = manifest.definitions["my_tool"]

    # ManifestV2 definitions is Dict[str, Union[ToolDefinition, Any]]
    # Pydantic might resolve it as a dict (Any) instead of ToolDefinition model.
    if isinstance(tool, ToolDefinition):
        assert tool.id == "weather-tool"
        assert tool.name == "Weather Tool"
    else:
        assert isinstance(tool, dict)
        assert tool["id"] == "weather-tool"
        assert tool["name"] == "Weather Tool"

def test_security_jailbreak(manifest_dir):
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
        "definitions": {
            "hack": {"$ref": "../outside/secret.yaml"}
        },
        "workflow": {
            "start": "step1",
            "steps": {"step1": {"type": "logic", "id": "step1", "code": "pass"}}
        }
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    # Load should fail
    with pytest.raises(ValueError, match="Security Error"):
        load_from_yaml(main_path)

def test_cycles(manifest_dir):
    """Test detection of circular dependencies."""

    # a.yaml refs b.yaml
    a_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "A"},
        "definitions": {
            "b": {"$ref": "b.yaml"}
        },
        "workflow": {
            "start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}
        }
    }

    # b.yaml refs a.yaml
    b_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "B"},
        "definitions": {
            "a": {"$ref": "a.yaml"}
        },
        "workflow": {
             "start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}
        }
    }

    with open(manifest_dir / "a.yaml", "w") as f:
        yaml.dump(a_manifest, f)

    with open(manifest_dir / "b.yaml", "w") as f:
        yaml.dump(b_manifest, f)

    with pytest.raises(RecursionError, match="Circular dependency"):
        load_from_yaml(manifest_dir / "a.yaml")

def test_recursive_disabled(manifest_dir):
    """Test that recursive=False does not resolve refs."""

    tool_def = {"id": "t", "name": "T", "uri": "u", "risk_level": "safe"}
    with open(manifest_dir / "tool.yaml", "w") as f:
        yaml.dump(tool_def, f)

    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Agent"},
        "definitions": {
            "my_tool": {"$ref": "tool.yaml"}
        },
        "workflow": {
             "start": "s", "steps": {"s": {"type": "logic", "id": "s", "code": "pass"}}
        }
    }
    main_path = manifest_dir / "main.yaml"
    with open(main_path, "w") as f:
        yaml.dump(main_manifest, f)

    # Since we are not resolving, the dict value for my_tool will be {"$ref": "tool.yaml"}
    manifest = load_from_yaml(main_path, recursive=False)
    assert manifest.definitions["my_tool"] == {"$ref": "tool.yaml"}
