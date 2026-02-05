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
from pydantic import TypeAdapter

from coreason_manifest import (
    AnyPresentationEvent,
    ErrorDomain,
    PresentationEventType,
    UserErrorEvent,
)


def test_error_domain_serialization() -> None:
    """Verify ErrorDomain serializes correctly."""
    assert ErrorDomain.CLIENT == "client"
    assert ErrorDomain.SYSTEM == "system"
    assert ErrorDomain.LLM == "llm"
    assert ErrorDomain.TOOL == "tool"
    assert ErrorDomain.SECURITY == "security"

    # Test serialization via Pydantic model implicitly (UserErrorEvent uses it)
    event = UserErrorEvent(
        message="Model failed",
        domain=ErrorDomain.LLM,
    )
    dumped = event.model_dump(mode='json')
    assert dumped["domain"] == "llm"


def test_user_error_event_parsing() -> None:
    """Verify parsing a dict into UserErrorEvent."""
    payload = {
        "type": "user_error",
        "message": "Rate limit exceeded",
        "code": 429,
        "retryable": True,
        "domain": "client",
    }

    event = UserErrorEvent.model_validate(payload)

    assert event.type == PresentationEventType.USER_ERROR
    assert event.message == "Rate limit exceeded"
    assert event.code == 429
    assert event.retryable is True
    assert event.domain == ErrorDomain.CLIENT


def test_user_error_event_defaults() -> None:
    """Verify default values for UserErrorEvent."""
    event = UserErrorEvent(message="Something went wrong")

    assert event.domain == ErrorDomain.SYSTEM
    assert event.retryable is False
    assert event.code is None


def test_any_presentation_event_union() -> None:
    """Verify AnyPresentationEvent can parse a UserErrorEvent."""
    payload = {
        "type": "user_error",
        "message": "Forbidden",
        "code": 403,
        "domain": "security",
    }

    adapter = TypeAdapter(AnyPresentationEvent)
    event = adapter.validate_python(payload)

    assert isinstance(event, UserErrorEvent)
    assert event.domain == ErrorDomain.SECURITY
    assert event.code == 403
