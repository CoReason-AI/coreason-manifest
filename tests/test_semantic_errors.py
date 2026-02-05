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
    ErrorDomain,
    MarkdownBlock,
    PresentationEvent,
    PresentationEventType,
)


def test_error_domain_serialization() -> None:
    """Verify ErrorDomain serializes correctly."""
    assert ErrorDomain.CLIENT.value == "client"
    assert ErrorDomain.SYSTEM.value == "system"
    assert ErrorDomain.LLM.value == "llm"
    assert ErrorDomain.TOOL.value == "tool"
    assert ErrorDomain.SECURITY.value == "security"


def test_user_error_event_parsing() -> None:
    """Verify parsing a dict into PresentationEvent (UserError)."""
    payload = {
        "type": "user_error",
        "data": {
            "message": "Rate limit exceeded",
            "code": 429,
            "retryable": True,
            "domain": "client",
        }
    }

    event = PresentationEvent.model_validate(payload)

    assert event.type == PresentationEventType.USER_ERROR
    assert isinstance(event.data, dict)
    assert event.data["message"] == "Rate limit exceeded"
    assert event.data["code"] == 429
    assert event.data["retryable"] is True
    assert event.data["domain"] == "client"


def test_presentation_event_union() -> None:
    """Verify PresentationEvent can parse a user error dict."""
    payload = {
        "type": "user_error",
        "data": {
            "message": "Forbidden",
            "code": 403,
            "domain": "security",
        }
    }

    event = PresentationEvent.model_validate(payload)

    assert event.type == PresentationEventType.USER_ERROR
    assert isinstance(event.data, dict)
    assert event.data["domain"] == "security"
    assert event.data["code"] == 403


def test_complex_polymorphism_structure() -> None:
    """Verify list of PresentationEvents."""
    events_data = [
        {
            "type": "user_error",
            "data": {"message": "Error 1"}
        },
        {
            "type": "markdown_block",
            "data": {"content": "Some text"}
        },
    ]

    adapter: TypeAdapter[list[PresentationEvent]] = TypeAdapter(list[PresentationEvent])
    loaded = adapter.validate_python(events_data)

    assert len(loaded) == 2
    assert loaded[0].type == PresentationEventType.USER_ERROR
    assert loaded[1].type == PresentationEventType.MARKDOWN_BLOCK

    # Check data access with type narrowing
    assert isinstance(loaded[0].data, dict)
    assert loaded[0].data["message"] == "Error 1"

    assert isinstance(loaded[1].data, MarkdownBlock)
    assert loaded[1].data.content == "Some text"  # MarkdownBlock model

    dumped = adapter.dump_python(loaded, mode="json")
    assert dumped[0]["type"] == "user_error"
    assert dumped[1]["type"] == "markdown_block"
