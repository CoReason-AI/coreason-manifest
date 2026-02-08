# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    GraphEdge,
    GraphTopology,
    PresentationHints,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
    VisualizationStyle,
)


def test_full_spectrum_node() -> None:
    """Test a node with all presentation and collaboration fields populated."""
    node = AgentNode(
        id="full-node",
        agent_ref="super-agent",
        presentation=PresentationHints(
            style=VisualizationStyle.TREE,
            display_title="Complex Reasoner",
            icon="lucide:brain-circuit",
            hidden_fields=["context.history", "debug_log"],
            progress_indicator="progress.percent",
        ),
        collaboration=CollaborationConfig(
            mode=CollaborationMode.INTERACTIVE,
            feedback_schema={"type": "object", "properties": {"score": {"type": "integer"}}},
            supported_commands=["/stop", "/restart", "/explain"],
        ),
    )

    dumped = node.model_dump(mode="json")

    # Verify Presentation
    assert dumped["presentation"]["style"] == "TREE"
    assert dumped["presentation"]["display_title"] == "Complex Reasoner"
    assert dumped["presentation"]["icon"] == "lucide:brain-circuit"
    assert dumped["presentation"]["hidden_fields"] == ["context.history", "debug_log"]
    assert dumped["presentation"]["progress_indicator"] == "progress.percent"

    # Verify Collaboration
    assert dumped["collaboration"]["mode"] == "INTERACTIVE"
    assert "score" in dumped["collaboration"]["feedback_schema"]["properties"]
    assert dumped["collaboration"]["supported_commands"] == ["/stop", "/restart", "/explain"]


def test_hybrid_workflow_visualization() -> None:
    """Test a recipe mixing nodes with different visualization styles."""

    # 1. Chat Node (Default)
    start_node = AgentNode(id="start", agent_ref="ref-1", presentation=PresentationHints(style=VisualizationStyle.CHAT))

    # 2. Tree Search Node
    search_node = AgentNode(
        id="deep-search", agent_ref="ref-2", presentation=PresentationHints(style=VisualizationStyle.TREE)
    )

    # 3. Kanban Node
    task_node = AgentNode(
        id="tasks", agent_ref="ref-3", presentation=PresentationHints(style=VisualizationStyle.KANBAN)
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Hybrid Viz"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[start_node, search_node, task_node],
            edges=[GraphEdge(source="start", target="deep-search"), GraphEdge(source="deep-search", target="tasks")],
            entry_point="start",
        ),
    )

    assert len(recipe.topology.nodes) == 3
    styles = [node.presentation.style for node in recipe.topology.nodes if node.presentation]
    assert VisualizationStyle.CHAT in styles
    assert VisualizationStyle.TREE in styles
    assert VisualizationStyle.KANBAN in styles


def test_orchestrator_pattern_collaboration() -> None:
    """Test a Router directing to nodes with different CollaborationModes."""

    # Router (Automated)
    router = RouterNode(
        id="orchestrator",
        input_key="intent",
        routes={"help": "human-help", "info": "bot-info"},
        default_route="bot-info",
    )

    # Interactive Node (Human-on-the-Loop)
    human_node = AgentNode(
        id="human-help", agent_ref="human-agent", collaboration=CollaborationConfig(mode=CollaborationMode.INTERACTIVE)
    )

    # Completion Node (Standard)
    bot_node = AgentNode(
        id="bot-info", agent_ref="bot-agent", collaboration=CollaborationConfig(mode=CollaborationMode.COMPLETION)
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Collab Orchestrator"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[router, human_node, bot_node],
            edges=[
                GraphEdge(source="orchestrator", target="human-help"),
                GraphEdge(source="orchestrator", target="bot-info"),
            ],
            entry_point="orchestrator",
        ),
    )

    # Verify configurations persist in topology
    nodes_map = {node.id: node for node in recipe.topology.nodes}

    assert nodes_map["human-help"].collaboration is not None
    assert nodes_map["human-help"].collaboration.mode == CollaborationMode.INTERACTIVE
    assert nodes_map["bot-info"].collaboration is not None
    assert nodes_map["bot-info"].collaboration.mode == CollaborationMode.COMPLETION
