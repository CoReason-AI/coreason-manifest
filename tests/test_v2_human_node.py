# Copyright (c) 2025 CoReason, Inc.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RenderStrategy,
    SteeringCommand,
)


def test_collaboration_config_deserialization() -> None:
    """Test that CollaborationConfig parses new fields correctly."""
    data = {
        "mode": "interactive",
        "supported_commands": ["approve", "reject"],
        "render_strategy": "adaptive_card",
        "trace_intervention": True,
    }
    config = CollaborationConfig.model_validate(data)

    assert config.supported_commands == [
        SteeringCommand.APPROVE,
        SteeringCommand.REJECT,
    ]
    assert config.render_strategy == RenderStrategy.ADAPTIVE_CARD
    assert config.trace_intervention is True


def test_collaboration_config_strict_typing_fail() -> None:
    """Test that invalid enum values raise ValidationError."""
    data = {
        "mode": "interactive",
        "supported_commands": ["approve", "make_coffee"],  # Invalid command
    }
    with pytest.raises(ValidationError) as exc:
        CollaborationConfig.model_validate(data)

    assert "make_coffee" in str(exc.value)


def test_human_node_with_routes() -> None:
    """Test that HumanNode parses routes correctly."""
    data = {
        "type": "human",
        "id": "human-1",
        "prompt": "Review this.",
        "routes": {
            "approve": "next-step",
            "reject": "end-step",
        },
    }
    node = HumanNode.model_validate(data)

    assert node.routes
    assert node.routes[SteeringCommand.APPROVE] == "next-step"
    assert node.routes[SteeringCommand.REJECT] == "end-step"


def test_topology_validation_human_routes_success() -> None:
    """Test that valid routes pass topology validation."""
    nodes = [
        HumanNode(
            id="human-1",
            prompt="Review",
            routes={
                SteeringCommand.APPROVE: "step-2",
                SteeringCommand.REJECT: "step-3",
            },
        ),
        AgentNode(id="step-2", agent_ref="agent-a"),
        AgentNode(id="step-3", agent_ref="agent-b"),
    ]
    # Implicit edges via routes don't need explicit graph edges for this test?
    # Wait, usually edges are explicit. But here flow is directed by routes.
    # However, GraphTopology requires valid edges if they exist.
    # If routes are used, edges might not be needed in the `edges` list strictly
    # for connectivity if the runner handles it, but topology validation checks
    # for dangling edges in `edges` list. Here we are testing
    # `validate_topology_integrity` which checks references.

    # We need to wrap it in RecipeDefinition to trigger the validator
    topology = GraphTopology(
        nodes=nodes,
        edges=[],  # No explicit edges needed for this specific validator check
        entry_point="human-1",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Test"),
        interface=RecipeInterface(),
        topology=topology,
    )

    node = recipe.topology.nodes[0]
    assert isinstance(node, HumanNode)
    assert node.routes
    assert node.routes[SteeringCommand.APPROVE] == "step-2"


def test_topology_validation_human_routes_failure() -> None:
    """Test that invalid routes fail topology validation."""
    nodes = [
        HumanNode(
            id="human-1",
            prompt="Review",
            routes={
                SteeringCommand.APPROVE: "step-2",  # Exists
                SteeringCommand.REJECT: "missing-step",  # Missing
            },
        ),
        AgentNode(id="step-2", agent_ref="agent-a"),
    ]

    # Use draft status for Topology, but RecipeDefinition validator runs regardless?
    # Actually RecipeDefinition validator runs `validate_topology_integrity`

    topology = GraphTopology(
        nodes=nodes,
        edges=[],
        entry_point="human-1",
        status="draft",
    )

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Test"),
            interface=RecipeInterface(),
            topology=topology,
        )

    assert "Topology Integrity Error" in str(exc.value)
    assert "missing-step" in str(exc.value)
