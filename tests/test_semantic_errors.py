# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest import (
    ErrorDomain,
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
    """Verify parsing a dict into PresentationEvent with USER_ERROR type."""
    payload = {
        "type": "user_error",
        "data": {
            "message": "Rate limit exceeded",
            "code": 429,
            "retryable": True,
            "domain": "client",
        },
    }

    event = PresentationEvent.model_validate(payload)

    assert event.type == PresentationEventType.USER_ERROR
    assert isinstance(event.data, dict)
    assert event.data["message"] == "Rate limit exceeded"
    assert event.data["code"] == 429
    assert event.data["retryable"] is True
    assert event.data["domain"] == "client"
