# tests/test_resilience_consolidated.py

import pytest

from coreason_manifest.spec.core.resilience import (
    EscalationStrategy,
    FallbackStrategy,
    ResilienceConfig,
    RetryStrategy,
    SwitchStrategy,
)


def test_resilience_config_union() -> None:
    # Test valid retry configuration
    rc_retry = ResilienceConfig.model_validate({
        "type": "retry",
        "max_attempts": 3,
        "backoff_factor": 2.0,
        "initial_delay_seconds": 1.0
    })
    assert isinstance(rc_retry, RetryStrategy)
    assert rc_retry.max_attempts == 3

    # Test valid fallback configuration
    rc_fallback = ResilienceConfig.model_validate({
        "type": "fallback",
        "fallback_node_id": "backup_agent"
    })
    assert isinstance(rc_fallback, FallbackStrategy)
    assert rc_fallback.fallback_node_id == "backup_agent"

    # Test valid escalation configuration
    rc_escalate = ResilienceConfig.model_validate({
        "type": "escalate",
        "queue_name": "support"
    })
    assert isinstance(rc_escalate, EscalationStrategy)
    assert rc_escalate.queue_name == "support"

    # Test switch strategy
    rc_switch = ResilienceConfig.model_validate({
        "type": "switch",
        "fallback_variable": "next_step",
        "cases": {"fail": "error_handler"}
    })
    assert isinstance(rc_switch, SwitchStrategy)

def test_resilience_defaults() -> None:
    # Test defaults
    retry = RetryStrategy(type="retry")
    assert retry.max_attempts == 3
    assert retry.backoff_factor == 2.0

    escalate = EscalationStrategy(type="escalate")
    assert escalate.queue_name == "default_human_queue"

def test_resilience_validation() -> None:
    # Fallback requires node id
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        FallbackStrategy(type="fallback")

    # Switch requires variable and cases
    with pytest.raises(ValidationError):
        SwitchStrategy(type="switch", fallback_variable="v")
