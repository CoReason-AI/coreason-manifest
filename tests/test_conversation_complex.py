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
from pydantic import TypeAdapter, ValidationError, AnyUrl

from coreason_manifest import (
    ChatMessage,
    PresentationEvent,
    PresentationEventType,
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    Role,
    StreamOpCode,
    StreamPacket,
)


def test_chat_message_edge_cases() -> None:
    """Test ChatMessage with edge cases."""
    # Empty content
    msg = ChatMessage(role=Role.USER, content="")
    assert msg.content == ""

    # Unicode/Emoji
    msg_emoji = ChatMessage(role=Role.ASSISTANT, content="Hello 🌍! 👍")
    assert msg_emoji.content == "Hello 🌍! 👍"
    dumped = msg_emoji.dump()
    assert dumped["content"] == "Hello 🌍! 👍"

    # Very long content
    long_str = "a" * 10000
    msg_long = ChatMessage(role=Role.SYSTEM, content=long_str)
    assert len(msg_long.content) == 10000


def test_role_enum_strictness() -> None:
    """Test that Role enum is strict."""
    # Valid roles
    assert ChatMessage(role=Role.SYSTEM, content="").role == Role.SYSTEM
    assert ChatMessage(role="system", content="").role == Role.SYSTEM  # Coercion works

    # Invalid role
    with pytest.raises(ValidationError):
        ChatMessage(role="admin", content="")


def test_presentation_event_polymorphism_adapter() -> None:
    """Test polymorphic deserialization using TypeAdapter."""
    # Create mixed list of events
    events = [
        {
            "type": "citation_block",
            "data": {
                "items": [{"source_id": "1", "uri": "https://doc1", "title": "Doc 1", "snippet": "foo"}]
            }
        },
        {
            "type": "media_carousel",
            "data": {
                "items": [{"url": "https://art1", "mime_type": "image/png"}]
            }
        },
    ]

    adapter = TypeAdapter(list[PresentationEvent])
    parsed = adapter.validate_python(events)

    assert len(parsed) == 2
    assert parsed[0].type == PresentationEventType.CITATION_BLOCK
    assert isinstance(parsed[0].data, CitationBlock)
    assert str(parsed[0].data.items[0].uri) == "https://doc1/" # AnyUrl adds trailing slash usually or sanitizes

    assert parsed[1].type == PresentationEventType.MEDIA_CAROUSEL
    assert isinstance(parsed[1].data, MediaCarousel)
    assert parsed[1].data.items[0].mime_type == "image/png"


def test_stream_packet_with_presentation_event() -> None:
    """Test embedding presentation events in StreamPacket."""
    citation_block = CitationBlock(items=[
        CitationItem(source_id="1", uri=AnyUrl("https://source"), title="Title", snippet="Quote")
    ])
    event = PresentationEvent(type=PresentationEventType.CITATION_BLOCK, data=citation_block)

    # Dump event to dict to fit StreamPacket payload schema
    packet = StreamPacket(op=StreamOpCode.EVENT, p=event.dump())

    assert packet.op == StreamOpCode.EVENT
    assert isinstance(packet.p, dict)
    assert packet.p["type"] == "citation_block"
    assert packet.p["data"]["items"][0]["snippet"] == "Quote"


def test_complex_immutability() -> None:
    """Verify deep immutability (to the extent frozen=True supports)."""
    citation_block = CitationBlock(items=[
        CitationItem(source_id="1", uri=AnyUrl("https://x"), title="X", snippet="y")
    ])
    event = PresentationEvent(type=PresentationEventType.CITATION_BLOCK, data=citation_block)

    # Direct field assignment fails
    with pytest.raises(ValidationError):
        setattr(event, "type", PresentationEventType.USER_ERROR)  # noqa: B010

    # Pydantic frozen models don't automatically freeze mutable sub-objects (like lists)
    # unless using FrozenSet or Tuple, but reassigning the field itself is blocked.
    # However, CitationBlock is also frozen.

    # Check that we can't assign to CitationBlock fields
    with pytest.raises(ValidationError):
        setattr(citation_block, "items", []) # noqa: B010

    # Standard Pydantic behavior: items list is technically mutable in Python if accessed directly
    # but strictly speaking we shouldn't modify it.
    assert len(citation_block.items) == 1


def test_json_roundtrip() -> None:
    """Test full JSON round-trip ensuring types are preserved."""
    original = ChatMessage(
        role=Role.TOOL,
        content='{"result": 42}',
        tool_call_id="call_123",
        name="calculator",
    )

    json_str = original.to_json()
    restored = ChatMessage.model_validate_json(json_str)

    assert original == restored
    assert restored.role == Role.TOOL
    assert restored.tool_call_id == "call_123"
    assert restored.timestamp == original.timestamp
