import pytest
from coreason_manifest.spec.v2.recipe import (
    RecipeNode,
    RecoveryConfig,
    FailureBehavior
)

def test_recovery_config_defaults():
    """Ensure default recovery strategy is fail-fast."""
    config = RecoveryConfig()
    assert config.behavior == FailureBehavior.FAIL_WORKFLOW
    assert config.max_retries is None
    assert config.retry_delay_seconds == 1.0

def test_recovery_retry_logic():
    """Test valid retry configurations."""
    config = RecoveryConfig(max_retries=3, retry_delay_seconds=0.5)
    assert config.max_retries == 3
    assert config.retry_delay_seconds == 0.5

def test_fallback_node_validation():
    """Test routing to a fallback node."""
    config = RecoveryConfig(
        behavior=FailureBehavior.ROUTE_TO_FALLBACK,
        fallback_node_id="agent_supervisor"
    )
    assert config.fallback_node_id == "agent_supervisor"
    assert config.behavior == "route_to_fallback"

def test_node_integration():
    """Ensure a node can carry a recovery config."""
    node = RecipeNode(
        id="step_1",
        recovery=RecoveryConfig(max_retries=5)
    )
    assert node.recovery is not None
    assert node.recovery.max_retries == 5

def test_serialization():
    """Verify JSON persistence."""
    node = RecipeNode(
        id="step_1",
        recovery=RecoveryConfig(behavior=FailureBehavior.IGNORE)
    )
    data = node.model_dump(mode='json')
    assert data['recovery']['behavior'] == 'ignore'
