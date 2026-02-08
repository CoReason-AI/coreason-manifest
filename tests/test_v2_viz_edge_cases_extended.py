# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    NodePresentation,
    PresentationHints,
    VisualizationStyle,
)


def test_null_viz_and_presentation() -> None:
    """Ensure both fields can be null without error."""
    node = AgentNode(id="node-1", agent_ref="ref-1")
    assert node.visualization is None
    assert node.presentation is None
    dumped = node.model_dump(mode="json")
    assert dumped["visualization"] is None
    assert dumped["presentation"] is None


def test_partial_updates_simulation() -> None:
    """Simulate a partial update scenario where only one aspect is modified."""
    # Start with layout only
    node = AgentNode(
        id="node-1",
        agent_ref="ref-1",
        presentation=NodePresentation(x=10, y=20),
    )
    assert node.visualization is None

    # Simulate adding visualization (recreating node as pydantic models are immutable/frozen)
    node_updated = node.model_copy(update={"visualization": PresentationHints(style=VisualizationStyle.TREE)})
    assert node_updated.presentation is not None
    assert node_updated.presentation.x == 10
    assert node_updated.visualization is not None
    assert node_updated.visualization.style == VisualizationStyle.TREE


def test_invalid_enum_boundary() -> None:
    """Test boundary conditions for enum validation."""
    with pytest.raises(ValidationError):
        PresentationHints(style="INVALID_STYLE_123")

    # Valid string input that matches enum value should work (case sensitive)
    hints = PresentationHints(style="TREE")
    assert hints.style == VisualizationStyle.TREE


def test_inheritance_chain_override() -> None:
    """Test overriding visualization in a subclass or copy."""
    original = AgentNode(
        id="base",
        agent_ref="ref",
        visualization=PresentationHints(style=VisualizationStyle.CHAT),
    )

    # Override with new hints
    new_hints = PresentationHints(style=VisualizationStyle.KANBAN)
    derived = original.model_copy(update={"visualization": new_hints})

    assert derived.visualization is not None
    assert derived.visualization.style == VisualizationStyle.KANBAN
    # Ensure original is untouched
    assert original.visualization is not None
    assert original.visualization.style == VisualizationStyle.CHAT


def test_color_hex_validation_loose() -> None:
    """
    Current spec allows any string for color, but verify it accepts
    standard hex codes and names.
    """
    p1 = NodePresentation(x=0, y=0, color="#FF0000")
    assert p1.color == "#FF0000"

    p2 = NodePresentation(x=0, y=0, color="red")
    assert p2.color == "red"

    # Verify None is allowed
    p3 = NodePresentation(x=0, y=0, color=None)
    assert p3.color is None


def test_hidden_fields_duplicates() -> None:
    """Test that hidden_fields handles duplicates (List allows them, Set would not)."""
    hints = PresentationHints(hidden_fields=["a", "b", "a"])
    assert len(hints.hidden_fields) == 3
    assert hints.hidden_fields == ["a", "b", "a"]
