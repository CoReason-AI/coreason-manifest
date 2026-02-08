import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.recipe import ExecutionPriority, PolicyConfig, RecipeDefinition


def test_policy_config_instantiation() -> None:
    """Test instantiating PolicyConfig with new QoS fields."""
    policy = PolicyConfig(
        priority=ExecutionPriority.BATCH,
        rate_limit_rpm=60,
        rate_limit_tpm=1000,
        caching_enabled=False
    )

    assert policy.priority == ExecutionPriority.BATCH
    assert policy.rate_limit_rpm == 60
    assert policy.rate_limit_tpm == 1000
    assert policy.caching_enabled is False

def test_policy_config_defaults() -> None:
    """Test default values for PolicyConfig."""
    policy = PolicyConfig()

    assert policy.priority == ExecutionPriority.NORMAL
    assert policy.rate_limit_rpm is None
    assert policy.rate_limit_tpm is None
    assert policy.caching_enabled is True

def test_rate_limit_validation() -> None:
    """Test validation for rate limits (must be non-negative)."""
    # Should accept None
    policy = PolicyConfig(rate_limit_rpm=None)
    assert policy.rate_limit_rpm is None

    # Should accept 0
    policy = PolicyConfig(rate_limit_rpm=0)
    assert policy.rate_limit_rpm == 0

    # Should reject negative numbers
    with pytest.raises(ValidationError) as excinfo:
        PolicyConfig(rate_limit_rpm=-1)

    assert "Input should be greater than or equal to 0" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        PolicyConfig(rate_limit_tpm=-500)

    assert "Input should be greater than or equal to 0" in str(excinfo.value)

def test_integration_recipe_definition() -> None:
    """Test integrating PolicyConfig with RecipeDefinition."""
    from coreason_manifest.spec.v2.definitions import ManifestMetadata
    from coreason_manifest.spec.v2.recipe import RecipeInterface, GraphTopology, AgentNode

    policy = PolicyConfig(
        priority=ExecutionPriority.CRITICAL,
        rate_limit_rpm=100
    )

    # Minimal valid recipe setup
    agent = AgentNode(id="agent1", agent_ref="my-agent")
    topology = GraphTopology(
        nodes=[agent],
        edges=[],
        entry_point="agent1"
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="test-recipe"),
        interface=RecipeInterface(),
        topology=topology,
        policy=policy
    )

    assert recipe.policy is not None
    assert recipe.policy.priority == ExecutionPriority.CRITICAL
    assert recipe.policy.rate_limit_rpm == 100

    # Check serialization
    dump = recipe.model_dump()
    assert dump["policy"]["priority"] == ExecutionPriority.CRITICAL
    assert dump["policy"]["rate_limit_rpm"] == 100
