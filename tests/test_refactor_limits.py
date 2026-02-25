import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
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
