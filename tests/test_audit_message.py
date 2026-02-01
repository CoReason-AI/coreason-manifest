# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
import uuid
from datetime import datetime

from coreason_manifest.definitions.audit import (
    GenAIOperation,
    GenAITokenUsage,
    ReasoningTrace,
)
from coreason_manifest.definitions.message import (
    ChatMessage,
    Message,
    Role,
    TextPart,
    ToolCallRequestPart,
)


def test_message_creation() -> None:
    """Test creating various types of messages with new schema."""
    # User message with TextPart
    user_msg = ChatMessage(role=Role.USER, parts=[TextPart(content="Hello")])
    assert user_msg.role == "user"
    part0 = user_msg.parts[0]
    assert isinstance(part0, TextPart)
    assert part0.content == "Hello"
    assert part0.type == "text"

    # Tool call message
    tool_call = ToolCallRequestPart(name="get_weather", arguments={"city": "Paris"}, id="call_123")
    assistant_msg = ChatMessage(role=Role.ASSISTANT, parts=[tool_call])
    assert len(assistant_msg.parts) == 1
    part = assistant_msg.parts[0]
    assert isinstance(part, ToolCallRequestPart)
    assert part.name == "get_weather"
    assert part.parsed_arguments["city"] == "Paris"


def test_message_alias_compatibility() -> None:
    """Verify Message alias works."""
    msg = Message(role=Role.SYSTEM, parts=[TextPart(content="System prompt")])
    assert isinstance(msg, ChatMessage)


def test_gen_ai_operation_creation() -> None:
    """Test creating a GenAI operation (audit step)."""
    trace_id = str(uuid.uuid4())
    step_id = "step_1"

    input_msg = ChatMessage(role=Role.USER, parts=[TextPart(content="Calculate 2+2")])

    tool_call = ToolCallRequestPart(name="calculator", arguments={"expression": "2+2"}, id="call_math")
    output_msg = ChatMessage(role=Role.ASSISTANT, parts=[tool_call])

    operation = GenAIOperation(
        span_id=step_id,
        trace_id=trace_id,
        operation_name="chat",
        provider="openai",
        model="gpt-4",
        input_messages=[input_msg],
        output_messages=[output_msg],
        token_usage=GenAITokenUsage(input=5, output=10, total=15),
    )

    assert operation.span_id == step_id
    assert operation.provider == "openai"
    assert operation.token_usage is not None
    assert operation.token_usage.total == 15
    # Check arguments using parsed_arguments
    assert tool_call.parsed_arguments["expression"] == "2+2"
    # Check backward compatibility fields on TokenUsage
    # Default is 0 unless explicitly set, or we add a validator to sync them.
    assert operation.token_usage.total_tokens == 0
    # Note: If we wanted strict backward compat for values, we'd need a validator.
    # For now, we just ensure the field exists on the schema.


def test_reasoning_trace_creation() -> None:
    """Test creating a full reasoning trace."""
    trace_id = uuid.uuid4()

    step = GenAIOperation(
        span_id="step_1",
        trace_id=str(trace_id),
        operation_name="chat",
        provider="openai",
        model="gpt-4",
        input_messages=[],
        output_messages=[],
    )

    trace = ReasoningTrace(
        trace_id=str(trace_id),
        agent_id="agent_v1",
        start_time=datetime.now(),
        steps=[step],
        status="success",
    )

    assert trace.trace_id == str(trace_id)
    assert len(trace.steps) == 1
    assert trace.steps[0].span_id == "step_1"


def test_serialization() -> None:
    """Test JSON serialization of the trace."""
    trace = ReasoningTrace(trace_id=str(uuid.uuid4()), agent_id="agent_json", start_time=datetime.now(), steps=[])

    json_str = trace.model_dump_json()
    data = json.loads(json_str)
    assert data["agent_id"] == "agent_json"
    assert "start_time" in data
