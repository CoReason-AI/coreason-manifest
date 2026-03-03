import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.presentation import AdaptiveUIContract
from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp
from coreason_manifest.core.telemetry.stream import (
    PacketContainer,
    StreamCloseEnvelope,
    StreamDeltaEnvelope,
    StreamError,
    StreamErrorEnvelope,
    StreamStateDeltaEnvelope,
    StreamThoughtEnvelope,
    StreamToolCallEnvelope,
    StreamUIEnvelope,
)
from coreason_manifest.core.telemetry.suspense_envelope import StreamSuspenseEnvelope


def test_stream_error_envelope() -> None:
    error = StreamError(code=500, message="Internal Error", severity="high")
    envelope = StreamErrorEnvelope(op="error", p=error, timestamp=12345.6, trace_id="trace1")
    assert envelope.op == "error"
    assert envelope.p.code == 500
    assert envelope.trace_id == "trace1"

    # Test discriminator parsing
    container = PacketContainer.model_validate(
        {
            "packet": {
                "op": "error",
                "p": {"code": 500, "message": "Internal Error", "severity": "high"},
                "timestamp": 12345.6,
            }
        }
    )
    assert isinstance(container.packet, StreamErrorEnvelope)


def test_stream_delta_envelope() -> None:
    envelope = StreamDeltaEnvelope(op="delta", p="hello", timestamp=123.4)
    assert envelope.p == "hello"

    container = PacketContainer.model_validate({"packet": {"op": "delta", "p": "world", "timestamp": 123.4}})
    assert isinstance(container.packet, StreamDeltaEnvelope)


def test_stream_close_envelope() -> None:
    envelope = StreamCloseEnvelope(op="close", p=None, timestamp=123.4)
    assert envelope.p is None

    container = PacketContainer.model_validate({"packet": {"op": "close", "p": None, "timestamp": 123.4}})
    assert isinstance(container.packet, StreamCloseEnvelope)


def test_stream_thought_envelope() -> None:
    envelope = StreamThoughtEnvelope(op="thought", p="I am thinking", timestamp=123.4)
    assert envelope.p == "I am thinking"

    container = PacketContainer.model_validate({"packet": {"op": "thought", "p": "thinking", "timestamp": 123.4}})
    assert isinstance(container.packet, StreamThoughtEnvelope)


def test_stream_tool_call_envelope() -> None:
    envelope = StreamToolCallEnvelope(op="tool_call", p={"name": "test_tool"}, timestamp=123.4)
    assert envelope.p == {"name": "test_tool"}

    container = PacketContainer.model_validate({"packet": {"op": "tool_call", "p": {"arg": 1}, "timestamp": 123.4}})
    assert isinstance(container.packet, StreamToolCallEnvelope)


def test_stream_ui_envelope() -> None:
    from coreason_manifest.core.common.presentation import UIComponentNode

    ui = AdaptiveUIContract(layout=[UIComponentNode(type="LineChart", props={})], fallback_to_text=True)
    envelope = StreamUIEnvelope(op="ui_mount", p=ui, timestamp=123.4)
    assert envelope.p.layout[0].type == "LineChart"

    container = PacketContainer.model_validate(
        {"packet": {"op": "ui_mount", "p": {"layout": [{"type": "LineChart", "props": {}}]}, "timestamp": 123.4}}
    )
    assert isinstance(container.packet, StreamUIEnvelope)


def test_stream_state_delta_envelope() -> None:
    patch = JSONPatchOperation(op=PatchOp.ADD, path="/test", value="test_value", from_=None)
    envelope = StreamStateDeltaEnvelope(op="state_delta", p=[patch], timestamp=123.4)
    assert len(envelope.p) == 1
    assert envelope.p[0].value == "test_value"

    container = PacketContainer.model_validate(
        {
            "packet": {
                "op": "state_delta",
                "p": [{"op": PatchOp.ADD, "path": "/test", "value": "test_value"}],
                "timestamp": 123.4,
            }
        }
    )
    assert isinstance(container.packet, StreamStateDeltaEnvelope)


def test_stream_suspense_envelope() -> None:
    # Just to test StreamSuspenseEnvelope as it's part of the union
    from coreason_manifest.core.common.suspense import SkeletonType

    container = PacketContainer.model_validate(
        {"packet": {"op": "suspense_mount", "p": {"fallback_type": SkeletonType.SPINNER}, "timestamp": 123.4}}
    )
    assert isinstance(container.packet, StreamSuspenseEnvelope)


def test_invalid_packet() -> None:
    with pytest.raises(ValidationError):
        PacketContainer.model_validate({"packet": {"op": "invalid_op", "p": "test", "timestamp": 123.4}})

    with pytest.raises(ValidationError):
        # Missing timestamp
        PacketContainer.model_validate({"packet": {"op": "thought", "p": "thinking"}})

    with pytest.raises(ValidationError):
        # Strict config prevents extra fields
        PacketContainer.model_validate(
            {"packet": {"op": "thought", "p": "thinking", "timestamp": 123.4, "extra_field": "disallowed"}}
        )


def test_base_envelope_strictness() -> None:
    # Test strict parsing of timestamps and trace_id
    with pytest.raises(ValidationError):
        StreamThoughtEnvelope(op="thought", p="thinking", timestamp="not a float")  # type: ignore
