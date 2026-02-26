import pytest
from coreason_manifest.builder import AgentBuilder, create_resilience
from coreason_manifest.spec.core.resilience import EscalationStrategy, FallbackStrategy, RetryStrategy

def test_create_resilience_retry() -> None:
    res = create_resilience(retries=3, strategy="retry", backoff=1.5, delay=2.0)
    assert isinstance(res, RetryStrategy)
    assert res.max_attempts == 3
    assert res.backoff_factor == 1.5
    assert res.initial_delay_seconds == 2.0

def test_create_resilience_fallback() -> None:
    res = create_resilience(retries=1, strategy="fallback", fallback_id="node_b")
    assert isinstance(res, FallbackStrategy)
    assert res.fallback_node_id == "node_b"

def test_create_resilience_fallback_missing_id() -> None:
    with pytest.raises(ValueError, match="fallback_id is required"):
        create_resilience(retries=1, strategy="fallback")

def test_create_resilience_escalate_default() -> None:
    # default strategy is escalate
    res = create_resilience(retries=1, strategy="unknown", queue_name="my_queue")
    assert isinstance(res, EscalationStrategy)
    assert res.queue_name == "my_queue"

    # default queue name
    res2 = create_resilience(retries=1, strategy="escalate")
    assert isinstance(res2, EscalationStrategy)
    assert res2.queue_name == "default_human_queue"

def test_agent_builder_with_resilience() -> None:
    builder = AgentBuilder("agent1")
    builder.with_identity("role", "persona")
    builder.with_resilience(retries=3, strategy="retry")
    agent = builder.build()
    assert isinstance(agent.resilience, RetryStrategy)
    assert agent.resilience.max_attempts == 3
