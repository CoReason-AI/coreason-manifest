import sys
from unittest.mock import patch
from tempfile import NamedTemporaryFile
from pathlib import Path
import yaml
import pytest
from _pytest.capture import CaptureFixture

from coreason_manifest.cli import main

def create_valid_flow(path: str):
    data = {
        "kind": "LinearFlow",
        "metadata": {
            "name": "ValidFlow",
            "version": "1.0",
            "description": "Test",
            "tags": []
        },
        "sequence": [
            {"id": "step1", "type": "placeholder", "metadata": {}, "supervision": None, "required_capabilities": []}
        ],
        "tool_packs": []
    }
    with open(path, "w") as f:
        yaml.dump(data, f)

def create_invalid_flow(path: str):
    data = {
        "kind": "LinearFlow",
        "metadata": {
            "name": "InvalidFlow",
            "version": "1.0",
            "description": "Test",
            "tags": []
        },
        "sequence": [], # Empty sequence is invalid
        "tool_packs": []
    }
    with open(path, "w") as f:
        yaml.dump(data, f)

def test_validate_success(capsys: CaptureFixture[str]):
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_valid_flow(tmp_path)

    try:
        test_args = ["coreason", "validate", tmp_path]
        with patch.object(sys, "argv", test_args):
            ret = main()
            assert ret == 0
            captured = capsys.readouterr()
            assert "Flow is valid" in captured.out
    finally:
        Path(tmp_path).unlink()

def test_validate_failure(capsys: CaptureFixture[str]):
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_invalid_flow(tmp_path)

    try:
        test_args = ["coreason", "validate", tmp_path]
        with patch.object(sys, "argv", test_args):
            ret = main()
            assert ret == 1
            captured = capsys.readouterr()
            assert "Validation failed" in captured.err
    finally:
        Path(tmp_path).unlink()

def test_visualize_success(capsys: CaptureFixture[str]):
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_valid_flow(tmp_path)

    try:
        test_args = ["coreason", "visualize", tmp_path]
        with patch.object(sys, "argv", test_args):
            ret = main()
            assert ret == 0
            captured = capsys.readouterr()
            assert "graph TD" in captured.out
    finally:
        Path(tmp_path).unlink()

def test_visualize_with_errors(capsys: CaptureFixture[str]):
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_invalid_flow(tmp_path)

    try:
        test_args = ["coreason", "visualize", tmp_path]
        with patch.object(sys, "argv", test_args):
            ret = main()
            assert ret == 0 # Visualize proceeds even with errors
            captured = capsys.readouterr()
            assert "Flow has validation errors" in captured.err
            assert "graph TD" in captured.out
    finally:
        Path(tmp_path).unlink()

def test_validate_missing_file(capsys: CaptureFixture[str]) -> None:
    """Test that the validate command handles missing files."""
    test_args = ["coreason", "validate", "non_existent.yaml"]
    with patch.object(sys, "argv", test_args):
        ret = main()
        assert ret == 1
        captured = capsys.readouterr()
        assert "Manifest file not found" in captured.err

def test_visualize_missing_file(capsys: CaptureFixture[str]) -> None:
    """Test that the visualize command handles missing files."""
    test_args = ["coreason", "visualize", "non_existent.yaml"]
    with patch.object(sys, "argv", test_args):
        ret = main()
        assert ret == 1
        captured = capsys.readouterr()
        assert "Manifest file not found" in captured.err

def test_cli_help(capsys: CaptureFixture[str]) -> None:
    """Test that help is printed when no command is given."""
    test_args = ["coreason"]
    with patch.object(sys, "argv", test_args):
        try:
            ret = main()
            assert ret == 0
            captured = capsys.readouterr()
            assert "usage: coreason" in captured.out
        except SystemExit:
            pass
