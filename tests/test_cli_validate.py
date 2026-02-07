
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from coreason_manifest.cli import main

def test_validate_manifest_success(tmp_path, capsys):
    manifest_content = """
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Test Agent"
  x-design:
    x: 0
    y: 0
workflow:
  start: "step-1"
  steps:
    step-1:
      type: "logic"
      id: "step-1"
      code: "print('Hello')"
"""
    f = tmp_path / "valid_manifest.yaml"
    f.write_text(manifest_content)

    with patch("sys.argv", ["coreason", "validate", str(f)]):
        try:
            main()
        except SystemExit as e:
            # Should exit with 0 (implicit return) or not exit
            if e.code != 0:
                raise

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Test Agent (v?)" in captured.out

def test_validate_manifest_with_version(tmp_path, capsys):
    manifest_content = """
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Test Agent"
  version: "1.0.0"
  x-design:
    x: 0
    y: 0
workflow:
  start: "step-1"
  steps:
    step-1:
      type: "logic"
      id: "step-1"
      code: "print('Hello')"
"""
    f = tmp_path / "valid_manifest_v1.yaml"
    f.write_text(manifest_content)

    with patch("sys.argv", ["coreason", "validate", str(f)]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: Test Agent (v1.0.0)" in captured.out

def test_validate_agent_definition_success(tmp_path, capsys):
    agent_def = {
        "type": "agent",
        "id": "agent-1",
        "name": "My Agent",
        "role": "Assistant",
        "goal": "Help user",
        "backstory": "I am helpful",
        "model": "gpt-4",
        "tools": [],
        "knowledge": [],
        "interface": {},
        "capabilities": {}
    }
    f = tmp_path / "valid_agent.json"
    f.write_text(json.dumps(agent_def))

    with patch("sys.argv", ["coreason", "validate", str(f)]):
        main()

    captured = capsys.readouterr()
    assert "✅ Valid Agent: My Agent (v?)" in captured.out

def test_validate_failure(tmp_path, capsys):
    manifest_content = """
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Test Agent"
  x-design:
    x: 0
    y: 0
workflow:
  start: "step-1"
  steps:
    step-1:
      type: "unknown_type"
      id: "step-1"
"""
    f = tmp_path / "invalid_manifest.yaml"
    f.write_text(manifest_content)

    with patch("sys.argv", ["coreason", "validate", str(f)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Validation Failed:" in captured.out
    # Pydantic error message might vary slightly
    assert "Input tag 'unknown_type' found using 'type' does not match any of the expected tags" in captured.out

def test_file_not_found(capsys):
    with patch("sys.argv", ["coreason", "validate", "non_existent.yaml"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err

def test_invalid_extension(tmp_path, capsys):
    f = tmp_path / "test.txt"
    f.write_text("content")

    with patch("sys.argv", ["coreason", "validate", str(f)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "Error: Unsupported file extension: .txt" in captured.err

def test_missing_pyyaml(tmp_path, capsys):
    f = tmp_path / "test.yaml"
    f.touch()

    # Mock import failure
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("No module named 'yaml'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        # We also need to patch sys.modules to remove yaml if it's already there
        with patch.dict("sys.modules"):
            if "yaml" in sys.modules:
                del sys.modules["yaml"]

            with patch("sys.argv", ["coreason", "validate", str(f)]):
                with pytest.raises(SystemExit) as e:
                    main()
                assert e.value.code == 1

    captured = capsys.readouterr()
    assert "Error: PyYAML is required" in captured.err
