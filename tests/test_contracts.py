import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from coreason_manifest.definitions.contracts import InterfaceDefinition, ContractMetadata
from coreason_manifest.definitions.agent import AgentCapability, CapabilityType, DeliveryMode


def test_contract_metadata_creation():
    metadata = ContractMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Test Interface",
        author="Tester",
        created_at=datetime.utcnow()
    )
    assert metadata.name == "Test Interface"
    assert metadata.version == "1.0.0"

def test_interface_definition_creation():
    metadata = ContractMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Search Interface",
        author="Tester",
        created_at=datetime.utcnow()
    )

    interface = InterfaceDefinition(
        metadata=metadata,
        inputs={"type": "object", "properties": {"query": {"type": "string"}}},
        outputs={"type": "object", "properties": {"results": {"type": "array"}}},
        description="A standard search interface."
    )

    assert interface.inputs["type"] == "object"
    assert interface.description == "A standard search interface."

def test_agent_capability_validation_inline_schema():
    # Test valid capability with inline schema
    cap = AgentCapability(
        name="search",
        type=CapabilityType.ATOMIC,
        description="Search function",
        inputs={"type": "object"},
        outputs={"type": "object"}
    )
    assert cap.inputs is not None
    assert cap.outputs is not None
    assert cap.interface_id is None

def test_agent_capability_validation_interface_id():
    # Test valid capability with interface_id
    cap = AgentCapability(
        name="search",
        type=CapabilityType.ATOMIC,
        description="Search function",
        interface_id=uuid4()
    )
    assert cap.interface_id is not None
    assert cap.inputs is None
    assert cap.outputs is None

def test_agent_capability_validation_both():
    # Test valid capability with both (override)
    cap = AgentCapability(
        name="search",
        type=CapabilityType.ATOMIC,
        description="Search function",
        interface_id=uuid4(),
        inputs={"type": "object"},
        outputs={"type": "object"}
    )
    assert cap.interface_id is not None
    assert cap.inputs is not None

def test_agent_capability_validation_failure():
    # Test invalid capability (neither)
    with pytest.raises(ValidationError) as excinfo:
        AgentCapability(
            name="search",
            type=CapabilityType.ATOMIC,
            description="Search function"
        )
    assert "AgentCapability must define either 'interface_id' or both 'inputs' and 'outputs'" in str(excinfo.value)

def test_agent_capability_validation_partial_schema():
    # Test invalid capability (only inputs)
    with pytest.raises(ValidationError) as excinfo:
        AgentCapability(
            name="search",
            type=CapabilityType.ATOMIC,
            description="Search function",
            inputs={"type": "object"}
        )
    assert "AgentCapability must define either 'interface_id' or both 'inputs' and 'outputs'" in str(excinfo.value)
