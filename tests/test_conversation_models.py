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
from pydantic import ValidationError, AnyUrl

from coreason_manifest import (
    ChatMessage,
    PresentationEvent,
    PresentationEventType,
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    Role,
)


def test_chat_message_serialization() -> None:
    """Test ChatMessage serialization with standard ISO timestamp."""
    msg = ChatMessage(role=Role.USER, content="Hello")
    dumped = msg.dump()

    assert dumped["role"] == "user"
    assert dumped["content"] == "Hello"
    assert "name" not in dumped
    assert "timestamp" in dumped
    # CoReasonBaseModel serializes datetime with Z suffix
    assert dumped["timestamp"].endswith("Z")


def test_role_validation() -> None:
    """Test Role validation rejects invalid roles."""
    with pytest.raises(ValidationError):
        ChatMessage(role="moderator", content="Hello")


def test_presentation_polymorphism() -> None:
    """Test polymorphism for presentation events."""
    events = [
        PresentationEvent(
            type=PresentationEventType.CITATION_BLOCK,
            data=CitationBlock(items=[
                CitationItem(source_id="1", uri=AnyUrl("https://example.com"), title="Example", snippet="Example")
            ])
        ),
        PresentationEvent(
            type=PresentationEventType.MEDIA_CAROUSEL,
            data=MediaCarousel(items=[
                MediaItem(url=AnyUrl("https://example.com/img"), mime_type="image/png")
            ])
        ),
    ]

    assert events[0].type == PresentationEventType.CITATION_BLOCK
    assert events[1].type == PresentationEventType.MEDIA_CAROUSEL

    dumped_citation = events[0].dump()
    dumped_artifact = events[1].dump()

    assert dumped_citation["type"] == "citation_block"
    assert dumped_artifact["type"] == "media_carousel"


def test_immutability() -> None:
    """Test that models are immutable."""
    msg = ChatMessage(role=Role.USER, content="Hello")
    with pytest.raises(ValidationError):
        setattr(msg, "content", "New")  # noqa: B010

    # Presentation event immutability
    event = PresentationEvent(
        type=PresentationEventType.MARKDOWN_BLOCK,
        data={"content": "foo"}
    )
    with pytest.raises(ValidationError):
        setattr(event, "type", PresentationEventType.USER_ERROR)  # noqa: B010
