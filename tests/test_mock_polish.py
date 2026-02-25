import uuid
from typing import Any

from coreason_manifest.utils.mock import MockFactory


def test_mock_string_formats() -> None:
    factory = MockFactory(seed=42)

    # UUID
    schema_uuid: dict[str, Any] = {"type": "string", "format": "uuid"}
    val_uuid = factory._generate_schema_data(schema_uuid)
    assert isinstance(val_uuid, str)
    # Validate it's a UUID
    assert uuid.UUID(val_uuid)

    # Date-time
    schema_dt: dict[str, Any] = {"type": "string", "format": "date-time"}
    val_dt = factory._generate_schema_data(schema_dt)
    assert isinstance(val_dt, str)
    assert "T" in val_dt # Simple ISO 8601 check

    # Email
    schema_email: dict[str, Any] = {"type": "string", "format": "email"}
    val_email = factory._generate_schema_data(schema_email)
    assert isinstance(val_email, str)
    assert "@example.com" in val_email

def test_mock_allof_merging() -> None:
    factory = MockFactory(seed=42)

    # Merge two objects
    schema: dict[str, Any] = {
        "allOf": [
            {"type": "object", "properties": {"a": {"type": "integer"}}},
            {"type": "object", "properties": {"b": {"type": "string"}}}
        ]
    }

    result = factory._generate_schema_data(schema)
    assert isinstance(result, dict)
    assert "a" in result
    assert "b" in result
    assert isinstance(result["a"], int)
    assert isinstance(result["b"], str)

def test_mock_allof_local_pollution_prevention() -> None:
    factory = MockFactory(seed=42)

    # allOf with NO local properties
    # Should NOT return {"mock_key": "mock_value"} from generic object fallback
    # The local schema {} should be detected as empty and skipped
    schema: dict[str, Any] = {
        "allOf": [
            {"type": "object", "properties": {"real": {"const": 1}}}
        ]
    }

    result = factory._generate_schema_data(schema)
    assert result == {"real": 1}
    assert "mock_key" not in result

def test_mock_allof_with_local_props() -> None:
    factory = MockFactory(seed=42)

    # allOf with local properties
    schema: dict[str, Any] = {
        "allOf": [
            {"type": "object", "properties": {"inherited": {"const": 1}}}
        ],
        "type": "object",
        "properties": {
            "local": {"const": 2}
        }
    }

    result = factory._generate_schema_data(schema)
    assert result == {"inherited": 1, "local": 2}
