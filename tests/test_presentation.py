# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions import (
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
    StreamOpCode,
    StreamPacket,
)


def test_citation_serialization() -> None:
    """Test serialization and immutability of Citation models."""
    item = CitationItem(
        source_id="1",
        uri="https://example.com/source",
        title="Example Source",
        confidence=0.95,
    )
    block = CitationBlock(citations=[item])

    dump = block.dump()
    assert dump["citations"][0]["source_id"] == "1"
    assert dump["citations"][0]["uri"] == "https://example.com/source"

    # Test immutability
    with pytest.raises(ValidationError):
        item.source_id = "2"  # type: ignore


def test_progress_update_serialization() -> None:
    """Test serialization of ProgressUpdate model."""
    update = ProgressUpdate(
        label="Searching...",
        status="running",
        progress_percent=0.5,
    )

    dump = update.dump()
    assert dump["status"] == "running"
    assert dump["progress_percent"] == 0.5


def test_media_carousel_serialization() -> None:
    """Test serialization of Media models."""
    item = MediaItem(
        url="https://example.com/image.png",
        mime_type="image/png",
        alt_text="An example image",
    )
    carousel = MediaCarousel(items=[item])

    dump = carousel.dump()
    assert len(dump["items"]) == 1
    assert dump["items"][0]["mime_type"] == "image/png"


def test_presentation_event_serialization() -> None:
    """Test serialization of PresentationEvent wrapper."""
    update = ProgressUpdate(
        label="Processing...",
        status="complete",
    )
    event_id = uuid4()
    now = datetime.now(timezone.utc)

    event = PresentationEvent(
        id=event_id,
        timestamp=now,
        type=PresentationEventType.PROGRESS_INDICATOR,
        data=update,
    )

    # Test JSON serialization of UUID and datetime
    json_str = event.to_json()
    data = json.loads(json_str)

    assert data["id"] == str(event_id)
    # Pydantic v2 might serialize UTC datetime with 'Z' instead of '+00:00'
    assert data["timestamp"].replace("Z", "+00:00") == now.isoformat()
    assert data["type"] == "PROGRESS_INDICATOR"
    assert data["data"]["status"] == "complete"


def test_presentation_event_generic_data() -> None:
    """Test PresentationEvent with generic dict data."""
    event = PresentationEvent(
        id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        type=PresentationEventType.THOUGHT_TRACE,
        data={"thought": "This is a thought trace."},
    )

    dump = event.dump()
    assert dump["data"]["thought"] == "This is a thought trace."


def test_stream_packet_serialization() -> None:
    """Test serialization of StreamPacket."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    # Test DELTA
    packet_delta = StreamPacket(
        stream_id=stream_id,
        seq=1,
        op=StreamOpCode.DELTA,
        t=now,
        p="Hello",
    )
    dump_delta = packet_delta.dump()
    assert dump_delta["op"] == "DELTA"
    assert dump_delta["p"] == "Hello"

    # Test EVENT
    update = ProgressUpdate(
        label="Processing...",
        status="complete",
    )
    event_id = uuid4()
    event = PresentationEvent(
        id=event_id,
        timestamp=now,
        type=PresentationEventType.PROGRESS_INDICATOR,
        data=update,
    )

    packet_event = StreamPacket(
        stream_id=stream_id,
        seq=2,
        op=StreamOpCode.EVENT,
        t=now,
        p=event,
    )
    dump_event = packet_event.dump()
    assert dump_event["op"] == "EVENT"
    assert dump_event["p"]["type"] == "PROGRESS_INDICATOR"

    # Test CLOSE (String payload allowed for CLOSE as per current validation logic)
    packet_close = StreamPacket(
        stream_id=stream_id,
        seq=3,
        op=StreamOpCode.CLOSE,
        t=now,
        p="Connection closed",
    )
    assert packet_close.p == "Connection closed"


def test_stream_packet_validation() -> None:
    """Test validation logic of StreamPacket."""
    stream_id = uuid4()
    now = datetime.now(timezone.utc)

    # DELTA must be string
    with pytest.raises(ValueError, match="Payload must be a string for DELTA op"):
        StreamPacket(
            stream_id=stream_id,
            seq=1,
            op=StreamOpCode.DELTA,
            t=now,
            p={"foo": "bar"},
        )

    # EVENT must not be string
    with pytest.raises(ValueError, match="Payload must be a PresentationEvent or Dict for EVENT op"):
        StreamPacket(
            stream_id=stream_id,
            seq=1,
            op=StreamOpCode.EVENT,
            t=now,
            p="Not an event",
        )
