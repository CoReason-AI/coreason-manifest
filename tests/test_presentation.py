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
        item.source_id = "2" # type: ignore


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
