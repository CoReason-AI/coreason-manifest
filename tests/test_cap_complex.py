# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest

from coreason_manifest.spec.cap import (
    ErrorSeverity,
    StreamError,
    StreamOpCode,
    StreamPacket,
)


def test_close_op_payload() -> None:
    """Test CLOSE op behavior. It allows None payload."""
    packet = StreamPacket(op=StreamOpCode.CLOSE, p=None)
    assert packet.op == StreamOpCode.CLOSE
    assert packet.p is None

    # Verify it dumps correctly
    dumped = packet.dump()
    assert dumped["op"] == "close"
    # CoReasonBaseModel.dump() excludes None fields by default
    assert "p" not in dumped


def test_event_op_complex_payload() -> None:
    """Test EVENT op with nested dictionary payload."""
    complex_payload = {
        "type": "tool_call",
        "tool": "calculator",
        "inputs": {"expression": "2 + 2"},
        "metadata": {"timestamp": 1234567890, "source": "agent_v1"},
    }
    packet = StreamPacket(op=StreamOpCode.EVENT, p=complex_payload)
    assert packet.op == StreamOpCode.EVENT
    assert isinstance(packet.p, dict)
    assert packet.p["type"] == "tool_call"
    assert packet.p["inputs"]["expression"] == "2 + 2"


def test_error_coercion_failure_missing_fields() -> None:
    """Test that dictionary coercion to StreamError fails if required fields are missing."""
    # "code" and "message" and "severity" are required.
    invalid_payload = {
        "code": "oops",
        # missing message and severity
    }

    # op=ERROR expects StreamError. Pydantic will try to coerce `p` to StreamError.
    # Since it fails validation (missing fields), and `p` allows Dict, does it fall back to Dict?
    # NO. The validator I wrote `validate_structure` strictly checks:
    # "if self.op == StreamOpCode.ERROR: if not isinstance(self.p, StreamError): raise ValueError..."
    #
    # However, Pydantic's Union parsing happens BEFORE my validator.
    # `p` is Union[StreamError, str, Dict, None].
    # `left_to_right` mode means:
    # 1. Try StreamError. `invalid_payload` fails StreamError validation.
    # 2. Try str. Fails.
    # 3. Try Dict. SUCCEEDS.
    # So `self.p` becomes a Dict.
    #
    # THEN `validate_structure` runs.
    # It checks `isinstance(self.p, StreamError)`. It is a Dict.
    # So it raises ValueError.

    with pytest.raises(ValueError, match="Payload 'p' must be a valid StreamError when op is ERROR"):
        StreamPacket(op=StreamOpCode.ERROR, p=invalid_payload)


def test_round_trip_serialization() -> None:
    """Test full JSON round-trip for various packet types."""

    # 1. Delta
    p1 = StreamPacket(op=StreamOpCode.DELTA, p="chunk")
    p1_json = p1.model_dump_json()
    p1_restored = StreamPacket.model_validate_json(p1_json)
    assert p1_restored == p1

    # 2. Error
    error = StreamError(code="e1", message="m1", severity=ErrorSeverity.FATAL)
    p2 = StreamPacket(op=StreamOpCode.ERROR, p=error)
    p2_json = p2.model_dump_json()
    p2_restored = StreamPacket.model_validate_json(p2_json)
    assert p2_restored == p2
    assert isinstance(p2_restored.p, StreamError)

    # 3. Event
    p3 = StreamPacket(op=StreamOpCode.EVENT, p={"k": "v"})
    p3_json = p3.model_dump_json()
    p3_restored = StreamPacket.model_validate_json(p3_json)
    assert p3_restored == p3


def test_ambiguous_payload_coercion() -> None:
    """Test what happens when a Dict payload LOOKS like a StreamError but op is EVENT."""
    # It matches StreamError structure exactly.
    payload = {"code": "fake_error", "message": "not actually an error op", "severity": "transient"}

    # op=EVENT.
    # Union is `StreamError | str | Dict | None`.
    # Pydantic (left_to_right) will match StreamError FIRST because it fits the schema.
    # So `p` will be parsed as a `StreamError` object.
    packet = StreamPacket(op=StreamOpCode.EVENT, p=payload)

    # Is this desired?
    # The requirement said "IF op is ERROR: payload MUST be StreamError".
    # It didn't strictly say "IF op is EVENT: payload MUST NOT be StreamError".
    # However, having an EVENT with a StreamError payload is... odd but technically valid types.
    # The validator only checks ERROR and DELTA.
    #
    # Let's verify what it actually is.
    assert isinstance(packet.p, StreamError)

    # If we want to FORCE it to be a dict, we'd need to ensure it doesn't match StreamError schema,
    # or rely on the user passing a generic dict that doesn't match.
    # But strictly speaking, if it quacks like a StreamError, it becomes one in the model.
    #
    # Test that we can use it as a dict if we cast it back? No, it's a model.
    # This test documents the behavior: "Greedy matching of StreamError in Union".


def test_stream_error_details_nested() -> None:
    """Test StreamError with complex nested details."""
    details = {"trace": ["a", "b", "c"], "meta": {"foo": {"bar": 123}}, "timestamp": "2023-01-01"}
    error = StreamError(code="c", message="m", severity=ErrorSeverity.TRANSIENT, details=details)
    packet = StreamPacket(op=StreamOpCode.ERROR, p=error)

    assert isinstance(packet.p, StreamError)
    assert packet.p.details is not None
    assert packet.p.details["meta"]["foo"]["bar"] == 123


def test_large_payload() -> None:
    """Test a large string payload for DELTA."""
    large_str = "a" * 10_000
    packet = StreamPacket(op=StreamOpCode.DELTA, p=large_str)
    assert isinstance(packet.p, str)
    assert len(packet.p) == 10_000
