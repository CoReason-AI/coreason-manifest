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
from pydantic import ValidationError

from coreason_manifest.spec.cap import (
    ErrorSeverity,
    StreamError,
    StreamOpCode,
    StreamPacket,
)


def test_happy_path_error() -> None:
    """Create a StreamPacket with op=ERROR and a valid StreamError object."""
    error = StreamError(
        code="rate_limit_exceeded",
        message="Too many requests",
        severity=ErrorSeverity.TRANSIENT,
        details={"retry_after": 60},
    )
    packet = StreamPacket(op=StreamOpCode.ERROR, p=error)

    dumped = packet.dump()
    assert dumped["op"] == "error"
    assert dumped["p"]["code"] == "rate_limit_exceeded"
    assert dumped["p"]["severity"] == "transient"


def test_happy_path_coercion() -> None:
    """Create a StreamPacket with op=ERROR and a dict payload."""
    payload = {
        "code": "auth_failed",
        "message": "Invalid token",
        "severity": "fatal",
    }
    # This relies on Pydantic coercing dict -> StreamError because StreamError is in the Union
    packet = StreamPacket(op=StreamOpCode.ERROR, p=payload)

    assert isinstance(packet.p, StreamError)
    assert packet.p.code == "auth_failed"
    assert packet.p.severity == ErrorSeverity.FATAL


def test_violation_string_error() -> None:
    """Attempt to create a packet with op=ERROR and p='Simple string error'."""
    with pytest.raises(ValueError) as excinfo:
        StreamPacket(op=StreamOpCode.ERROR, p="Simple string error")

    # The validator raises ValueError
    assert "Payload 'p' must be a valid StreamError when op is ERROR" in str(excinfo.value)


def test_violation_delta_type() -> None:
    """Attempt to create a packet with op=DELTA and p=StreamError(...)."""
    error = StreamError(
        code="oops",
        message="oops",
        severity=ErrorSeverity.TRANSIENT,
    )
    with pytest.raises(ValueError) as excinfo:
        StreamPacket(op=StreamOpCode.DELTA, p=error)

    assert "Payload 'p' must be a string when op is DELTA" in str(excinfo.value)


def test_immutability() -> None:
    """Ensure StreamError cannot be modified after creation."""
    error = StreamError(
        code="oops",
        message="oops",
        severity=ErrorSeverity.TRANSIENT,
    )

    with pytest.raises(ValidationError) as excinfo:
        # Use setattr to bypass static analysis but trigger runtime immutability check
        setattr(error, "code", "new_code")

    assert "Instance is frozen" in str(excinfo.value)
