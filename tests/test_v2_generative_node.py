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

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GenerativeNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
    TaskSequence,
)


def test_generative_node_serialization() -> None:
    """Test that a GenerativeNode correctly serializes and deserializes."""
    node = GenerativeNode(
        id="gen-1",
        goal="Research competitor pricing",
        max_depth=5,
        strategy="bfs",
        allowed_tools=["tool-1", "tool-2"],
        output_schema={"type": "object", "properties": {"price": {"type": "number"}}},
    )

    # Dump to JSON (dict)
    data = node.model_dump(by_alias=True)
    assert data["type"] == "generative"
    assert data["goal"] == "Research competitor pricing"
    assert data["max_depth"] == 5
    assert data["strategy"] == "bfs"
    assert data["allowed_tools"] == ["tool-1", "tool-2"]

    # Round-trip
    node2 = GenerativeNode.model_validate(data)
    assert node2.id == "gen-1"
    assert node2.strategy == "bfs"


def test_generative_node_defaults() -> None:
    """Test default values for GenerativeNode."""
    node = GenerativeNode(id="gen-default", goal="Simple goal")
    assert node.max_depth == 3
    assert node.strategy == "hybrid"
    assert node.allowed_tools == []
    assert node.output_schema == {}


def test_generative_node_validation() -> None:
    """Test validation constraints."""
    # max_depth < 1 should fail
    with pytest.raises(ValidationError) as excinfo:
        GenerativeNode(id="bad-depth", goal="Fail", max_depth=0)
    assert "Input should be greater than or equal to 1" in str(excinfo.value)

    # Invalid strategy should fail
    with pytest.raises(ValidationError) as excinfo:
        GenerativeNode(
            id="bad-strategy",
            goal="Fail",
            strategy="invalid_strat",
        )
    assert "Input should be 'bfs', 'dfs' or 'hybrid'" in str(excinfo.value)


