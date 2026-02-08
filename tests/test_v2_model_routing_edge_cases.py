# Copyright (c) 2025 CoReason, Inc.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.recipe import AgentNode, RecipeDefinition, RecipeInterface, GraphTopology
from coreason_manifest.spec.v2.resources import ModelSelectionPolicy, RoutingStrategy, ComplianceTier
from coreason_manifest.spec.v2.definitions import ManifestMetadata


def test_model_selection_policy_empty_constraints() -> None:
    """Test that a policy with no constraints is valid."""
    policy = ModelSelectionPolicy(strategy=RoutingStrategy.PRIORITY)
    assert policy.strategy == RoutingStrategy.PRIORITY
    assert policy.min_context_window is None
    assert policy.max_input_cost_per_m is None
    assert policy.compliance == []
    assert policy.provider_whitelist == []


def test_agent_node_explicit_none_policy() -> None:
    """Test that setting model_policy to None explicitly is allowed."""
    node = AgentNode(id="agent-1", agent_ref="agent-a", model_policy=None)
    assert node.model_policy is None


def test_recipe_definition_invalid_default_policy() -> None:
    """Test that passing an invalid type to default_model_policy raises ValidationError."""
    with pytest.raises(ValidationError):
        RecipeDefinition(
            metadata=ManifestMetadata(name="Invalid Recipe"),
            interface=RecipeInterface(),
            topology=GraphTopology(nodes=[AgentNode(id="start", agent_ref="agent-1")], edges=[], entry_point="start"),
            default_model_policy="not-a-policy-object",  # type: ignore[arg-type]
        )


def test_compliance_tier_validation() -> None:
    """Test that invalid compliance tiers are rejected."""
    with pytest.raises(ValidationError):
        ModelSelectionPolicy(
            strategy=RoutingStrategy.PRIORITY,
            compliance=["invalid_compliance"],  # type: ignore[list-item]
        )


def test_routing_strategy_validation() -> None:
    """Test that invalid routing strategies are rejected."""
    with pytest.raises(ValidationError):
        ModelSelectionPolicy(
            strategy="random_strategy"  # type: ignore[arg-type]
        )


def test_agent_node_invalid_model_policy_type() -> None:
    """Test that model_policy rejects invalid types (e.g., int)."""
    with pytest.raises(ValidationError):
        AgentNode(
            id="agent-1",
            agent_ref="agent-a",
            model_policy=123,  # type: ignore[arg-type]
        )
