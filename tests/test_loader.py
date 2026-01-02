# Prosperity-3.0
from unittest.mock import patch
from uuid import uuid4
from typing import Any, Dict

import pytest
import yaml
from pathlib import Path

from coreason_manifest.errors import ManifestSyntaxError, PolicyViolationError
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import AgentDefinition


@pytest.fixture
def valid_agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-26T12:00:00Z",
        },
        "interface": {"inputs": {"arg1": "string"}, "outputs": {"result": "string"}},
        "topology": {
            "steps": [{"id": "step1", "description": "First step"}],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": ["requests==2.31.0"]},
    }


def test_load_from_dict_valid(valid_agent_data: Dict[str, Any]) -> None:
    """Test loading from a valid dictionary."""
    agent = ManifestLoader.load_from_dict(valid_agent_data)
    assert isinstance(agent, AgentDefinition)
    assert agent.metadata.name == "Test Agent"
    assert str(agent.metadata.id) == valid_agent_data["metadata"]["id"]


def test_load_from_dict_invalid_missing_field(valid_agent_data: Dict[str, Any]) -> None:
    """Test loading from a dictionary with missing required field."""
    del valid_agent_data["metadata"]["name"]
    with pytest.raises(ManifestSyntaxError) as excinfo:
        ManifestLoader.load_from_dict(valid_agent_data)
    assert "Manifest validation failed" in str(excinfo.value)


def test_load_from_dict_invalid_version(valid_agent_data: Dict[str, Any]) -> None:
    """Test loading from a dictionary with invalid SemVer."""
    valid_agent_data["metadata"]["version"] = "invalid-version"
    with pytest.raises(ManifestSyntaxError) as excinfo:
        ManifestLoader.load_from_dict(valid_agent_data)
    assert "Manifest validation failed" in str(excinfo.value)


def test_load_from_file_valid(tmp_path: Path, valid_agent_data: Dict[str, Any]) -> None:
    """Test loading from a valid YAML file."""
    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    agent = ManifestLoader.load_from_file(manifest_path)
    assert isinstance(agent, AgentDefinition)
    assert agent.metadata.name == "Test Agent"


def test_load_from_file_not_found() -> None:
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        ManifestLoader.load_from_file("non_existent_file.yaml")


def test_load_from_file_invalid_yaml(tmp_path: Path) -> None:
    """Test loading from a file with invalid YAML syntax."""
    manifest_path = tmp_path / "invalid.yaml"
    with open(manifest_path, "w") as f:
        # Use content that is definitely invalid YAML
        f.write("[ this is broken")

    with pytest.raises(ManifestSyntaxError) as excinfo:
        ManifestLoader.load_from_file(manifest_path)
    assert "Failed to parse YAML file" in str(excinfo.value)


def test_load_from_file_not_a_dict(tmp_path: Path) -> None:
    """Test loading from a file that is valid YAML but not a dictionary."""
    manifest_path = tmp_path / "list.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(["item1", "item2"], f)

    with pytest.raises(ManifestSyntaxError) as excinfo:
        ManifestLoader.load_from_file(manifest_path)
    assert "Invalid YAML content" in str(excinfo.value)


def test_policy_violation_error() -> None:
    """Test PolicyViolationError initialization."""
    err = PolicyViolationError("msg", ["violation1"])
    assert err.violations == ["violation1"]

    err2 = PolicyViolationError("msg")
    assert err2.violations == []


def test_load_from_file_os_error(tmp_path: Path) -> None:
    """Test handling of OSError during file read."""
    manifest_path = tmp_path / "agent.yaml"
    manifest_path.touch()

    # Mock open to raise PermissionError
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with pytest.raises(ManifestSyntaxError) as excinfo:
            ManifestLoader.load_from_file(manifest_path)
    assert "Error reading file" in str(excinfo.value)
