import uuid
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import AgentCapability, CapabilityType, AgentDefinition
from coreason_manifest.definitions.contracts import InterfaceDefinition, ContractMetadata


def test_interface_definition_creation() -> None:
    """Test creating a valid InterfaceDefinition."""
    valid_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Corporate Search",
            "author": "IT Dept",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "inputs": {"type": "object", "properties": {"query": {"type": "string"}}},
        "outputs": {"type": "string"},
        "description": "Standard search interface",
    }
    interface = InterfaceDefinition(**valid_data)
    assert interface.metadata.name == "Corporate Search"
    assert interface.inputs["type"] == "object"


def test_agent_capability_with_interface_id() -> None:
    """Test AgentCapability valid when interface_id is provided and inputs/outputs omitted."""
    cap = AgentCapability(
        name="search",
        type=CapabilityType.ATOMIC,
        description="Search",
        interface_id=uuid.uuid4(),
    )
    assert cap.interface_id is not None
    assert cap.inputs is None
    assert cap.outputs is None


def test_agent_capability_with_inputs_outputs() -> None:
    """Test AgentCapability valid when inputs/outputs provided and interface_id omitted."""
    cap = AgentCapability(
        name="search",
        type=CapabilityType.ATOMIC,
        description="Search",
        inputs={"type": "object"},
        outputs={"type": "string"},
    )
    assert cap.interface_id is None
    assert cap.inputs is not None
    assert cap.outputs is not None


def test_agent_capability_invalid_both_missing() -> None:
    """Test AgentCapability invalid when both interface_id and inputs/outputs are missing."""
    with pytest.raises(ValidationError) as exc:
        AgentCapability(
            name="search",
            type=CapabilityType.ATOMIC,
            description="Search",
        )
    assert "If 'interface_id' is not provided, both 'inputs' and 'outputs' must be defined" in str(exc.value)


def test_agent_capability_partial_missing() -> None:
    """Test AgentCapability invalid when inputs present but outputs missing (and no interface_id)."""
    with pytest.raises(ValidationError) as exc:
        AgentCapability(
            name="search",
            type=CapabilityType.ATOMIC,
            description="Search",
            inputs={"type": "object"},
        )
    assert "If 'interface_id' is not provided, both 'inputs' and 'outputs' must be defined" in str(exc.value)


def test_agent_definition_validate_input_with_interface() -> None:
    """Test that validate_input raises ValueError if interface_id is used."""
    cap = AgentCapability(
        name="search",
        type=CapabilityType.ATOMIC,
        description="Search",
        interface_id=uuid.uuid4(),
    )

    # Create minimal agent definition
    agent = AgentDefinition(
        metadata={
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        capabilities=[cap],
        config={
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Prompt",
        },
        dependencies={},
        integrity_hash="a" * 64,
    )

    with pytest.raises(ValueError, match="uses an interface definition which cannot be resolved at runtime"):
        agent.validate_input("search", {"query": "test"})
