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
    ArtifactEvent,
    ChatMessage,
    CitationEvent,
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
        {"type": "citation", "uri": "doc1", "text": "foo"},
        {"type": "artifact", "artifact_id": "art1", "mime_type": "image/png"},
    ]

    adapter = TypeAdapter(list[CitationEvent | ArtifactEvent])
    parsed = adapter.validate_python(events)

    assert len(parsed) == 2
    assert isinstance(parsed[0], CitationEvent)
    assert parsed[0].uri == "doc1"
    assert isinstance(parsed[1], ArtifactEvent)
    assert parsed[1].artifact_id == "art1"


def test_stream_packet_with_presentation_event() -> None:
    """Test embedding presentation events in StreamPacket (conceptually).

    Note: StreamPacket.p is strictly typed as Union[str, Dict[str, Any], StreamError, None]
    in the current spec. Ideally, it should support PresentationEvent, but currently
    it treats 'event' op as Dict. This test verifies we can dump PresentationEvent to that Dict.
    """
    citation = CitationEvent(uri="http://source", text="Quote")

    # Dump event to dict to fit StreamPacket payload schema
    packet = StreamPacket(op=StreamOpCode.EVENT, p=citation.dump())

    assert packet.op == StreamOpCode.EVENT
    assert isinstance(packet.p, dict)
    assert packet.p["type"] == "citation"
    assert packet.p["text"] == "Quote"


def test_complex_immutability() -> None:
    """Verify deep immutability (to the extent frozen=True supports)."""
    citation = CitationEvent(uri="http://x", text="y", indices=[10, 20])

    # Direct field assignment fails
    with pytest.raises(ValidationError):
        setattr(citation, "uri", "http://z")  # noqa: B010

    # Replacing the list (indices) fails
    with pytest.raises(ValidationError):
        setattr(citation, "indices", [0, 5])  # noqa: B010

    # Note: Pydantic frozen models don't automatically freeze mutable sub-objects (like lists)
    # unless using FrozenSet or Tuple, but reassigning the field itself is blocked.
    # Standard Pydantic behavior:
    assert citation.indices == [10, 20]


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
