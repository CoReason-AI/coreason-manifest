import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from coreason_manifest.cli import main


def test_validate_json_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation of a valid AgentDefinition in JSON format."""
    agent_file = tmp_path / "valid_agent.json"
    agent_data = {
        "type": "agent",
        "id": "test-agent",
        "name": "Test Agent",
        "role": "Tester",
        "goal": "Test things",
    }
    agent_file.write_text(json.dumps(agent_data))

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file), "--json"]):
        main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["type"] == "agent"
    assert output["id"] == "test-agent"
    assert output["name"] == "Test Agent"


def test_validate_manifest_v2_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation of a valid ManifestV2 in YAML format."""
    agent_file = tmp_path / "valid_manifest_v2.yaml"
    agent_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Manifest Agent", "version": "1.0.0"},
        "workflow": {"start": "step1", "steps": {"step1": {"type": "logic", "id": "step1", "code": "print('hello')"}}},
    }
    agent_file.write_text(yaml.dump(agent_data))

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Manifest Agent (v1.0.0)" in captured.out


def test_validate_manifest_v2_no_version(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation of a valid ManifestV2 without version."""
    agent_file = tmp_path / "valid_manifest_v2_no_ver.yaml"
    agent_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Manifest Agent NoVer"},
        "workflow": {"start": "step1", "steps": {"step1": {"type": "logic", "id": "step1", "code": "print('hello')"}}},
    }
    agent_file.write_text(yaml.dump(agent_data))

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Manifest Agent NoVer (vUnknown)" in captured.out


def test_validate_yaml_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation of a valid AgentDefinition in YAML format."""
    agent_file = tmp_path / "valid_agent.yaml"
    agent_data = {
        "type": "agent",
        "id": "test-agent-yaml",
        "name": "Test Agent YAML",
        "role": "Tester",
        "goal": "Test YAML",
    }
    agent_file.write_text(yaml.dump(agent_data))

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Test Agent YAML (vUnknown)" in captured.out


def test_validate_yaml_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation failure for an invalid AgentDefinition."""
    agent_file = tmp_path / "invalid_agent.yaml"
    agent_data = {
        "type": "agent",
        "id": "test-agent",
        # Missing 'name', 'role', 'goal'
    }
    agent_file.write_text(yaml.dump(agent_data))

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Validation Failed:" in captured.out
    assert "name" in captured.out
    assert "Field required" in captured.out


def test_validate_file_not_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation on non-existent file."""
    agent_file = tmp_path / "non_existent.yaml"

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert f"❌ Error: File '{agent_file}' not found." in captured.out


def test_validate_malformed_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation on malformed JSON file."""
    agent_file = tmp_path / "malformed.json"
    agent_file.write_text("{ incomplete json")

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Malformed JSON file" in captured.out


def test_validate_malformed_yaml(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation on malformed YAML file."""
    agent_file = tmp_path / "malformed.yaml"
    # Invalid YAML syntax
    agent_file.write_text("key: : value")

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Malformed YAML file" in captured.out


def test_validate_unsupported_extension(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation on unsupported file extension."""
    agent_file = tmp_path / "agent.txt"
    agent_file.write_text("{}")

    with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Unsupported file extension" in captured.out


def test_validate_read_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation when file reading fails (generic exception)."""
    agent_file = tmp_path / "read_error.json"
    agent_file.write_text("{}")

    with (
        patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]),
        patch("pathlib.Path.read_text", side_effect=PermissionError("Boom")),
    ):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error reading file: Boom" in captured.out


def test_validate_missing_pyyaml(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test validation of YAML file when PyYAML is not installed."""
    agent_file = tmp_path / "agent.yaml"
    agent_file.touch()

    # Simulate missing yaml module
    with patch.dict(sys.modules, {"yaml": None}):
        with patch.object(sys, "argv", ["coreason", "validate", str(agent_file)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: PyYAML is not installed" in captured.out
