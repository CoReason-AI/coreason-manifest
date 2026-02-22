import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import FlowMetadata, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode


def test_immutable_node() -> None:
    """
    Test that modifying a field on a Node instance raises a ValidationError (FrozenInstanceError).
    """
    node = AgentNode(id="agent_1", type="agent", profile="researcher", tools=["search"])

    with pytest.raises(ValidationError):
        node.id = "new_id"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        # Reassignment is forbidden
        node.tools = ["new_tool"]  # type: ignore[misc]


def test_immutable_flow() -> None:
    """
    Test that modifying a Flow instance raises a ValidationError.
    """
    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Test Flow", version="1.0.0", description="Test", tags=[]),
        steps=[],
    )

    with pytest.raises(ValidationError):
        flow.status = "published"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        flow.metadata.name = "New Name"  # type: ignore[misc]
