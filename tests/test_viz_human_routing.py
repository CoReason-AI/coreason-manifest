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
    GraphEdge,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
)
from coreason_manifest.utils.viz import generate_mermaid_graph


def test_recipe_mermaid_human_routing() -> None:
    # 1. Create a HumanNode with routing and collaboration config
    human_node = HumanNode(
        id="human_decision",
        prompt="Review the plan?",
        collaboration=CollaborationConfig(
            mode="co_edit",
            render_strategy="json_forms",
        ),
        routes={
            "approve": "agent_execution",
            "reject": "end_workflow",
            "revise": "human_decision",  # Self-loop
        },
    )

    # 2. Create other nodes
    agent_node = AgentNode(id="agent_execution", agent_ref="execution_agent")
    end_node = AgentNode(id="end_workflow", agent_ref="terminator")

    nodes = [human_node, agent_node, end_node]
    edges: list[GraphEdge] = []

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="HumanRoutingTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="human_decision"),
    )

    # 4. Generate Graph
    chart = generate_mermaid_graph(recipe)

    # 5. Assertions

    # Check Icon and Protocol
    # We expect sanitized ID in label? No, label logic uses node.id directly but quotes are escaped.
    # The ID in mermaid definition is sanitized: human_decision
    # Label: "✍️ human_decision<br/>(Protocol: json_forms)"
    assert 'human_decision{{"✍️ human_decision<br/>(Protocol: json_forms)"}}:::human' in chart

    # Check Routing Edges
    # human_decision -- "approve" --> agent_execution
    assert 'human_decision -- "approve" --> agent_execution' in chart
    # human_decision -- "reject" --> end_workflow
    assert 'human_decision -- "reject" --> end_workflow' in chart
    # human_decision -- "revise" --> human_decision
    assert 'human_decision -- "revise" --> human_decision' in chart

def test_recipe_mermaid_human_default() -> None:
    # Test default icon and protocol
    human_node = HumanNode(
        id="simple_human",
        prompt="Simple?",
        # No collaboration config -> defaults
    )

    nodes = [human_node]
    edges: list[GraphEdge] = []

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="HumanDefaultTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="simple_human"),
    )

    chart = generate_mermaid_graph(recipe)

    # Default icon 👤, default strategy "default"
    assert 'simple_human{{"👤 simple_human<br/>(Protocol: default)"}}:::human' in chart
