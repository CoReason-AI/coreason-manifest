# Prosperity-3.0
from typing import Any, Dict
from uuid import uuid4

import pytest
from coreason_manifest.errors import ManifestSyntaxError
from coreason_manifest.models import AgentDefinition
from coreason_manifest.validator import SchemaValidator
from pydantic import ValidationError


@pytest.fixture
def valid_agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1"}],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": []},
    }


def test_schema_validator_extra_field(valid_agent_data: Dict[str, Any]) -> None:
    """Test that SchemaValidator rejects extra fields."""
    valid_agent_data["extra_field"] = "value"
    validator = SchemaValidator()

    # Reload schema if necessary (it loads on init)
    # The overwrite of agent.schema.json should be picked up if we run tests after.
    # Note: If tests run in the same process where schema was already loaded, it might be cached?
    # SchemaValidator loads from file on init, so new instance should read new file.

    with pytest.raises(ManifestSyntaxError) as excinfo:
        validator.validate(valid_agent_data)
    assert "Schema validation failed" in str(excinfo.value)


def test_schema_validator_nested_extra_field(valid_agent_data: Dict[str, Any]) -> None:
    """Test that SchemaValidator rejects extra fields in nested objects."""
    valid_agent_data["metadata"]["extra_meta"] = "value"
    validator = SchemaValidator()

    with pytest.raises(ManifestSyntaxError) as excinfo:
        validator.validate(valid_agent_data)
    assert "Schema validation failed" in str(excinfo.value)


def test_pydantic_extra_field(valid_agent_data: Dict[str, Any]) -> None:
    """Test that Pydantic models reject extra fields."""
    valid_agent_data["extra_field"] = "value"

    # If using ManifestLoader.load_from_dict, it calls model_validate
    with pytest.raises(ValidationError):  # ValidationError from Pydantic
        AgentDefinition.model_validate(valid_agent_data)

    # Check nested
    del valid_agent_data["extra_field"]
    valid_agent_data["metadata"]["extra"] = 1
    with pytest.raises(ValidationError):
        AgentDefinition.model_validate(valid_agent_data)
