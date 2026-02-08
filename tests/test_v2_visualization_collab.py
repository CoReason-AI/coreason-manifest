# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Literal

from pydantic import Field

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    NodePresentation,
    PresentationHints,
    RecipeNode,
    VisualizationStyle,
)


# Mock GenerativeNode since it doesn't exist in the codebase yet but is requested in the test plan
class GenerativeNode(RecipeNode):
    type: Literal["generative"] = "generative"
    solver: str = Field(..., description="Solver configuration")


def test_sota_configuration() -> None:
    """Create a GenerativeNode configured for 'Tree Search' visualization and 'Interactive' collaboration."""
    node = GenerativeNode(
        id="gen-1",
        solver="tree_search",
        visualization=PresentationHints(
            style=VisualizationStyle.TREE,
            display_title="Reasoning Tree",
            icon="lucide:brain-circuit",
        ),
        collaboration=CollaborationConfig(
            mode=CollaborationMode.INTERACTIVE,
            supported_commands=["/prune", "/branch"],
        ),
    )

    assert node.visualization is not None
    assert node.visualization.style == VisualizationStyle.TREE
    assert node.collaboration is not None
    assert node.collaboration.mode == CollaborationMode.INTERACTIVE
    assert "/prune" in node.collaboration.supported_commands


def test_magentic_ui_configuration() -> None:
    """Create an AgentNode configured for 'Document Co-Edit'."""
    node = AgentNode(
        id="agent-1",
        agent_ref="writer-agent",
        visualization=PresentationHints(
            style=VisualizationStyle.DOCUMENT,
            display_title="Shared Draft",
            hidden_fields=["scratchpad"],
        ),
        collaboration=CollaborationConfig(
            mode=CollaborationMode.CO_EDIT,
            feedback_schema={"rating": "int", "comment": "str"},
        ),
    )

    assert node.visualization is not None
    assert node.visualization.style == VisualizationStyle.DOCUMENT
    assert node.collaboration is not None
    assert node.collaboration.mode == CollaborationMode.CO_EDIT
    assert node.visualization.hidden_fields == ["scratchpad"]


def test_inheritance() -> None:
    """Ensure standard AgentNode accepts these fields without issue."""
    node = AgentNode(
        id="simple-agent",
        agent_ref="ref-1",
        visualization=PresentationHints(style=VisualizationStyle.CHAT),
        # collaboration is optional, defaults to None
    )

    assert node.visualization is not None
    assert node.visualization.style == VisualizationStyle.CHAT
    assert node.collaboration is None


def test_conflict_avoidance() -> None:
    """
    Test Case 3: Conflict Avoidance
    Verify that `presentation` (layout) and `visualization` (hints) coexist.
    """
    node = AgentNode(
        id="conflict-check",
        agent_ref="ref-conflict",
        presentation=NodePresentation(x=100, y=200, color="#FF0000"),
        visualization=PresentationHints(style=VisualizationStyle.KANBAN),
    )

    # Check Layout
    assert node.presentation is not None
    assert node.presentation.x == 100
    assert node.presentation.y == 200
    assert node.presentation.color == "#FF0000"

    # Check Visualization
    assert node.visualization is not None
    assert node.visualization.style == VisualizationStyle.KANBAN

    # Serialize and verify both keys exist
    dumped = node.model_dump(mode="json")
    assert "presentation" in dumped
    assert "visualization" in dumped
    assert dumped["presentation"]["x"] == 100.0
    assert dumped["visualization"]["style"] == "KANBAN"
