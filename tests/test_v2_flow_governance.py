# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    FailureBehavior,
    RecipeNode,
    RecoveryConfig,
)


def test_fallback_configuration() -> None:
    """Test creating a node with fallback behavior."""
    node = AgentNode(
        id="agent-1",
        agent_ref="some-agent",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="fallback-agent",
            max_retries=3,
        ),
    )
    assert node.recovery is not None
    assert node.recovery.behavior == FailureBehavior.ROUTE_TO_FALLBACK
    assert node.recovery.fallback_node_id == "fallback-agent"
    assert node.recovery.max_retries == 3


def test_default_value_configuration() -> None:
    """Test creating a node with default output behavior."""
    default_payload = {"status": "skipped", "reason": "failed"}
    node = AgentNode(
        id="agent-2",
        agent_ref="some-agent",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.CONTINUE_WITH_DEFAULT,
            default_output=default_payload,
            retry_delay_seconds=2.5,
        ),
    )
    assert node.recovery is not None
    assert node.recovery.behavior == FailureBehavior.CONTINUE_WITH_DEFAULT
    assert node.recovery.default_output == default_payload
    assert node.recovery.retry_delay_seconds == 2.5


def test_serialization() -> None:
    """Test that recovery config is correctly serialized."""
    node = AgentNode(
        id="agent-3",
        agent_ref="some-agent",
        recovery=RecoveryConfig(behavior=FailureBehavior.FAIL_WORKFLOW),
    )

    dumped = node.model_dump(mode="json")
    assert dumped["recovery"]["behavior"] == "fail_workflow"
    assert dumped["recovery"]["retry_delay_seconds"] == 1.0  # Default check


def test_base_node_integration() -> None:
    """Test that base RecipeNode supports recovery field."""
    # Since RecipeNode is abstract-ish (but not ABC), we can try to instantiate subclasses or check fields.
    # AgentNode inherits from RecipeNode.
    assert "recovery" in RecipeNode.model_fields
