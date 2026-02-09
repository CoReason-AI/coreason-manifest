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

from coreason_manifest import (
    ChatMessage,
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
    Role,
)


def test_chat_message_serialization() -> None:
    """Test ChatMessage serialization with standard ISO timestamp."""
    msg = ChatMessage(role=Role.USER, content="Hello")
    dumped = msg.model_dump(mode='json', by_alias=True, exclude_none=True)

    assert dumped["role"] == "user"
    assert dumped["content"] == "Hello"
    assert "name" not in dumped
    assert "timestamp" in dumped
    # ManifestBaseModel serializes datetime with Z suffix
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
            data=CitationBlock(
                items=[
                    CitationItem(
                        source_id="s1",
                        uri="https://example.com",
                        title="Example",
                    )
                ]
            ),
        ),
        PresentationEvent(
            type=PresentationEventType.MEDIA_CAROUSEL,
            data=MediaCarousel(items=[MediaItem(url="https://art.com/1", mime_type="text/csv")]),
        ),
    ]

    assert events[0].type == PresentationEventType.CITATION_BLOCK
    assert events[1].type == PresentationEventType.MEDIA_CAROUSEL

    dumped_citation = events[0].model_dump(mode='json', by_alias=True, exclude_none=True)
    dumped_artifact = events[1].model_dump(mode='json', by_alias=True, exclude_none=True)

    assert dumped_citation["type"] == "citation_block"
    assert dumped_artifact["type"] == "media_carousel"


def test_immutability() -> None:
    """Test that models are immutable."""
    msg = ChatMessage(role=Role.USER, content="Hello")
    with pytest.raises(ValidationError):
        setattr(msg, "content", "New")  # noqa: B010

    event = PresentationEvent(
        type=PresentationEventType.CITATION_BLOCK,
        data=CitationBlock(items=[CitationItem(source_id="s1", uri="http://a.com", title="b")]),
    )
    with pytest.raises(ValidationError):
        setattr(event, "type", PresentationEventType.USER_ERROR)  # noqa: B010
