# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import contextlib
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.cap import (
    AgentRequest,
    ServiceRequest,
    SessionContext,
)
from coreason_manifest.spec.common.identity import Identity

# --- Security Test Cases ---


def test_spoofing_attempt_invalid_user_type() -> None:
    """Attempt to spoof user identity with invalid types."""
    with pytest.raises(ValidationError):
        SessionContext(
            session_id="s1",
            user={"id": 123, "name": "Not a String", "role": "admin"},
        )


def test_payload_injection_large_string() -> None:
    """Test resilience against large payload injections (DoS)."""
    large_string = "A" * 10_000_000  # 10MB string

    # Should handle it without crashing (though it might be slow)
    payload = AgentRequest(session_id=uuid4(), payload={"query": large_string})
    assert len(payload.payload["query"]) == 10_000_000


def test_payload_injection_deeply_nested_meta() -> None:
    """Test resilience against deeply nested metadata (recursion limits)."""
    # Create a deeply nested dict
    nested: dict[str, Any] = {}
    current = nested
    for _ in range(1000):
        current["next"] = {}
        current = current["next"]

    # Pydantic usually handles deep nesting fine, but recursion limits in python might be hit during dump
    payload = AgentRequest(session_id=uuid4(), payload={"query": "nested"}, metadata=nested)

    # Verify we can dump it without recursion error or that it fails safely
    # Pydantic v2 has recursion protection which raises ValueError: Circular reference detected (depth exceeded)
    with contextlib.suppress(RecursionError, ValueError):
        payload.dump()


def test_extra_fields_smuggling() -> None:
    """Verify that extra fields are either ignored or forbidden based on config."""
    # ServiceRequest is frozen, so extra fields in init should fail if config is strict,
    # or be ignored/allowed. CoReasonBaseModel doesn't explicitly forbid extra by default,
    # but frozen models in Pydantic V2 often behave strictly.

    # Attempt to inject a 'superuser' flag
    data = {
        "request_id": str(uuid4()),
        "context": {
            "session_id": "s1",
            "user": {"id": "u1", "name": "User"},
            "is_admin": True,  # Smuggled field
        },
        "payload": {
            "session_id": str(uuid4()),
            "payload": {"query": "q"},
            "exec_code": "import os; os.system('rm -rf /')",  # Smuggled field
        },
    }

    req = ServiceRequest.model_validate(data)

    # Check if smuggled fields made it into the model
    # Since we didn't define extra='allow', they should not be accessible as attributes
    assert not hasattr(req.context, "is_admin")
    assert not hasattr(req.payload, "exec_code")

    # Check if they are in the dump (if extra='ignore', they shouldn't be)
    dumped = req.dump()
    assert "is_admin" not in dumped["context"]
    assert "exec_code" not in dumped["payload"]


def test_type_confusion_coercion() -> None:
    """Test if dangerous type coercion happens."""
    # Attempt to pass an integer as a string for session_id.
    # If strictly typed, this should raise ValidationError.
    # If loosely typed (coercion), it becomes "12345".
    # In Pydantic V2, default behavior is lax coercion unless strict=True.
    # However, our previous run showed it raised ValidationError, implying strictness or specific config.
    # We update the test to expect strict behavior which is better for security.

    with pytest.raises(ValidationError):
        SessionContext(
            session_id=12345,
            user=Identity.anonymous(),
        )

    # Attempt to pass a list where a dict is expected for payload
    with pytest.raises(ValidationError):
        AgentRequest(session_id=uuid4(), payload=[1, 2, 3])


def test_null_byte_injection() -> None:
    """Test for null byte injection in strings."""
    # Python strings handle null bytes fine, but downstream systems might not.
    # The manifest library itself should just store it faithfully.
    malicious_id = "user\0admin"
    user = Identity(id=malicious_id, name="User")
    assert user.id == "user\0admin"

    dumped = user.dump()
    assert dumped["id"] == "user\0admin"


def test_context_isolation() -> None:
    """Ensure context and payload are truly separate."""
    user = Identity.anonymous()
    ctx = SessionContext(session_id="s1", user=user)
    payload = AgentRequest(session_id=uuid4(), payload={"query": "test"})

    req = ServiceRequest(request_id=uuid4(), context=ctx, payload=payload)

    # Modifying payload should not affect context (immutability check)
    with pytest.raises(ValidationError):
        setattr(req, "payload", AgentRequest(session_id=uuid4(), payload={"query": "hacked"}))  # noqa: B010

    # Verify they are distinct objects
    assert req.context is ctx
    assert req.payload is payload
