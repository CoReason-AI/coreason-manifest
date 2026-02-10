# Copyright (c) 2025 CoReason, Inc.

from coreason_manifest.spec.common.presentation import (
    ComponentSpec,
    ComponentType,
    PresentationHints,
    ViewportMode,
)
from coreason_manifest.spec.v2.recipe import AgentNode


def test_presentation_hints_viewport_initialization() -> None:
    """Test initializing PresentationHints with ViewportMode.PLANNER_CONSOLE."""
    hints = PresentationHints(initial_viewport=ViewportMode.PLANNER_CONSOLE)
    assert hints.initial_viewport == ViewportMode.PLANNER_CONSOLE
    assert hints.initial_viewport == "planner_console"


def test_component_spec_serialization() -> None:
    """Test defining a mutable ComponentSpec and verifying serialization."""
    comp = ComponentSpec(
        id="plan-editor-1",
        type=ComponentType.CODE_EDITOR,
        title="Plan Editor",
        data_source="plan.markdown",
        is_mutable=True,
        mutation_handler_ref="handler-1",
    )

    dumped = comp.model_dump(mode="json")

    assert dumped["id"] == "plan-editor-1"
    assert dumped["type"] == "code_editor"
    assert dumped["title"] == "Plan Editor"
    assert dumped["data_source"] == "plan.markdown"
    assert dumped["is_mutable"] is True
    assert dumped["mutation_handler_ref"] == "handler-1"


def test_agent_node_with_magentic_hints() -> None:
    """Verify that AgentNode loads correctly with the new PresentationHints."""
    hints = PresentationHints(
        initial_viewport=ViewportMode.ARTIFACT_SPLIT,
        components=[
            ComponentSpec(
                id="comp-1",
                type=ComponentType.MARKDOWN,
                data_source="output",
            )
        ],
        display_title="Magentic Agent",
    )

    node = AgentNode(
        id="agent-1",
        agent_ref="agent-ref-1",
        visualization=hints,
    )

    assert node.visualization is not None
    assert node.visualization.initial_viewport == ViewportMode.ARTIFACT_SPLIT
    assert len(node.visualization.components) == 1
    assert node.visualization.components[0].id == "comp-1"
    assert node.visualization.display_title == "Magentic Agent"

    # Verify serialization
    dumped = node.model_dump(mode="json")
    assert dumped["visualization"]["initial_viewport"] == "artifact_split"
    assert dumped["visualization"]["components"][0]["type"] == "markdown"
