from datetime import datetime
import json
import uuid
from coreason_manifest.definitions.message import Message, Role, ToolCall, FunctionCall
from coreason_manifest.definitions.audit import ReasoningTrace, AuditLog, CognitiveStep, TokenUsage

def test_message_creation() -> None:
    """Test creating various types of messages."""
    # User message
    user_msg = Message(role=Role.USER, content="Hello")
    assert user_msg.role == "user"
    assert user_msg.content == "Hello"

    # Tool call message
    tool_call = ToolCall(
        id="call_123",
        function=FunctionCall(name="get_weather", arguments='{"city": "Paris"}')
    )
    assistant_msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])
    assert assistant_msg.tool_calls
    assert assistant_msg.tool_calls[0].function.name == "get_weather"

def test_reasoning_trace_creation() -> None:
    """Test creating a full reasoning trace."""
    trace_id = uuid.uuid4()

    # Input
    input_msg = Message(role=Role.USER, content="Calculate 2+2")

    # Output
    tool_call = ToolCall(
        id="call_math",
        function=FunctionCall(name="calculator", arguments='{"expression": "2+2"}')
    )
    output_msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])

    step = CognitiveStep(
        step_id="step_1",
        input_messages=[input_msg],
        output_message=output_msg,
        tool_calls=[tool_call],
        token_usage=TokenUsage(total_tokens=10)
    )

    trace = ReasoningTrace(
        trace_id=trace_id,
        agent_id="agent_v1",
        start_time=datetime.now(),
        steps=[step],
        status="success"
    )

    assert trace.trace_id == trace_id
    assert len(trace.steps) == 1
    assert trace.steps[0].step_id == "step_1"
    assert trace.steps[0].token_usage is not None
    assert trace.steps[0].token_usage.total_tokens == 10

def test_audit_log_alias() -> None:
    """Verify that AuditLog is an alias for ReasoningTrace."""
    assert AuditLog is ReasoningTrace

    # Instantiate using AuditLog
    log = AuditLog(
        trace_id=uuid.uuid4(),
        agent_id="test_agent",
        start_time=datetime.now()
    )
    assert isinstance(log, ReasoningTrace)

def test_serialization() -> None:
    """Test JSON serialization of the trace."""
    trace = ReasoningTrace(
        trace_id=uuid.uuid4(),
        agent_id="agent_json",
        start_time=datetime.now(),
        steps=[]
    )

    json_str = trace.model_dump_json()
    data = json.loads(json_str)
    assert data["agent_id"] == "agent_json"
    assert "start_time" in data
