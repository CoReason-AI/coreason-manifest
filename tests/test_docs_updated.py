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
    GraphTopology,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
    StateDefinition,
)


def test_usage_doc_example() -> None:
    """Verify the example code in docs/usage.md works as expected."""
    # 1. Define Metadata
    metadata = ManifestMetadata(name="Research Recipe")

    # 2. Define Topology
    topology = GraphTopology(
        entry_point="step1",
        nodes=[
            AgentNode(
                id="step1",
                agent_ref="researcher-agent",
            ),
        ],
        edges=[],
    )

    # 3. Instantiate Manifest
    manifest = RecipeDefinition(
        kind="Recipe",
        metadata=metadata,
        interface=RecipeInterface(inputs={"topic": {"type": "string"}}, outputs={"summary": {"type": "string"}}),
        state=StateDefinition(properties={"notes": {"type": "string"}}, persistence="redis"),
        policy=PolicyConfig(max_retries=3),
        topology=topology,
    )

    assert manifest.metadata.name == "Research Recipe"
    assert manifest.interface.inputs["topic"]["type"] == "string"
    assert manifest.state is not None
    assert manifest.state.persistence == "redis"
    assert manifest.policy is not None
    assert manifest.policy.max_retries == 3


def test_graph_recipes_doc_example() -> None:
    """Verify the example YAML structure in docs/graph_recipes.md."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Blog Post Workflow"},
        "interface": {"inputs": {"topic": {"type": "string"}}, "outputs": {"final_post": {"type": "string"}}},
        "state": {
            "properties": {"draft": {"type": "string"}, "status": {"type": "string"}},
            "persistence": "ephemeral",
        },
        "policy": {"max_retries": 2, "timeout_seconds": 600},
        "topology": {
            "entry_point": "draft",
            "nodes": [{"type": "agent", "id": "draft", "agent_ref": "writer-agent"}],
            "edges": [],
        },
    }

    recipe = RecipeDefinition.model_validate(data)
    assert recipe.metadata.name == "Blog Post Workflow"
    assert recipe.interface.inputs["topic"]["type"] == "string"
    assert recipe.state is not None
    assert recipe.state.persistence == "ephemeral"
    assert recipe.policy is not None
    assert recipe.policy.max_retries == 2


def test_edge_case_empty_interface() -> None:
    """Test Recipe with default empty interface."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Empty Interface Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(entry_point="start", nodes=[AgentNode(id="start", agent_ref="agent-1")], edges=[]),
    )
    assert recipe.interface.inputs == {}
    assert recipe.interface.outputs == {}


def test_edge_case_state_defaults() -> None:
    """Test StateDefinition defaults (persistence='ephemeral')."""
    state = StateDefinition(properties={})
    assert state.persistence == "ephemeral"


def test_edge_case_policy_defaults() -> None:
    """Test PolicyConfig defaults."""
    policy = PolicyConfig()
    assert policy.max_retries == 0
    assert policy.timeout_seconds is None
    assert policy.execution_mode == "sequential"


def test_complex_case_full_stack() -> None:
    """Test a complex recipe with all optional fields and detailed configuration."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Recipe"),
        interface=RecipeInterface(
            inputs={"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}},
            outputs={"results": {"type": "array", "items": {"type": "object"}}},
        ),
        state=StateDefinition(
            properties={"counter": {"type": "integer"}, "logs": {"type": "array"}}, persistence="postgres"
        ),
        policy=PolicyConfig(max_retries=5, timeout_seconds=3600, execution_mode="parallel"),
        topology=GraphTopology(
            entry_point="start",
            nodes=[
                AgentNode(id="start", agent_ref="agent-1"),
                AgentNode(id="worker1", agent_ref="agent-2"),
                AgentNode(id="worker2", agent_ref="agent-3"),
            ],
            edges=[
                {"source": "start", "target": "worker1"},
                {"source": "start", "target": "worker2"},
            ],
        ),
    )

    assert recipe.interface.inputs["limit"]["default"] == 10
    assert recipe.state is not None
    assert recipe.state.persistence == "postgres"
    assert recipe.policy is not None
    assert recipe.policy.execution_mode == "parallel"
    assert len(recipe.topology.edges) == 2


def test_validation_state_persistence_enum() -> None:
    """Test that invalid persistence options raise ValidationError."""
    with pytest.raises(ValidationError):
        StateDefinition(
            properties={},
            persistence="invalid_db",
        )


def test_validation_policy_execution_mode_enum() -> None:
    """Test that invalid execution modes raise ValidationError."""
    with pytest.raises(ValidationError):
        PolicyConfig(execution_mode="random")
