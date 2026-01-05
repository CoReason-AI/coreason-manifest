# Prosperity-3.0
import uuid

import pytest
from pydantic import ValidationError

from coreason_manifest.models import (
    AgentDefinition,
    AgentMetadata,
    ModelConfig,
)


def test_agent_definition_valid() -> None:
    """Test creating a valid AgentDefinition."""
    valid_data = {
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
        "integrity_hash": "dummy_hash",
    }

    agent = AgentDefinition(**valid_data)
    assert agent.metadata.name == "Test Agent"
    assert agent.topology.llm_config.temperature == 0.7
    assert len(agent.dependencies.libraries) == 1


def test_agent_metadata_invalid_version() -> None:
    """Test that invalid SemVer raises a ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        AgentMetadata(id=uuid.uuid4(), version="invalid-version", name="Test", author="Author", created_at="now")
    assert "Version 'invalid-version' is not a valid SemVer string" in str(excinfo.value)


def test_agent_metadata_invalid_uuid() -> None:
    """Test that invalid UUID raises a ValidationError."""
    with pytest.raises(ValidationError):
        AgentMetadata(id="not-a-uuid", version="1.0.0", name="Test", author="Author", created_at="now")


def test_model_config_validation() -> None:
    """Test ModelConfig validation constraints."""
    # Temperature too high
    with pytest.raises(ValidationError):
        ModelConfig(model="gpt-4", temperature=2.1)

    # Temperature too low
    with pytest.raises(ValidationError):
        ModelConfig(model="gpt-4", temperature=-0.1)


def test_validation_error_on_missing_fields() -> None:
    """Test that missing required fields (like integrity_hash) raises ValidationError."""
    valid_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [], "model_config": {"model": "gpt-4", "temperature": 0.5}},
        "dependencies": {},
    }
    with pytest.raises(ValidationError) as excinfo:
        AgentDefinition(**valid_data)
    assert "integrity_hash" in str(excinfo.value)
