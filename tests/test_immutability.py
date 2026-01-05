# Prosperity-3.0
import uuid

import pytest
from pydantic import ValidationError

from coreason_manifest.models import (
    AgentDefinition,
    AgentDependencies,
    ModelConfig,
)


def test_model_config_immutability() -> None:
    """Test that ModelConfig is immutable."""
    config = ModelConfig(model="gpt-4", temperature=0.7)

    with pytest.raises(ValidationError):
        config.temperature = 0.8  # type: ignore[misc]

    with pytest.raises(ValidationError):
        config.model = "gpt-3.5"  # type: ignore[misc]


def test_agent_definition_immutability() -> None:
    """Test that AgentDefinition (root) is immutable."""
    agent_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Immutable Agent",
            "author": "Tester",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [],
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "original_hash",
    }

    agent = AgentDefinition(**agent_data)

    # Try to modify a direct field
    with pytest.raises(ValidationError):
        agent.integrity_hash = "modified_hash"  # type: ignore[misc]

    # Try to replace a nested model
    with pytest.raises(ValidationError):
        agent.dependencies = AgentDependencies(tools=["new_tool"], libraries=[])  # type: ignore[misc]


def test_nested_model_immutability() -> None:
    """Test that nested models accessed through the root are immutable."""
    agent_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Immutable Agent",
            "author": "Tester",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [],
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "original_hash",
    }

    agent = AgentDefinition(**agent_data)

    # Try to modify a field on a nested object
    with pytest.raises(ValidationError):
        agent.topology.llm_config.temperature = 0.9  # type: ignore[misc]

    with pytest.raises(ValidationError):
        agent.metadata.name = "New Name"  # type: ignore[misc]
