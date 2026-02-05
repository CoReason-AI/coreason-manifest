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
    ChatMessage,
    CitationBlock,
    CitationItem,
    MediaCarousel,
    PresentationEvent,
    PresentationEventType,
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
                "items": [
                    {
                        "source_id": "s1",
                        "uri": "https://doc1.com",
                        "title": "foo",
                    }
                ]
            },
        },
        {
            "type": "media_carousel",
            "data": {"items": [{"url": "https://art1.com", "mime_type": "image/png"}]},
        },
    ]

    adapter = TypeAdapter(list[PresentationEvent])
    parsed = adapter.validate_python(events)

    assert len(parsed) == 2
    assert parsed[0].type == PresentationEventType.CITATION_BLOCK
    assert isinstance(parsed[0].data, CitationBlock)
    assert str(parsed[0].data.items[0].uri) == "https://doc1.com/"
    assert parsed[1].type == PresentationEventType.MEDIA_CAROUSEL
    assert isinstance(parsed[1].data, MediaCarousel)


def test_stream_packet_with_presentation_event() -> None:
    """Test embedding presentation events in StreamPacket (conceptually)."""
    citation_event = PresentationEvent(
        type=PresentationEventType.CITATION_BLOCK,
        data=CitationBlock(items=[CitationItem(source_id="s1", uri="http://source.com", title="Quote")]),
    )

    # Dump event to dict to fit StreamPacket payload schema
    packet = StreamPacket(op=StreamOpCode.EVENT, p=citation_event.dump())

    assert packet.op == StreamOpCode.EVENT
    assert isinstance(packet.p, dict)
    assert packet.p["type"] == "citation_block"
    assert packet.p["data"]["items"][0]["title"] == "Quote"


def test_complex_immutability() -> None:
    """Verify deep immutability (to the extent frozen=True supports)."""
    event = PresentationEvent(
        type=PresentationEventType.CITATION_BLOCK,
        data=CitationBlock(items=[CitationItem(source_id="s1", uri="http://x.com", title="y")]),
    )

    # Direct field assignment fails
    with pytest.raises(ValidationError):
        setattr(event, "type", PresentationEventType.MEDIA_CAROUSEL)  # noqa: B010

    # Replacing the data fails
    with pytest.raises(ValidationError):
        setattr(event, "data", {})  # noqa: B010


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
