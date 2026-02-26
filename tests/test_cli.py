
import sys
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock

import pytest
import yaml
from typer.testing import CliRunner
from coreason_manifest.cli import app

runner = CliRunner()

def create_valid_flow(path: str) -> None:
    data = {
        "kind": "LinearFlow",
        "metadata": {"name": "ValidFlow", "version": "1.0.0", "description": "Test", "tags": []},
        "sequence": [{"id": "step1", "type": "placeholder", "metadata": {}, "required_capabilities": []}],
    }
    with open(path, "w") as f:
        yaml.dump(data, f)


def create_invalid_flow(path: str) -> None:
    data = {
        "kind": "LinearFlow",
        "metadata": {"name": "InvalidFlow", "version": "1.0.0", "description": "Test", "tags": []},
        "sequence": [],  # Empty sequence is invalid
    }
    with open(path, "w") as f:
        yaml.dump(data, f)


def test_validate_success() -> None:
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_valid_flow(tmp_path)

    try:
        # Mocking ManifestIO because of strict security checks in loader
        with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io:
            from coreason_manifest.utils.io import ManifestIO
            def unsafe_manifest_io(*args, **kwargs):
                kwargs["strict_security"] = False
                return ManifestIO(*args, **kwargs)
            mock_io.side_effect = unsafe_manifest_io

            result = runner.invoke(app, ["validate", tmp_path])
            assert result.exit_code == 0
            assert "Flow is valid" in result.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_validate_failure() -> None:
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_invalid_flow(tmp_path)

    try:
        with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io:
            from coreason_manifest.utils.io import ManifestIO
            def unsafe_manifest_io(*args, **kwargs):
                kwargs["strict_security"] = False
                return ManifestIO(*args, **kwargs)
            mock_io.side_effect = unsafe_manifest_io

            result = runner.invoke(app, ["validate", tmp_path])
            assert result.exit_code == 1
            assert "Validation failed" in result.stderr
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_visualize_success() -> None:
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_valid_flow(tmp_path)

    try:
        with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io:
            from coreason_manifest.utils.io import ManifestIO
            def unsafe_manifest_io(*args, **kwargs):
                kwargs["strict_security"] = False
                return ManifestIO(*args, **kwargs)
            mock_io.side_effect = unsafe_manifest_io

            result = runner.invoke(app, ["visualize", tmp_path])
            assert result.exit_code == 0
            assert "graph TD" in result.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_visualize_with_errors() -> None:
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    create_invalid_flow(tmp_path)

    try:
        with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io:
            from coreason_manifest.utils.io import ManifestIO
            def unsafe_manifest_io(*args, **kwargs):
                kwargs["strict_security"] = False
                return ManifestIO(*args, **kwargs)
            mock_io.side_effect = unsafe_manifest_io

            result = runner.invoke(app, ["visualize", tmp_path])
            assert result.exit_code == 0
            assert "Flow has validation errors" in result.stderr
            assert "graph TD" in result.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_validate_missing_file() -> None:
    result = runner.invoke(app, ["validate", "non_existent.yaml"])
    assert result.exit_code == 1
    assert "Error loading file" in result.stderr


def test_visualize_missing_file() -> None:
    result = runner.invoke(app, ["visualize", "non_existent.yaml"])
    assert result.exit_code == 1
    assert "Error loading file" in result.stderr


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "CoReason Manifest CLI" in result.stdout


def test_validate_unexpected_error() -> None:
    with patch("coreason_manifest.cli.load_flow_from_file", side_effect=RuntimeError("Boom")):
        result = runner.invoke(app, ["validate", "test.yaml"])
        assert result.exit_code == 1
        assert "Unexpected Error: Boom" in result.stderr


def test_visualize_unexpected_error() -> None:
    with patch("coreason_manifest.cli.load_flow_from_file", side_effect=RuntimeError("Boom")):
        result = runner.invoke(app, ["visualize", "test.yaml"])
        assert result.exit_code == 1
        assert "Unexpected Error: Boom" in result.stderr


def test_version() -> None:
    with patch("coreason_manifest.cli.version", return_value="0.25.0"):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "coreason 0.25.0" in result.stdout


def test_version_not_found() -> None:
    with patch("coreason_manifest.cli.version", side_effect=PackageNotFoundError):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "coreason unknown" in result.stdout
