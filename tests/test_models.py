# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import uuid
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import (
    AgentCapability,
    AgentDefinition,
    AgentMetadata,
    CapabilityType,
    EventSchema,
    ModelConfig,
    Persona,
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
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {"type": "object", "properties": {"query": {"type": "string"}}},
                "outputs": {"type": "string"},
                "injected_params": [],  # Missing user_context
            }
        ],
        "config": {
            "nodes": [{"id": "step1", "type": "logic", "code": "pass"}],
            "edges": [],
            "entry_point": "step1",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {
            "tools": [
                {
                    "uri": "tool:search",
                    "hash": "a" * 64,
                    "scopes": ["read"],
                    "risk_level": "safe",
                }
            ],
            "libraries": ["pandas==2.0.1"],
        },
        "integrity_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }

    agent = AgentDefinition(**valid_data)
    assert agent.metadata.name == "Test Agent"
    assert agent.config.llm_config.temperature == 0.7
    assert len(agent.dependencies.libraries) == 1


def test_agent_metadata_invalid_version() -> None:
    """Test that invalid SemVer raises a ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        AgentMetadata(id=uuid.uuid4(), version="invalid-version", name="Test", author="Author", created_at="now")
    assert "String should match pattern" in str(excinfo.value)


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
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.5},
            "system_prompt": "Prompt",  # Added to satisfy Atomic Agent requirement
        },
        "dependencies": {},
        "status": "published",  # Added to trigger integrity_hash check
    }
    with pytest.raises(ValidationError) as excinfo:
        AgentDefinition(**valid_data)
    assert "integrity_hash" in str(excinfo.value)


def test_auth_validation_failure() -> None:
    """Test that auth requirement without user_context raises ValueError."""
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
            "requires_auth": True,
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {"type": "object", "properties": {"query": {"type": "string"}}},
                "outputs": {"type": "string"},
                "injected_params": [],  # Missing user_context
            }
        ],
        "config": {
            "nodes": [{"id": "step1", "type": "logic", "code": "pass"}],
            "edges": [],
            "entry_point": "step1",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "a" * 64,
    }
    with pytest.raises(
        ValueError, match="Agent requires authentication but capability 'default' does not inject 'user_context'."
    ):
        AgentDefinition(**data)


def test_agent_definition_with_policy_and_observability() -> None:
    """Test AgentDefinition with policy and observability fields."""
    valid_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Full Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Policy agent",
        },
        "dependencies": {"tools": [], "libraries": []},
        "policy": {"budget_caps": {"cost": 100.0}},
        "observability": {"trace_level": "full"},
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition(**valid_data)
    assert agent.policy is not None
    assert agent.policy.budget_caps["cost"] == 100.0
    assert agent.observability is not None
    assert agent.observability.trace_level == "full"


def test_model_config_system_prompt() -> None:
    """Test ModelConfig with system_prompt."""
    config = ModelConfig(model="gpt-4", temperature=0.7, system_prompt="You are a helpful assistant.")
    assert config.system_prompt == "You are a helpful assistant."

    config_no_prompt = ModelConfig(model="gpt-4", temperature=0.7)
    assert config_no_prompt.system_prompt is None


def test_persona() -> None:
    """Test Persona model."""
    persona = Persona(name="Helper", description="A helpful assistant", directives=["Be nice", "Help user"])
    assert persona.name == "Helper"
    assert len(persona.directives) == 2


def test_agent_config_system_prompt() -> None:
    """Test AgentRuntimeConfig with system_prompt."""
    valid_data: Dict[str, Any] = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Global instruction",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition(**valid_data)
    assert agent.config.system_prompt == "Global instruction"

    # Ensure optionality:
    # If we remove system_prompt from config AND model_config, validation should fail (Atomic Agent)
    del valid_data["config"]["system_prompt"]

    # In the valid_data setup above, nodes=[], so it is an Atomic Agent.
    # llm_config doesn't have system_prompt set.
    # So this should fail now.
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**valid_data)
    assert "Atomic Agents require a system_prompt" in str(exc.value)

    # But if we add it to model_config, it should pass
    valid_data["config"]["model_config"]["system_prompt"] = "Model Prompt"
    agent = AgentDefinition(**valid_data)
    assert agent.config.system_prompt is None
    assert agent.config.llm_config.system_prompt == "Model Prompt"


def test_agent_capability_events() -> None:
    """Test AgentCapability with EventSchema."""
    event = EventSchema(
        name="SEARCH_PROGRESS",
        data_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    assert event.name == "SEARCH_PROGRESS"
    assert event.data_schema["type"] == "object"

    capability = AgentCapability(
        name="test",
        type=CapabilityType.ATOMIC,
        description="Test capability",
        inputs={"type": "object"},
        outputs={"type": "string"},
        events=[event],
    )
    assert len(capability.events) == 1
    assert capability.events[0].name == "SEARCH_PROGRESS"

    # Test default factory
    capability_empty = AgentCapability(
        name="test",
        type=CapabilityType.ATOMIC,
        description="Test capability",
        inputs={"type": "object"},
        outputs={"type": "string"},
    )
    assert capability_empty.events == []


def test_agent_capabilities_validation() -> None:
    """Test validation of capabilities list."""
    valid_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Prompt",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    # Test empty capabilities
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(capabilities=[], **valid_data)
    assert "Agent must have at least one capability" in str(exc.value)

    # Test duplicate names
    cap = AgentCapability(name="dup", type=CapabilityType.ATOMIC, description="D", inputs={}, outputs={})
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(capabilities=[cap, cap], **valid_data)
    assert "Duplicate capability names found" in str(exc.value)
