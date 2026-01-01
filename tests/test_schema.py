# Prosperity-3.0
import json
import os
import uuid
import pytest
from jsonschema import validate, ValidationError, FormatChecker
from typing import Any, Dict

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "coreason_manifest", "schemas", "agent.schema.json"
)

def load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

@pytest.fixture
def agent_schema() -> Dict[str, Any]:
    return load_schema()

@pytest.fixture
def valid_agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {
            "inputs": {"type": "object", "properties": {"query": {"type": "string"}}},
            "outputs": {"type": "string"},
        },
        "topology": {
            "steps": [{"id": "step1", "description": "First step"}],
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": ["tool:search"], "libraries": ["pandas==2.0.1"]},
    }

def test_schema_valid_agent(agent_schema: Dict[str, Any], valid_agent_data: Dict[str, Any]) -> None:
    """Test that a valid agent dictionary passes schema validation."""
    validate(instance=valid_agent_data, schema=agent_schema, format_checker=FormatChecker())

def test_schema_invalid_version(agent_schema: Dict[str, Any], valid_agent_data: Dict[str, Any]) -> None:
    """Test that an invalid SemVer version fails schema validation."""
    valid_agent_data["metadata"]["version"] = "invalid-version"
    with pytest.raises(ValidationError):
        validate(instance=valid_agent_data, schema=agent_schema, format_checker=FormatChecker())

def test_schema_invalid_uuid(agent_schema: Dict[str, Any], valid_agent_data: Dict[str, Any]) -> None:
    """Test that an invalid UUID fails schema validation."""
    valid_agent_data["metadata"]["id"] = "not-a-uuid"
    with pytest.raises(ValidationError):
        validate(instance=valid_agent_data, schema=agent_schema, format_checker=FormatChecker())

def test_schema_invalid_temperature(agent_schema: Dict[str, Any], valid_agent_data: Dict[str, Any]) -> None:
    """Test that temperature outside range fails schema validation."""
    valid_agent_data["topology"]["model_config"]["temperature"] = 2.5
    with pytest.raises(ValidationError):
        validate(instance=valid_agent_data, schema=agent_schema, format_checker=FormatChecker())

    valid_agent_data["topology"]["model_config"]["temperature"] = -0.1
    with pytest.raises(ValidationError):
        validate(instance=valid_agent_data, schema=agent_schema, format_checker=FormatChecker())

def test_schema_missing_required_field(agent_schema: Dict[str, Any], valid_agent_data: Dict[str, Any]) -> None:
    """Test that missing required field fails schema validation."""
    del valid_agent_data["metadata"]
    with pytest.raises(ValidationError):
        validate(instance=valid_agent_data, schema=agent_schema, format_checker=FormatChecker())
