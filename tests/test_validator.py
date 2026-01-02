# Prosperity-3.0
import json
from pathlib import Path
from typing import Any

import pytest

from coreason_manifest.errors import SchemaValidationError
from coreason_manifest.validator import SchemaValidator

VALID_MANIFEST = {
    "metadata": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "version": "1.0.0",
        "name": "Test Agent",
        "author": "Tester",
        "created_at": "2023-10-27T10:00:00Z",
    },
    "interface": {"inputs": {"type": "object"}, "outputs": {"type": "object"}},
    "topology": {
        "steps": [{"id": "step1", "description": "Start"}],
        "model_config": {"model": "gpt-4", "temperature": 0.7},
    },
    "dependencies": {"tools": [], "libraries": ["requests"]},
}


def test_validator_init_bundled() -> None:
    validator = SchemaValidator()
    assert validator.schema is not None


def test_validator_init_explicit_path(tmp_path: Path) -> None:
    schema_path = tmp_path / "custom.schema.json"
    with open(schema_path, "w") as f:
        json.dump(VALID_MANIFEST, f)  # Just dumping anything as schema for test

    validator = SchemaValidator(schema_path=schema_path)
    assert validator.schema == VALID_MANIFEST


def test_validate_valid_manifest() -> None:
    validator = SchemaValidator()
    assert validator.validate(VALID_MANIFEST) is True


def test_validate_invalid_uuid() -> None:
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["metadata"] = VALID_MANIFEST["metadata"].copy()  # type: ignore
    invalid_manifest["metadata"]["id"] = "not-a-uuid"  # type: ignore

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    assert "metadata.id" in str(excinfo.value.errors[0])
    assert "is not a 'uuid'" in str(excinfo.value.errors[0])


def test_validate_missing_field() -> None:
    invalid_manifest = VALID_MANIFEST.copy()
    del invalid_manifest["interface"]

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    # Error message format depends on jsonschema version but usually mentions required property
    assert any("interface" in e for e in excinfo.value.errors)


def test_validate_invalid_version() -> None:
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["metadata"] = VALID_MANIFEST["metadata"].copy()  # type: ignore
    invalid_manifest["metadata"]["version"] = "invalid-version"  # type: ignore

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    assert "metadata.version" in str(excinfo.value.errors[0])


def test_validate_invalid_temperature() -> None:
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["topology"] = VALID_MANIFEST["topology"].copy()  # type: ignore
    invalid_manifest["topology"]["model_config"] = VALID_MANIFEST["topology"]["model_config"].copy()  # type: ignore
    invalid_manifest["topology"]["model_config"]["temperature"] = 2.5  # type: ignore

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    assert "topology.model_config.temperature" in str(excinfo.value.errors[0])


def test_load_bundled_schema_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback logic when resources.files fails."""

    def mock_files(*args: Any) -> Any:
        raise ImportError("Mocked ImportError")

    monkeypatch.setattr("coreason_manifest.validator.resources.files", mock_files)

    validator = SchemaValidator()
    assert validator.schema is not None


def test_load_bundled_schema_fallback_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback logic fails when file not found."""

    def mock_files(*args: Any) -> Any:
        raise ImportError("Mocked ImportError")

    monkeypatch.setattr("coreason_manifest.validator.resources.files", mock_files)

    # We rely on the fact that the fallback path likely doesn't exist in the test env structure
    # if we force it? Or we need to mock Path.exists too.
    pass


def test_load_bundled_schema_fallback_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that it raises FileNotFoundError if fallback also fails."""

    def mock_files(*args: Any) -> Any:
        raise ImportError("Mocked ImportError")

    monkeypatch.setattr("coreason_manifest.validator.resources.files", mock_files)

    # Mock Path used in the module
    # We can patch Path in the module namespace
    class MockPath:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __truediv__(self, other: Any) -> "MockPath":
            return self

        @property
        def parent(self) -> "MockPath":
            return self

        def exists(self) -> bool:
            return False

    monkeypatch.setattr("coreason_manifest.validator.Path", MockPath)

    with pytest.raises(FileNotFoundError, match="Could not locate agent.schema.json"):
        SchemaValidator()
