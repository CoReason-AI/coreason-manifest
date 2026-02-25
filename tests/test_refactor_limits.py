import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    ReflexionStrategy,
    RetryStrategy,
    SupervisionPolicy,
)


def test_infinite_retry() -> None:
    # Should pass
    rs = RetryStrategy(max_attempts="infinite", backoff_factor=1.5)
    assert rs.max_attempts == "infinite"

    # Should fail
    with pytest.raises(ValidationError):
        RetryStrategy(max_attempts=-1)

    # Cross-field validation: max_delay < initial_delay
    with pytest.raises(ValueError, match="must be greater than or equal to"):
        RetryStrategy(max_attempts=3, initial_delay_seconds=10.0, max_delay_seconds=5.0)


def test_retry_strategy_zero_initial_delay() -> None:
    # Should fail: initial_delay_seconds must be > 0.0
    with pytest.raises(ValidationError):
        RetryStrategy(max_attempts=3, initial_delay_seconds=0.0)


def test_escalation_template_validation() -> None:
    # Valid
    EscalationStrategy(
        queue_name="q",
        notification_level="info",
        timeout_seconds=60,
        template="Error in {{ node_id }}: {{ message }}",
    )

    # Invalid var
    with pytest.raises(ValidationError, match="unauthorized root variable"):
        EscalationStrategy(
            queue_name="q",
            notification_level="info",
            timeout_seconds=60,
            template="Error: {{ secret_env }}",
        )

    # None template (should pass)
    EscalationStrategy(
        queue_name="q",
        notification_level="info",
        timeout_seconds=60,
        template=None,
    )


def test_infinite_reflexion() -> None:
    # Should pass
    rs = ReflexionStrategy(max_attempts="infinite", critic_model="gpt-4", critic_prompt="fix it", include_trace=False)
    assert rs.max_attempts == "infinite"

    # Should fail
    with pytest.raises(ValidationError):
        ReflexionStrategy(max_attempts=-1, critic_model="gpt-4", critic_prompt="fix it")


def test_infinite_governance() -> None:
    # Should pass
    g = Governance(rate_limit_rpm="infinite", timeout_seconds="infinite")
    assert g.rate_limit_rpm == "infinite"
    assert g.timeout_seconds == "infinite"

    # Should fail
    with pytest.raises(ValidationError):
        Governance(rate_limit_rpm=-1)

    with pytest.raises(ValidationError):
        Governance(timeout_seconds=-1)


def test_circuit_breaker_limits() -> None:
    # Should pass
    CircuitBreaker(error_threshold_count=5, reset_timeout_seconds=60)

    # Should fail
    with pytest.raises(ValidationError):
        CircuitBreaker(error_threshold_count=-1, reset_timeout_seconds=60)

    with pytest.raises(ValidationError):
        CircuitBreaker(error_threshold_count=5, reset_timeout_seconds=-1)


def test_supervision_infinite_global() -> None:
    # Should pass: Infinite global limit allows infinite child
    strategy = RetryStrategy(max_attempts="infinite")
    handler = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=strategy)
    policy = SupervisionPolicy(handlers=[handler], max_cumulative_actions="infinite")
    assert policy.max_cumulative_actions == "infinite"


def test_supervision_finite_global_infinite_child() -> None:
    # Should fail: Finite global limit cannot contain infinite child
    strategy = RetryStrategy(max_attempts="infinite")
    handler = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=strategy)

    with pytest.raises(ValueError, match="contains a child strategy with 'infinite' retries"):
        SupervisionPolicy(handlers=[handler], max_cumulative_actions=10)


def test_supervision_finite_global_finite_child() -> None:
    # Should pass: Finite child <= Finite global
    strategy = RetryStrategy(max_attempts=5)
    handler = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=strategy)
    policy = SupervisionPolicy(handlers=[handler], max_cumulative_actions=10)
    assert policy.max_cumulative_actions == 10


def test_supervision_finite_global_exceeding_child() -> None:
    # Should fail: Finite child > Finite global
    strategy = RetryStrategy(max_attempts=15)
    handler = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=strategy)

    with pytest.raises(ValueError, match="is lower than a strategy limit"):
        SupervisionPolicy(handlers=[handler], max_cumulative_actions=10)


def test_supervision_default_strategy_check() -> None:
    # Check that default_strategy is also validated
    strategy = RetryStrategy(max_attempts="infinite")
    # No handlers, but default strategy is infinite

    # Infinite global -> OK
    SupervisionPolicy(handlers=[], default_strategy=strategy, max_cumulative_actions="infinite")

    # Finite global -> Fail
    with pytest.raises(ValueError, match="contains a child strategy with 'infinite' retries"):
        SupervisionPolicy(handlers=[], default_strategy=strategy, max_cumulative_actions=10)


def test_governance_resolvers() -> None:
    # Test resolve_timeout
    g1 = Governance(timeout_seconds=600)
    assert g1.resolve_timeout() == 600

    g2 = Governance(timeout_seconds=None)
    assert g2.resolve_timeout(default_env_timeout=999) == 999

    g3 = Governance(timeout_seconds="infinite")
    assert g3.resolve_timeout() == "infinite"

    # Test resolve_cost_limit
    g4 = Governance(cost_limit_usd=50.0)
    assert g4.resolve_cost_limit() == 50.0

    g5 = Governance(cost_limit_usd=None)
    assert g5.resolve_cost_limit(default_env_cost=100.0) == 100.0

    g6 = Governance(cost_limit_usd="infinite")
    assert g6.resolve_cost_limit() == "infinite"

    # Test resolve_rate_limit
    g7 = Governance(rate_limit_rpm=120)
    assert g7.resolve_rate_limit() == 120

    g8 = Governance(rate_limit_rpm=None)
    assert g8.resolve_rate_limit(default_env_rpm=60) == 60

    g9 = Governance(rate_limit_rpm="infinite")
    assert g9.resolve_rate_limit() == "infinite"


def test_escalation_template_filters() -> None:
    # Should pass with filters
    EscalationStrategy(
        queue_name="q",
        notification_level="info",
        timeout_seconds=60,
        template="Error: {{ message | upper }} in {{ node_id }}",
    )

    # Should fail with unauthorized root var
    with pytest.raises(ValidationError, match="unauthorized root variable"):
        EscalationStrategy(
            queue_name="q",
            notification_level="info",
            timeout_seconds=60,
            template="{{ bad_var | lower }}",
        )
