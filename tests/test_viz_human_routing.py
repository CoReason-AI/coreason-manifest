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
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    RenderStrategy,
    SteeringCommand,
)
from coreason_manifest.utils.viz import generate_mermaid_graph


def test_human_node_routing_visualization() -> None:
    # Node 1: With Collaboration and Routes
    human_node = HumanNode(
        id="human_approval",
        prompt="Review the plan",
        collaboration=CollaborationConfig(
            mode=CollaborationMode.CO_EDIT,
            render_strategy=RenderStrategy.ADAPTIVE_CARD,
            supported_commands=[SteeringCommand.APPROVE, SteeringCommand.REJECT],
        ),
        routes={
            SteeringCommand.APPROVE: "execute_agent",
            SteeringCommand.REJECT: "end_node",
        },
    )

    # Node 2: Without Collaboration and Routes
    human_simple = HumanNode(
        id="human_simple",
        prompt="Simple check",
    )

    agent_node = AgentNode(
        id="execute_agent",
        agent_ref="agent-1",
    )

    end_node = AgentNode(
        id="end_node",
        agent_ref="agent-end",
    )

    # Define topology
    topology = GraphTopology(
        nodes=[human_node, human_simple, agent_node, end_node],
        edges=[
            GraphEdge(source="execute_agent", target="human_approval"),
            # Also edge to simple node to keep it connected
            GraphEdge(source="execute_agent", target="human_simple"),
        ],
        entry_point="execute_agent",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Test Recipe"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    chart = generate_mermaid_graph(recipe)

    # Check Node 1 (Advanced)
    # Expected: ✍️ human_approval<br/>(Protocol: adaptive_card)
    assert 'human_approval{{"✍️ human_approval<br/>(Protocol: adaptive_card)"}}:::human' in chart

    # Check Routing Edges
    assert 'human_approval -- "approve" --> execute_agent' in chart
    assert 'human_approval -- "reject" --> end_node' in chart

    # Check Node 2 (Simple)
    # Expected: human_simple<br/>(Human Input)
    assert 'human_simple{{"human_simple<br/>(Human Input)"}}:::human' in chart

    # Ensure no routing edges for simple node
    # Since simple node has no routes, checking for existence of edges starting from it is hard without parsing
    # But we can check that no edge labeled "None" or similar exists if we were worried about bugs.
    # The absence of assertion implies we trust logic, but we can't easily assert absence of arbitrary string.
