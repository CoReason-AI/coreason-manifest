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
from pydantic import TypeAdapter, ValidationError

from coreason_manifest import (
    AnyPresentationEvent,
    CitationEvent,
    ErrorDomain,
    PresentationEventType,
    UserErrorEvent,
)


def test_error_domain_serialization() -> None:
    """Verify ErrorDomain serializes correctly."""
    assert ErrorDomain.CLIENT.value == "client"
    assert ErrorDomain.SYSTEM.value == "system"
    assert ErrorDomain.LLM.value == "llm"
    assert ErrorDomain.TOOL.value == "tool"
    assert ErrorDomain.SECURITY.value == "security"

    # Test serialization via Pydantic model implicitly (UserErrorEvent uses it)
    event = UserErrorEvent(
        message="Model failed",
        domain=ErrorDomain.LLM,
    )
    dumped = event.model_dump(mode="json")
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

    adapter: TypeAdapter[AnyPresentationEvent] = TypeAdapter(AnyPresentationEvent)
    event = adapter.validate_python(payload)

    assert isinstance(event, UserErrorEvent)
    assert event.domain == ErrorDomain.SECURITY
    assert event.code == 403


def test_edge_case_empty_strings() -> None:
    """Verify empty message strings are handled."""
    event = UserErrorEvent(message="", domain=ErrorDomain.SYSTEM)
    assert event.message == ""
    dumped = event.model_dump(mode="json")
    assert dumped["message"] == ""


def test_edge_case_numeric_limits() -> None:
    """Verify large/negative codes."""
    # Negative code
    event = UserErrorEvent(message="Negative", code=-1)
    assert event.code == -1

    # Large code
    event = UserErrorEvent(message="Large", code=999999)
    assert event.code == 999999


def test_complex_polymorphism_structure() -> None:
    """Verify nested unions and serialization."""
    events: list[AnyPresentationEvent] = [
        UserErrorEvent(message="Error 1"),
        CitationEvent(uri="http://example.com", text="Quote"),
        UserErrorEvent(message="Error 2", code=500),
    ]

    adapter: TypeAdapter[list[AnyPresentationEvent]] = TypeAdapter(list[AnyPresentationEvent])
    dumped = adapter.dump_python(events, mode="json")

    assert len(dumped) == 3
    assert dumped[0]["type"] == "user_error"
    assert dumped[1]["type"] == "citation"
    assert dumped[2]["type"] == "user_error"

    # Round trip
    loaded = adapter.validate_python(dumped)
    assert isinstance(loaded[0], UserErrorEvent)
    assert isinstance(loaded[1], CitationEvent)
    assert isinstance(loaded[2], UserErrorEvent)


def test_redundant_validation_scenarios() -> None:
    """Verify validation failures."""
    # Missing required field 'message'
    with pytest.raises(ValidationError):
        UserErrorEvent.model_validate({"type": "user_error"})

    # Invalid domain string
    with pytest.raises(ValidationError):
        UserErrorEvent.model_validate(
            {
                "type": "user_error",
                "message": "Fail",
                "domain": "invalid_domain",
            }
        )
