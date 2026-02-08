from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    FailureBehavior,
    RecoveryConfig,
)


def test_fallback_configuration() -> None:
    """Test creating a node with ROUTE_TO_FALLBACK behavior."""
    node = AgentNode(
        id="agent-fail",
        agent_ref="agent-a",
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
    """Test creating a node with CONTINUE_WITH_DEFAULT behavior."""
    default_payload = {"status": "skipped", "reason": "timeout"}
    node = AgentNode(
        id="agent-skip",
        agent_ref="agent-b",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.CONTINUE_WITH_DEFAULT,
            default_output=default_payload,
        ),
    )

    assert node.recovery is not None
    assert node.recovery.behavior == FailureBehavior.CONTINUE_WITH_DEFAULT
    assert node.recovery.default_output == default_payload


def test_serialization() -> None:
    """Verify that recovery fields persist correctly in the Recipe JSON."""
    node = AgentNode(
        id="agent-persist",
        agent_ref="agent-c",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.IGNORE,
            retry_delay_seconds=5.0,
        ),
    )

    # Serialize
    json_str = node.model_dump_json()

    # Deserialize
    restored_node = AgentNode.model_validate_json(json_str)

    assert restored_node.recovery is not None
    assert restored_node.recovery.behavior == FailureBehavior.IGNORE
    assert restored_node.recovery.retry_delay_seconds == 5.0
