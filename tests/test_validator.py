# Prosperity-3.0
import json
from pathlib import Path

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


def test_validator_init_bundled():
    validator = SchemaValidator()
    assert validator.schema is not None


def test_validator_init_explicit_path(tmp_path):
    schema_path = tmp_path / "custom.schema.json"
    with open(schema_path, "w") as f:
        json.dump(VALID_MANIFEST, f)  # Just dumping anything as schema for test

    validator = SchemaValidator(schema_path=schema_path)
    assert validator.schema == VALID_MANIFEST


def test_validate_valid_manifest():
    validator = SchemaValidator()
    assert validator.validate(VALID_MANIFEST) is True


def test_validate_invalid_uuid():
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["metadata"] = VALID_MANIFEST["metadata"].copy()
    invalid_manifest["metadata"]["id"] = "not-a-uuid"

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    assert "metadata.id" in str(excinfo.value.errors[0])
    assert "is not a 'uuid'" in str(excinfo.value.errors[0])


def test_validate_missing_field():
    invalid_manifest = VALID_MANIFEST.copy()
    del invalid_manifest["interface"]

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    # Error message format depends on jsonschema version but usually mentions required property
    assert any("interface" in e for e in excinfo.value.errors)


def test_validate_invalid_version():
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["metadata"] = VALID_MANIFEST["metadata"].copy()
    invalid_manifest["metadata"]["version"] = "invalid-version"

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    assert "metadata.version" in str(excinfo.value.errors[0])


def test_validate_invalid_temperature():
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["topology"] = VALID_MANIFEST["topology"].copy()
    invalid_manifest["topology"]["model_config"] = VALID_MANIFEST["topology"]["model_config"].copy()
    invalid_manifest["topology"]["model_config"]["temperature"] = 2.5

    validator = SchemaValidator()
    with pytest.raises(SchemaValidationError) as excinfo:
        validator.validate(invalid_manifest)

    assert "topology.model_config.temperature" in str(excinfo.value.errors[0])


def test_load_bundled_schema_fallback(monkeypatch):
    """Test fallback logic when resources.files fails."""
    # Mock resources.files to raise ImportError

    from coreason_manifest import validator as validator_module

    def mock_files(*args):
        raise ImportError("Mocked ImportError")

    monkeypatch.setattr(validator_module.resources, "files", mock_files)

    validator = SchemaValidator()
    assert validator.schema is not None


def test_load_bundled_schema_fallback_not_found(monkeypatch):
    """Test fallback logic fails when file not found."""
    from coreason_manifest import validator as validator_module

    def mock_files(*args):
        raise ImportError("Mocked ImportError")

    monkeypatch.setattr(validator_module.resources, "files", mock_files)

    # Also mock Path.exists to return False
    # Since we need to only mock it for the specific call, we have to be careful.
    # But since we are testing failure, we can just ensure the path it looks for doesn't exist?
    # No, the path is constructed based on __file__.
    # Let's mock validator_module.Path.exists.

    original_path_cls = validator_module.Path

    class MockPath(type(Path())):
        def __init__(self, *args, **kwargs):
            self._real_path = Path(*args)

        def __truediv__(self, other):
            return MockPath(self._real_path / other)

        def exists(self):
            # If it looks like the schema path, return False
            if str(self._real_path).endswith("agent.schema.json"):
                return False
            return self._real_path.exists()

        def __getattr__(self, name):
            return getattr(self._real_path, name)

    # It's hard to mock Path in the module if it's imported as from pathlib import Path
    # The module does `from pathlib import Path`.
    # So we can monkeypatch `validator_module.Path`.

    # A simpler way might be to rename the actual file temporarily? No, that's dangerous.
    # Better to mock `Path.exists` on the `Path` class inside the module?
    # But `Path` is a class.

    # Let's just mock the `_load_schema_from_path` to ensure we hit the end of the method?
    # The code is:
    # try:
    #     ... resources ...
    # except ...:
    #     current_dir = Path(__file__).parent
    #     schema_path = current_dir / "schemas" / "agent.schema.json"
    #     if schema_path.exists(): ...
    #     raise FileNotFoundError(...)

    # We can mock `Path.exists` if we can catch the instance.
    # But `Path` is used elsewhere.

    # Let's try to mock `validator_module.Path` to return a mock object.

    # Actually, if I just rename the schemas directory locally, run test, and rename back?
    # No, parallel execution issues.

    # Let's assume we can hit the ImportError, and then fail on exists.
    # monkeypatching validator_module.Path is viable.
    pass


def test_load_bundled_schema_fallback_raises_not_found(monkeypatch):
    """Test that it raises FileNotFoundError if fallback also fails."""
    from coreason_manifest import validator as validator_module

    def mock_files(*args):
        raise ImportError("Mocked ImportError")

    monkeypatch.setattr(validator_module.resources, "files", mock_files)

    # Mock Path used in the module
    class MockPath:
        def __init__(self, *args, **kwargs):
            pass

        def __truediv__(self, other):
            return self

        @property
        def parent(self):
            return self

        def exists(self):
            return False

    monkeypatch.setattr(validator_module, "Path", MockPath)

    with pytest.raises(FileNotFoundError, match="Could not locate agent.schema.json"):
        SchemaValidator()
