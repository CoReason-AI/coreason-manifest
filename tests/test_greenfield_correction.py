from datetime import datetime

import pytest

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.core.nodes import HumanNode, SteeringConfig
from coreason_manifest.spec.core.resilience import ErrorDomain, EscalationStrategy, RetryStrategy, SupervisionPolicy
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.spec.interop.telemetry import HumanSteeringEvent


def test_human_node_validation_shadow() -> None:
    # Shadow mode -> input_schema and options MUST be None

    # Valid
    HumanNode(
        id="h1",
        type="human",
        prompt="p",
        interaction_mode="shadow",
        escalation=EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10),
        input_schema=None,
        options=None,
    )

    # Invalid input_schema
    with pytest.raises(ManifestError) as excinfo:
        HumanNode(
            id="h2",
            type="human",
            prompt="p",
            interaction_mode="shadow",
            escalation=EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10),
            input_schema={"type": "object"},
        )
    assert "cannot have 'input_schema'" in str(excinfo.value)

    # Invalid options
    with pytest.raises(ManifestError) as excinfo:
        HumanNode(
            id="h3",
            type="human",
            prompt="p",
            interaction_mode="shadow",
            escalation=EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10),
            options=["a", "b"],
        )
    assert "cannot have 'input_schema' or 'options'" in str(excinfo.value)


def test_human_node_validation_hijack() -> None:
    # Hijack only -> steering_config MUST be present

    # Valid
    HumanNode(
        id="h4",
        type="human",
        prompt="p",
        interaction_mode="hijack_only",
        escalation=EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10),
        steering_config=SteeringConfig(allow_variable_mutation=True),
    )

    # Invalid missing steering_config
    with pytest.raises(ManifestError) as excinfo:
        HumanNode(
            id="h5",
            type="human",
            prompt="p",
            interaction_mode="hijack_only",
            escalation=EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10),
            steering_config=None,
        )
    assert "requires 'steering_config'" in str(excinfo.value)


def test_builder_with_human_steering_upgrade() -> None:
    # Case 1: No previous resilience
    builder = AgentBuilder("a1").with_identity("r", "p")
    builder.with_human_steering(timeout=100)
    node = builder.build()
    assert isinstance(node.resilience, EscalationStrategy)
    assert node.resilience.timeout_seconds == 100

    # Case 2: Existing RecoveryStrategy (Retry)
    builder2 = AgentBuilder("a2").with_identity("r", "p")
    builder2.with_resilience(retries=3, strategy="retry")
    assert isinstance(builder2.resilience, RetryStrategy)

    builder2.with_human_steering(timeout=200)
    node2 = builder2.build()

    # Should be upgraded to SupervisionPolicy
    assert isinstance(node2.resilience, SupervisionPolicy)
    policy = node2.resilience

    # Should contain handlers for both
    strategies = [h.strategy for h in policy.handlers]
    # One retry, one escalate
    assert any(isinstance(s, RetryStrategy) for s in strategies)
    assert any(isinstance(s, EscalationStrategy) for s in strategies)

    # Also default strategy should be escalation
    assert isinstance(policy.default_strategy, EscalationStrategy)

    # Case 3: Existing SupervisionPolicy
    builder3 = AgentBuilder("a3").with_identity("r", "p")
    # Manually set supervision policy
    builder3.resilience = SupervisionPolicy(
        handlers=[
            # Some handler
        ],
        default_strategy=None,
    )

    # Need to properly construct SupervisionPolicy with handlers
    # Import ErrorHandler/ErrorDomain
    from coreason_manifest.spec.core.resilience import ErrorHandler

    builder3.resilience = SupervisionPolicy(
        handlers=[ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=RetryStrategy(max_attempts=1))]
    )

    builder3.with_human_steering(timeout=300)
    node3 = builder3.build()

    assert isinstance(node3.resilience, SupervisionPolicy)
    # Should have appended handler
    assert len(node3.resilience.handlers) == 2
    assert isinstance(node3.resilience.handlers[1].strategy, EscalationStrategy)


def test_telemetry_human_steering_event() -> None:
    event = HumanSteeringEvent(
        checkpoint_id="chk_1", timestamp=datetime.now(), mutated_variables={"var": 1}, human_identity="user@example.com"
    )
    assert event.checkpoint_id == "chk_1"
    assert event.human_identity == "user@example.com"


def test_steering_config_validation() -> None:
    # Test that allowed_targets is invalid if allow_variable_mutation is False
    with pytest.raises(ManifestError) as excinfo:
        SteeringConfig(allow_variable_mutation=False, allowed_targets=["var1"])
    assert "SteeringConfig defines 'allowed_targets' but 'allow_variable_mutation' is False" in str(excinfo.value)

    # Test valid case
    cfg = SteeringConfig(allow_variable_mutation=True, allowed_targets=["var1"])
    assert cfg.allow_variable_mutation is True
    assert cfg.allowed_targets == ["var1"]

    # Test valid case with no targets (implicitly allowed all)
    cfg2 = SteeringConfig(allow_variable_mutation=True)
    assert cfg2.allowed_targets is None


def test_builder_supervision_limits() -> None:
    # Test dynamic limit calculation in with_human_steering
    builder = AgentBuilder("agent1").with_identity("role", "persona")

    # Set a retry strategy with high attempts
    builder.with_resilience(retries=15, strategy="retry")

    # Upgrade to human steering
    builder.with_human_steering(timeout=300)

    node = builder.build()
    assert isinstance(node.resilience, SupervisionPolicy)
    # 15 retries + 1 escalation > 10, so limit should be 16
    assert node.resilience.max_cumulative_actions == 16


def test_builder_fallback_exposure() -> None:
    builder = AgentBuilder("agent1").with_identity("role", "persona")
    builder.with_human_steering(timeout=300, fallback_id="fallback_node")

    node = builder.build()
    # If it was upgraded to Supervision, we need to check the strategy inside handlers
    # Or if it's direct EscalationStrategy (if no previous resilience)

    if isinstance(node.resilience, EscalationStrategy):
        assert node.resilience.fallback_node_id == "fallback_node"
    elif isinstance(node.resilience, SupervisionPolicy):
        # Find the escalation strategy
        esc_handler = next(h for h in node.resilience.handlers if isinstance(h.strategy, EscalationStrategy))
        assert isinstance(esc_handler.strategy, EscalationStrategy)
        assert esc_handler.strategy.fallback_node_id == "fallback_node"

        assert isinstance(node.resilience.default_strategy, EscalationStrategy)
        assert node.resilience.default_strategy.fallback_node_id == "fallback_node"