def test_recipe_with_generative_node() -> None:
    """Test that a RecipeDefinition can load a graph with a GenerativeNode."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Generative Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[
                GenerativeNode(id="gen-step", goal="Generate content"),
                AgentNode(id="agent-step", agent_ref="editor-agent"),
            ],
            edges=[{"source": "gen-step", "target": "agent-step"}],
            entry_point="gen-step",
        ),
    )

    json_str = recipe.model_dump_json()
    loaded = RecipeDefinition.model_validate_json(json_str)

    assert len(loaded.topology.nodes) == 2
    gen_node = next(n for n in loaded.topology.nodes if n.id == "gen-step")
    assert isinstance(gen_node, GenerativeNode)
    assert gen_node.goal == "Generate content"

    agent_node = next(n for n in loaded.topology.nodes if n.id == "agent-step")
    assert isinstance(agent_node, AgentNode)


def test_topology_validation_with_generative_node() -> None:
    """Test polymorphic deserialization in GraphTopology."""
    data = {
        "nodes": [
            {
                "type": "generative",
                "id": "gen-1",
                "goal": "Solve X",
                "strategy": "dfs",
            }
        ],
        "edges": [],
        "entry_point": "gen-1",
    }

    topology = GraphTopology.model_validate(data)
    assert isinstance(topology.nodes[0], GenerativeNode)
    assert topology.nodes[0].strategy == "dfs"


def test_task_sequence_with_generative_node() -> None:
    """Test that TaskSequence accepts GenerativeNode."""
    seq = TaskSequence(
        steps=[
            GenerativeNode(id="gen-1", goal="Goal 1"),
            GenerativeNode(id="gen-2", goal="Goal 2"),
        ]
    )
    graph = seq.to_graph()
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].source == "gen-1"
    assert graph.edges[0].target == "gen-2"


def test_edge_case_max_depth_boundary() -> None:
    """Test max_depth boundary conditions."""
    # Minimum valid depth
    node = GenerativeNode(id="min-depth", goal="Goal", max_depth=1)
    assert node.max_depth == 1

    # Large depth
    node = GenerativeNode(id="large-depth", goal="Goal", max_depth=100)
    assert node.max_depth == 100


def test_edge_case_allowed_tools() -> None:
    """Test allowed_tools with various inputs."""
    # Empty list (default)
    node = GenerativeNode(id="empty-tools", goal="Goal")
    assert node.allowed_tools == []

    # Duplicates are allowed by list type, but conceptually fine
    node = GenerativeNode(id="dup-tools", goal="Goal", allowed_tools=["t1", "t1"])
    assert node.allowed_tools == ["t1", "t1"]

    # Large list
    tools = [f"tool-{i}" for i in range(100)]
    node = GenerativeNode(id="large-tools", goal="Goal", allowed_tools=tools)
    assert len(node.allowed_tools) == 100


def test_complex_case_mixed_topology() -> None:
    """Test a mixed graph with GenerativeNode, RouterNode, and AgentNode."""
    # Gen -> Router -> (Agent1 | Agent2)
    nodes = [
        GenerativeNode(id="gen-start", goal="Analyze market", output_schema={"type": "object"}),
        RouterNode(
            id="router",
            input_key="market_sentiment",
            routes={"positive": "agent-buy", "negative": "agent-sell"},
            default_route="agent-hold",
        ),
        AgentNode(id="agent-buy", agent_ref="buyer-bot"),
        AgentNode(id="agent-sell", agent_ref="seller-bot"),
        AgentNode(id="agent-hold", agent_ref="holder-bot"),
    ]
    edges = [
        {"source": "gen-start", "target": "router"},
        {"source": "router", "target": "agent-buy"},
        {"source": "router", "target": "agent-sell"},
        {"source": "router", "target": "agent-hold"},
    ]

    topology = GraphTopology(nodes=nodes, edges=edges, entry_point="gen-start")
    assert len(topology.nodes) == 5
    assert len(topology.edges) == 4
    assert topology.verify_completeness() is True


def test_complex_case_chained_generative() -> None:
    """Test chaining multiple GenerativeNodes."""
    # Gen1 -> Gen2 -> Gen3
    seq = TaskSequence(
        steps=[
            GenerativeNode(id="g1", goal="Step 1"),
            GenerativeNode(id="g2", goal="Step 2"),
            GenerativeNode(id="g3", goal="Step 3"),
        ]
    )
    graph = seq.to_graph()
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.edges[0].source == "g1"
    assert graph.edges[0].target == "g2"
    assert graph.edges[1].source == "g2"
    assert graph.edges[1].target == "g3"


def test_complex_case_cycle_with_generative() -> None:
    """Test a GenerativeNode within a cyclic graph."""
    # Gen1 -> Agent -> Gen1 (Loop)
    nodes = [
        GenerativeNode(id="gen-loop", goal="Generate until perfect"),
        AgentNode(id="critic", agent_ref="critic-bot"),
    ]
    edges = [
        {"source": "gen-loop", "target": "critic"},
        {"source": "critic", "target": "gen-loop"},
    ]
    topology = GraphTopology(nodes=nodes, edges=edges, entry_point="gen-loop")
    assert topology.verify_completeness() is True

    # Verify structure
    assert topology.edges[0].source == "gen-loop"
    assert topology.edges[1].target == "gen-loop"


def test_complex_case_task_sequence_mixed() -> None:
    """Test TaskSequence with a mix of all node types."""
    seq = TaskSequence(
        steps=[
            GenerativeNode(id="step1", goal="Plan"),
            AgentNode(id="step2", agent_ref="executor"),
            GenerativeNode(id="step3", goal="Review"),
        ]
    )
    graph = seq.to_graph()
    assert len(graph.nodes) == 3
    assert isinstance(graph.nodes[0], GenerativeNode)
    assert isinstance(graph.nodes[1], AgentNode)
    assert isinstance(graph.nodes[2], GenerativeNode)
