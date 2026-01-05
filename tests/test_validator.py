# Prosperity-3.0
import json
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from coreason_manifest.errors import ManifestSyntaxError
from coreason_manifest.validator import SchemaValidator


@pytest.fixture
def valid_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {
            "inputs": {"type": "object"},
            "outputs": {"type": "string"},
        },
        "topology": {
            "steps": [{"id": "step1", "description": "First step"}],
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": ["tool:search"], "libraries": ["pandas==2.0.1"]},
        "integrity_hash": "dummy_hash",
    }


def test_validator_init() -> None:
    """Test validator initialization and schema loading."""
    validator = SchemaValidator()
    assert isinstance(validator.schema, dict)
    assert validator.schema.get("title") == "CoReason Agent Manifest"


def test_validate_valid_data(valid_data: Dict[str, Any]) -> None:
    """Test validation with valid data."""
    validator = SchemaValidator()
    assert validator.validate(valid_data) is True


def test_validate_invalid_data_type(valid_data: Dict[str, Any]) -> None:
    """Test validation with invalid data type."""
    validator = SchemaValidator()
    valid_data["metadata"]["version"] = 123  # Should be string
    with pytest.raises(ManifestSyntaxError) as excinfo:
        validator.validate(valid_data)
    assert "Schema validation failed" in str(excinfo.value)


def test_validate_invalid_format(valid_data: Dict[str, Any]) -> None:
    """Test validation with invalid format (UUID)."""
    validator = SchemaValidator()
    valid_data["metadata"]["id"] = "not-a-uuid"
    with pytest.raises(ManifestSyntaxError) as excinfo:
        validator.validate(valid_data)
    assert "Schema validation failed" in str(excinfo.value)


def test_validate_missing_required(valid_data: Dict[str, Any]) -> None:
    """Test validation with missing required field."""
    validator = SchemaValidator()
    del valid_data["metadata"]
    with pytest.raises(ManifestSyntaxError) as excinfo:
        validator.validate(valid_data)
    assert "Schema validation failed" in str(excinfo.value)


def test_schema_load_error() -> None:
    """Test error handling when schema file fails to load."""
    with patch("coreason_manifest.validator.files") as mock_files:
        mock_path = MagicMock()
        mock_files.return_value.joinpath.return_value = mock_path
        mock_path.open.side_effect = IOError("File missing")

        with pytest.raises(ManifestSyntaxError) as excinfo:
            SchemaValidator()
        assert "Failed to load agent schema" in str(excinfo.value)


def test_schema_invalid_json() -> None:
    """Test error handling when schema file contains invalid JSON."""
    # We patch json.load because it's easier to simulate JSONDecodeError that way
    with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
        with pytest.raises(ManifestSyntaxError) as excinfo:
            SchemaValidator()
        assert "Failed to load agent schema" in str(excinfo.value)


def test_schema_not_a_dict() -> None:
    """Test error handling when schema is valid JSON but not a dict."""
    with patch("coreason_manifest.validator.files") as mock_files:
        mock_path = MagicMock()
        mock_files.return_value.joinpath.return_value = mock_path
        # When mocking open, we need to ensure the returned file object reads properly.
        # However, since we are mocking files(), we can just mock the json.load return value
        # by mocking the file content and letting real json.load parse it?
        # No, json.load takes a file-like object.
        # Let's mock json.load to return a list instead of a dict, it's easier.
        pass

    with patch("json.load", return_value=["not", "a", "dict"]):
        with pytest.raises(ManifestSyntaxError) as excinfo:
            SchemaValidator()
        assert "Schema file is not a valid JSON object" in str(excinfo.value)
