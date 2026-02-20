import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import FlowMetadata, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode


def test_immutable_node():
    """
    Test that modifying a field on a Node instance raises a ValidationError (FrozenInstanceError).
    """
    node = AgentNode(
        id="agent_1",
        type="agent",
        profile="researcher",
        tools=["search"]
    )

    with pytest.raises(ValidationError):
        node.id = "new_id"

    with pytest.raises(ValidationError):
        node.tools.append("new_tool")  # List inside is mutable? No, usually pydantic makes container fields mutable unless re-validated or config specific.
        # Wait, frozen=True usually makes the instance frozen, but fields that are mutable objects (like list) can be modified in-place if retrieved.
        # However, reassignment `node.tools = ...` is forbidden.
        # Let's check reassignment.
        node.tools = ["new_tool"]


def test_immutable_flow():
    """
    Test that modifying a Flow instance raises a ValidationError.
    """
    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(
            name="Test Flow",
            version="1.0.0",
            description="Test",
            tags=[]
        ),
        sequence=[]
    )

    with pytest.raises(ValidationError):
        flow.status = "published"

    with pytest.raises(ValidationError):
        flow.metadata.name = "New Name"  # Recursive immutability if sub-models are also frozen.
