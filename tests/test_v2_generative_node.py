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
            strategy="invalid_strat"  # type: ignore
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
