# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.recipe import FailureBehavior, RecipeNode, RecoveryConfig


def test_recovery_config_defaults() -> None:
    """Ensure default recovery strategy is fail-fast."""
    config = RecoveryConfig()
    assert config.behavior == FailureBehavior.FAIL_WORKFLOW
    assert config.max_retries is None
    assert config.retry_delay_seconds == 1.0


def test_recovery_retry_logic() -> None:
    """Test valid retry configurations."""
    config = RecoveryConfig(max_retries=3, retry_delay_seconds=0.5)
    assert config.max_retries == 3
    assert config.retry_delay_seconds == 0.5


def test_fallback_node_validation() -> None:
    """Test routing to a fallback node."""
    config = RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="agent_supervisor")
    assert config.fallback_node_id == "agent_supervisor"
    assert config.behavior == "route_to_fallback"


def test_node_integration() -> None:
    """Ensure a node can carry a recovery config."""
    node = RecipeNode(id="step_1", recovery=RecoveryConfig(max_retries=5))
    assert node.recovery is not None
    assert node.recovery.max_retries == 5


def test_serialization() -> None:
    """Verify JSON persistence."""
    node = RecipeNode(id="step_1", recovery=RecoveryConfig(behavior=FailureBehavior.IGNORE))
    data = node.model_dump(mode="json")
    assert data["recovery"]["behavior"] == "ignore"
