# Copyright (c) 2025 CoReason, Inc.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    ExecutionPriority,
    GraphTopology,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
)


def test_edge_case_zero_limits() -> None:
    """Test that rate limits of 0 are valid (effectively blocking)."""
    policy = PolicyConfig(rate_limit_rpm=0, rate_limit_tpm=0)
    assert policy.rate_limit_rpm == 0
    assert policy.rate_limit_tpm == 0


def test_edge_case_large_limits() -> None:
    """Test very large integer values for limits."""
    large_val = 10**18  # Quintillion
    policy = PolicyConfig(rate_limit_rpm=large_val)
    assert policy.rate_limit_rpm == large_val


def test_edge_case_invalid_priority_value() -> None:
    """Test that priority strictly enforces Enum members (Pydantic validation)."""
    # Passing an integer not in the Enum should fail validation
    with pytest.raises(ValidationError) as excinfo:
        PolicyConfig(priority=99)  # 99 is not a valid ExecutionPriority

    assert "Input should be" in str(excinfo.value)


def test_complex_case_full_recipe_serialization() -> None:
    """Test serialization of a full Recipe with all QoS fields set."""
    policy = PolicyConfig(
        priority=ExecutionPriority.CRITICAL,
        rate_limit_rpm=60,
        rate_limit_tpm=10000,
        caching_enabled=False,
        max_retries=5,
        timeout_seconds=300,
        budget_cap_usd=100.0,
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex QoS Recipe"),
        interface=RecipeInterface(),
        policy=policy,
        topology=GraphTopology(nodes=[AgentNode(id="worker", agent_ref="worker-v1")], edges=[], entry_point="worker"),
    )

    dumped = recipe.model_dump()
    assert dumped["policy"]["priority"] == 10
    assert dumped["policy"]["rate_limit_rpm"] == 60
    assert dumped["policy"]["caching_enabled"] is False

    # Verify round-trip
    loaded = RecipeDefinition.model_validate(dumped)
    assert loaded.policy is not None
    assert loaded.policy.priority == ExecutionPriority.CRITICAL


def test_complex_case_nested_structure_immutability() -> None:
    """Test that PolicyConfig remains immutable when accessed via Recipe."""
    policy = PolicyConfig(priority=ExecutionPriority.LOW)
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Immutable Policy"),
        interface=RecipeInterface(),
        policy=policy,
        topology=GraphTopology(nodes=[AgentNode(id="a", agent_ref="b")], edges=[], entry_point="a"),
    )

    # Attempting to modify the frozen model should raise ValidationError
    with pytest.raises(ValidationError):
        recipe.policy.priority = ExecutionPriority.HIGH  # type: ignore


def test_edge_case_none_vs_missing() -> None:
    """Test distinction between explicit None and default None (should be same for Pydantic)."""
    p1 = PolicyConfig(rate_limit_rpm=None)
    p2 = PolicyConfig()

    assert p1.rate_limit_rpm is None
    assert p2.rate_limit_rpm is None
    assert p1.model_dump() == p2.model_dump()
