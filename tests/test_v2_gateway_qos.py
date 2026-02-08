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


def test_policy_config_instantiation() -> None:
    """Test standard instantiation of PolicyConfig."""
    policy = PolicyConfig(
        priority=ExecutionPriority.BATCH,
        rate_limit_rpm=60,
        rate_limit_tpm=1000,
        caching_enabled=False,
    )

    assert policy.priority == ExecutionPriority.BATCH
    assert policy.rate_limit_rpm == 60
    assert policy.rate_limit_tpm == 1000
    assert policy.caching_enabled is False


def test_policy_config_defaults() -> None:
    """Test default values of PolicyConfig."""
    policy = PolicyConfig()

    assert policy.priority == ExecutionPriority.NORMAL
    assert policy.rate_limit_rpm is None
    assert policy.rate_limit_tpm is None
    assert policy.caching_enabled is True


def test_policy_config_validation_negative_rpm() -> None:
    """Test that rate_limit_rpm rejects negative numbers."""
    with pytest.raises(ValidationError) as excinfo:
        PolicyConfig(rate_limit_rpm=-1)

    assert "Input should be greater than or equal to 0" in str(excinfo.value)


def test_policy_config_validation_negative_tpm() -> None:
    """Test that rate_limit_tpm rejects negative numbers."""
    with pytest.raises(ValidationError) as excinfo:
        PolicyConfig(rate_limit_tpm=-100)

    assert "Input should be greater than or equal to 0" in str(excinfo.value)


def test_recipe_definition_with_qos_policy() -> None:
    """Test integration of QoS-enhanced PolicyConfig within a RecipeDefinition."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(
            name="QoS Test Recipe",
        ),
        interface=RecipeInterface(),
        policy=PolicyConfig(
            priority=ExecutionPriority.CRITICAL,
            rate_limit_rpm=120,
        ),
        topology=GraphTopology(
            nodes=[
                AgentNode(id="start", agent_ref="agent-1"),
            ],
            edges=[],
            entry_point="start",
        ),
    )

    # Dump to dict and verify
    dumped = recipe.model_dump()
    assert dumped["policy"]["priority"] == 10  # CRITICAL is 10
    assert dumped["policy"]["rate_limit_rpm"] == 120
    assert dumped["policy"]["caching_enabled"] is True  # Default

    # Round-trip JSON
    json_str = recipe.model_dump_json()
    loaded = RecipeDefinition.model_validate_json(json_str)

    assert loaded.policy is not None
    assert loaded.policy.priority == ExecutionPriority.CRITICAL
    assert loaded.policy.rate_limit_rpm == 120


# --- User Requested Tests ---

def test_qos_priority_enum_user_requested() -> None:
    """Verify traffic priority levels."""
    assert ExecutionPriority.CRITICAL == 10
    assert ExecutionPriority.NORMAL == 5
    assert ExecutionPriority.BATCH == 1

def test_policy_qos_fields_user_requested() -> None:
    """Ensure PolicyConfig accepts rate limits and priority."""
    policy = PolicyConfig(
        budget_cap_usd=100.0,
        priority=ExecutionPriority.HIGH,
        rate_limit_rpm=120,
        rate_limit_tpm=50000,
        caching_enabled=False
    )

    assert policy.priority == ExecutionPriority.HIGH
    assert policy.rate_limit_rpm == 120
    assert policy.caching_enabled is False

def test_qos_defaults_user_requested() -> None:
    """Verify default QoS settings."""
    policy = PolicyConfig(budget_cap_usd=1.0)
    assert policy.priority == ExecutionPriority.NORMAL
    assert policy.caching_enabled is True
    assert policy.rate_limit_rpm is None

def test_serialization_user_requested() -> None:
    """Verify JSON persistence of QoS fields."""
    policy = PolicyConfig(
        budget_cap_usd=1.0,
        priority=ExecutionPriority.BATCH
    )
    data = policy.model_dump(mode='json')
    assert data['priority'] == 1  # IntEnum serializes to value
