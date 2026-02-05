# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pydantic import TypeAdapter

from coreason_manifest import (
    CitationBlock,
    CitationItem,
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

    # Test serialization via PresentationEvent
    event = PresentationEvent(
        type=PresentationEventType.USER_ERROR,
        data={
            "message": "Model failed",
            "domain": ErrorDomain.LLM,
        },
    )
    dumped = event.model_dump(mode="json")
    assert dumped["data"]["domain"] == "llm"


def test_user_error_event_parsing() -> None:
    """Verify parsing a dict into PresentationEvent (UserError)."""
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
    assert event.data["message"] == "Rate limit exceeded"
    assert event.data["code"] == 429
    assert event.data["retryable"] is True
    assert event.data["domain"] == "client"


def test_edge_case_empty_strings() -> None:
    """Verify empty message strings are handled."""
    event = PresentationEvent(
        type=PresentationEventType.USER_ERROR,
        data={"message": "", "domain": ErrorDomain.SYSTEM},
    )
    assert event.data["message"] == ""
    dumped = event.model_dump(mode="json")
    assert dumped["data"]["message"] == ""


def test_edge_case_numeric_limits() -> None:
    """Verify large/negative codes."""
    # Negative code
    event = PresentationEvent(
        type=PresentationEventType.USER_ERROR,
        data={"message": "Negative", "code": -1},
    )
    assert event.data["code"] == -1

    # Large code
    event = PresentationEvent(
        type=PresentationEventType.USER_ERROR,
        data={"message": "Large", "code": 999999},
    )
    assert event.data["code"] == 999999


def test_complex_polymorphism_structure() -> None:
    """Verify nested unions and serialization."""
    events: list[PresentationEvent] = [
        PresentationEvent(type=PresentationEventType.USER_ERROR, data={"message": "Error 1"}),
        PresentationEvent(
            type=PresentationEventType.CITATION_BLOCK,
            data=CitationBlock(items=[CitationItem(source_id="s1", uri="http://example.com", title="Quote")]),
        ),
        PresentationEvent(
            type=PresentationEventType.USER_ERROR,
            data={"message": "Error 2", "code": 500},
        ),
    ]

    adapter: TypeAdapter[list[PresentationEvent]] = TypeAdapter(list[PresentationEvent])
    dumped = adapter.dump_python(events, mode="json")

    assert len(dumped) == 3
    assert dumped[0]["type"] == "user_error"
    assert dumped[1]["type"] == "citation_block"
    assert dumped[2]["type"] == "user_error"

    # Round trip
    loaded = adapter.validate_python(dumped)
    assert loaded[0].type == PresentationEventType.USER_ERROR
    assert loaded[1].type == PresentationEventType.CITATION_BLOCK
    assert isinstance(loaded[1].data, CitationBlock)
    assert loaded[2].type == PresentationEventType.USER_ERROR
