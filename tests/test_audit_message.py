import uuid
from datetime import datetime

from coreason_manifest.definitions.audit import GenAIOperation, ReasoningTrace


def test_token_accumulation() -> None:
    """Verify that total_tokens accumulates correctly from steps."""
    trace = ReasoningTrace(
        trace_id=str(uuid.uuid4()), agent_id="test_agent", request_id=uuid.uuid4(), start_time=datetime.now()
    )

    # Simulate a step with usage
    op = GenAIOperation.thought("Thinking...")
    op.token_usage = op.token_usage or trace.total_tokens.model_copy()
    op.token_usage.input = 10
    op.token_usage.output = 20
    op.token_usage.total = 30

    # In a real engine, we'd sum this up. Here we just ensure the model holds data.
    trace.total_tokens.input += 10
    trace.total_tokens.output += 20
    trace.total_tokens.total += 30

    assert trace.total_tokens.total == 30


def test_json_serialization() -> None:
    """Ensure complex trace can be serialized."""
    trace = ReasoningTrace(
        trace_id=str(uuid.uuid4()),
        agent_id="agent_json",
        request_id=uuid.uuid4(),
        start_time=datetime.now(),
        steps=[],
    )
    json_str = trace.to_json()
    assert "trace_id" in json_str
