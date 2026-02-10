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

from coreason_manifest.spec.common.presentation import NodePresentation, PresentationHints, ViewportMode
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    GenerativeNode,
    InteractionConfig,
    InterventionTrigger,
    TransparencyLevel,
)


def test_sota_tree_search_configuration() -> None:
    node = GenerativeNode(
        id="node-1",
        goal="Solve the problem",
        output_schema={"type": "string"},
        visualization=PresentationHints(
            initial_viewport=ViewportMode.PLANNER_CONSOLE,
            display_title="Reasoning Tree",
        ),
        collaboration=CollaborationConfig(
            mode=CollaborationMode.INTERACTIVE,
            supported_commands=["/prune"],
        ),
    )

    data = node.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert data["visualization"]["initial_viewport"] == "planner_console"
    assert data["visualization"]["display_title"] == "Reasoning Tree"
    assert data["collaboration"]["mode"] == "interactive"
    assert data["collaboration"]["supported_commands"] == ["/prune"]


def test_co_edit_agent() -> None:
    node = AgentNode(
        id="agent-1",
        agent_ref="agent-ref-1",
        visualization=PresentationHints(initial_viewport=ViewportMode.ARTIFACT_SPLIT),
        collaboration=CollaborationConfig(mode=CollaborationMode.CO_EDIT),
    )

    assert node.visualization is not None
    assert node.visualization.initial_viewport == ViewportMode.ARTIFACT_SPLIT
    assert node.collaboration is not None
    assert node.collaboration.mode == CollaborationMode.CO_EDIT


def test_conflict_avoidance() -> None:
    node = AgentNode(
        id="agent-1",
        agent_ref="agent-ref-1",
        presentation=NodePresentation(x=100, y=200, color="#0000FF"),
        visualization=PresentationHints(initial_viewport=ViewportMode.STREAM),
    )

    data = node.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Check that both fields exist and are correct
    assert data["presentation"]["x"] == 100
    assert data["presentation"]["y"] == 200
    assert data["visualization"]["initial_viewport"] == "stream"


def test_edge_cases() -> None:
    """Test optional fields, defaults, and validation."""
    # 1. Test defaults
    node = AgentNode(
        id="minimal",
        agent_ref="ref",
        visualization=PresentationHints(),  # Should use default initial_viewport=STREAM
        collaboration=CollaborationConfig(),  # Should use default mode=COMPLETION
    )
    assert node.visualization is not None
    assert node.visualization.initial_viewport == ViewportMode.STREAM
    assert node.visualization.hidden_fields == []
    assert node.collaboration is not None
    assert node.collaboration.mode == CollaborationMode.COMPLETION
    assert node.collaboration.supported_commands == []

    # 2. Test invalid Viewport Mode
    with pytest.raises(ValidationError) as exc:
        PresentationHints(initial_viewport="INVALID_STYLE")
    assert "Input should be 'stream', 'artifact_split', 'planner_console' or 'canvas'" in str(exc.value)

    # 3. Test invalid Collaboration Mode
    with pytest.raises(ValidationError) as exc:
        CollaborationConfig(mode="INVALID_MODE")
    assert "Input should be 'completion', 'interactive' or 'co_edit'" in str(exc.value)

    # 4. Test nullable fields
    hints = PresentationHints(
        initial_viewport=ViewportMode.CANVAS, display_title=None, icon=None, progress_indicator=None
    )
    assert hints.display_title is None

    # 5. Test empty hidden fields
    hints_empty = PresentationHints(hidden_fields=[])
    assert hints_empty.hidden_fields == []


def test_complex_configuration() -> None:
    """Test a node with all UX/Control planes configured."""
    node = GenerativeNode(
        id="complex-node",
        goal="Do everything",
        output_schema={"type": "object"},
        # 1. Layout
        presentation=NodePresentation(x=50, y=50, color="#FF0000"),
        # 2. Visualization
        visualization=PresentationHints(
            initial_viewport=ViewportMode.PLANNER_CONSOLE,
            display_title="Master Plan",
            icon="lucide:brain-circuit",
            hidden_fields=["internal_scratchpad"],
            progress_indicator="percent_complete",
        ),
        # 3. Collaboration
        collaboration=CollaborationConfig(
            mode=CollaborationMode.INTERACTIVE,
            feedback_schema={"type": "object", "properties": {"rating": {"type": "integer"}}},
            supported_commands=["/retry", "/explain"],
        ),
        # 4. Interaction (Control)
        interaction=InteractionConfig(
            transparency=TransparencyLevel.OBSERVABLE,
            triggers=[InterventionTrigger.ON_FAILURE],
            editable_fields=["goal"],
            guidance_hint="Watch closely",
        ),
    )

    data = node.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Assertions for complex structure
    assert data["presentation"]["color"] == "#FF0000"
    assert data["visualization"]["icon"] == "lucide:brain-circuit"
    assert "internal_scratchpad" in data["visualization"]["hidden_fields"]
    assert data["collaboration"]["feedback_schema"]["properties"]["rating"]["type"] == "integer"
    assert "/retry" in data["collaboration"]["supported_commands"]
    assert data["interaction"]["transparency"] == "observable"


def test_serialization_roundtrip() -> None:
    """Ensure data integrity after dump/load cycle."""
    original = AgentNode(
        id="roundtrip",
        agent_ref="ref",
        visualization=PresentationHints(initial_viewport=ViewportMode.CANVAS),
        collaboration=CollaborationConfig(mode=CollaborationMode.CO_EDIT),
    )

    # Dump to dict
    serialized = original.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Load back
    reloaded = AgentNode.model_validate(serialized)

    assert reloaded.id == original.id
    assert reloaded.visualization is not None
    assert reloaded.visualization.initial_viewport == ViewportMode.CANVAS
    assert reloaded.collaboration is not None
    assert reloaded.collaboration.mode == CollaborationMode.CO_EDIT
