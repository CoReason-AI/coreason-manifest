import pytest
from pydantic import ValidationError

from coreason_manifest import AgentNode, NodePresentation
from coreason_manifest.spec.v2.recipe import PresentationHints, VisualizationStyle


def test_node_presentation_coordinates() -> None:
    """Verify coordinate handling and edge cases."""
    # Integer to Float Coercion
    p1 = NodePresentation(x=100, y=200)
    assert isinstance(p1.x, float)
    assert isinstance(p1.y, float)
    assert p1.x == 100.0
    assert p1.y == 200.0

    # Negative coordinates
    p2 = NodePresentation(x=-50.5, y=-10.0)
    assert p2.x == -50.5
    assert p2.y == -10.0

    # Zero coordinates
    p3 = NodePresentation(x=0, y=0)
    assert p3.x == 0.0
    assert p3.y == 0.0

    # Large values
    p4 = NodePresentation(x=1e6, y=1e6)
    assert p4.x == 1000000.0


def test_node_presentation_color_edge_cases() -> None:
    """Verify strict hex color validation."""
    # Case insensitivity for hex digits
    assert NodePresentation(x=0, y=0, color="#ABCDEF").color == "#ABCDEF"
    assert NodePresentation(x=0, y=0, color="#abcdef").color == "#abcdef"
    assert NodePresentation(x=0, y=0, color="#AbCdEf").color == "#AbCdEf"

    # Invalid lengths
    with pytest.raises(ValidationError):
        NodePresentation(x=0, y=0, color="#12345")  # Too short
    with pytest.raises(ValidationError):
        NodePresentation(x=0, y=0, color="#1234567")  # Too long

    # Missing hash
    with pytest.raises(ValidationError):
        NodePresentation(x=0, y=0, color="123456")

    # Invalid characters
    with pytest.raises(ValidationError):
        NodePresentation(x=0, y=0, color="#GGGGGG")
    with pytest.raises(ValidationError):
        NodePresentation(x=0, y=0, color="#12345G")


def test_node_presentation_label_edge_cases() -> None:
    """Verify label handling."""
    # Empty string is valid
    p1 = NodePresentation(x=0, y=0, label="")
    assert p1.label == ""

    # Long string
    long_label = "A" * 1000
    p2 = NodePresentation(x=0, y=0, label=long_label)
    assert p2.label == long_label

    # Special characters
    special = "Label with 😊 unicode and symbols !@#$%^&*()"
    p3 = NodePresentation(x=0, y=0, label=special)
    assert p3.label == special

    # None
    p4 = NodePresentation(x=0, y=0, label=None)
    assert p4.label is None


def test_node_presentation_z_index() -> None:
    """Verify z-index handling."""
    # Default
    assert NodePresentation(x=0, y=0).z_index == 0

    # Negative
    assert NodePresentation(x=0, y=0, z_index=-1).z_index == -1

    # Large positive
    assert NodePresentation(x=0, y=0, z_index=9999).z_index == 9999


def test_node_presentation_icon() -> None:
    """Verify icon field."""
    # Standard usage
    assert NodePresentation(x=0, y=0, icon="lucide:brain").icon == "lucide:brain"

    # None
    assert NodePresentation(x=0, y=0, icon=None).icon is None

    # Empty string
    assert NodePresentation(x=0, y=0, icon="").icon == ""


def test_recipe_node_integration_full() -> None:
    """Verify full integration within a node including metadata and presentation."""
    node = AgentNode(
        id="complex-node",
        agent_ref="agent-v1",
        metadata={"custom_key": "custom_value", "version": 1},
        visualization=PresentationHints(
            style=VisualizationStyle.TREE,
            display_title="My Node",
            icon="lucide:cpu",
        ),
    )

    dumped = node.model_dump(mode="json")

    # Check Presentation
    assert dumped["visualization"]["style"] == "TREE"
    assert dumped["visualization"]["display_title"] == "My Node"
    assert dumped["visualization"]["icon"] == "lucide:cpu"

    # Check Metadata
    assert dumped["metadata"]["custom_key"] == "custom_value"
    assert dumped["metadata"]["version"] == 1

    # Ensure separation
    assert "style" not in dumped["metadata"]
