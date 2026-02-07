# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from coreason_manifest.cli import main
from coreason_manifest.spec.v2.definitions import AgentDefinition

# Sample Valid AgentDefinition
VALID_AGENT = {
    "type": "agent",
    "id": "agent-1",
    "name": "Test Agent",
    "role": "Tester",
    "goal": "Test things",
    "tools": [],
    "knowledge": [],
    "interface": {},
    "capabilities": {},
}

# Invalid Agent (missing role, goal)
INVALID_AGENT = {
    "type": "agent",
    "id": "agent-1",
    "name": "Test Agent",
}


@pytest.fixture
def temp_agent_file(tmp_path):
    def _create(content, ext=".json"):
        p = tmp_path / f"agent{ext}"
        if ext == ".json":
            with open(p, "w") as f:
                json.dump(content, f)
        else:
            import yaml
            with open(p, "w") as f:
                yaml.dump(content, f)
        return str(p)
    return _create


def test_validate_valid_json(temp_agent_file, capsys):
    fpath = temp_agent_file(VALID_AGENT, ".json")

    with patch.object(sys, "argv", ["coreason", "validate", fpath]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Test Agent (vUnknown)" in captured.out


def test_validate_valid_yaml(temp_agent_file, capsys):
    fpath = temp_agent_file(VALID_AGENT, ".yaml")

    with patch.object(sys, "argv", ["coreason", "validate", fpath]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Test Agent (vUnknown)" in captured.out


def test_validate_invalid_yaml(temp_agent_file, capsys):
    fpath = temp_agent_file(INVALID_AGENT, ".yaml")

    with patch.object(sys, "argv", ["coreason", "validate", fpath]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Validation Failed:" in captured.out
    assert "role" in captured.out
    assert "goal" in captured.out


def test_validate_file_not_found(capsys):
    with patch.object(sys, "argv", ["coreason", "validate", "non_existent.json"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: File not found" in captured.err


def test_validate_invalid_json_syntax(tmp_path, capsys):
    p = tmp_path / "broken.json"
    p.write_text("{ broken }")

    with patch.object(sys, "argv", ["coreason", "validate", str(p)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Invalid JSON" in captured.err


def test_validate_pyyaml_missing(temp_agent_file, capsys):
    fpath = temp_agent_file(VALID_AGENT, ".yaml")

    # Mock ImportError for yaml
    with patch.dict(sys.modules, {"yaml": None}):
        with patch.object(sys, "argv", ["coreason", "validate", fpath]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

    captured = capsys.readouterr()
    assert "PyYAML is not installed" in captured.err


def test_validate_json_read_error(temp_agent_file, capsys):
    fpath = temp_agent_file(VALID_AGENT, ".json")

    with patch("builtins.open", side_effect=OSError("Read error")):
        with patch.object(sys, "argv", ["coreason", "validate", fpath]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error reading file: Read error" in captured.err


def test_validate_yaml_read_error(temp_agent_file, capsys):
    fpath = temp_agent_file(VALID_AGENT, ".yaml")

    # We need to ensure open is patched, but we also need to allow import yaml.
    # The builtins.open patch affects everything.
    # But temp_agent_file created the file before the patch.

    with patch("builtins.open", side_effect=OSError("Read error")):
        with patch.object(sys, "argv", ["coreason", "validate", fpath]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error reading file: Read error" in captured.err


def test_validate_generic_exception(temp_agent_file, capsys):
    fpath = temp_agent_file(VALID_AGENT, ".json")

    with patch.object(AgentDefinition, "model_validate", side_effect=Exception("Unexpected boom")):
        with patch.object(sys, "argv", ["coreason", "validate", fpath]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Unexpected boom" in captured.out


def test_validate_unsupported_extension(tmp_path, capsys):
    p = tmp_path / "agent.txt"
    p.touch()

    with patch.object(sys, "argv", ["coreason", "validate", str(p)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Unsupported file extension: .txt" in captured.err


def test_validate_invalid_yaml_syntax(tmp_path, capsys):
    p = tmp_path / "broken.yaml"
    p.write_text("broken: [")

    with patch.object(sys, "argv", ["coreason", "validate", str(p)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Error: Invalid YAML" in captured.err
