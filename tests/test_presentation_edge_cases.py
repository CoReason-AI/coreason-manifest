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
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
)


def test_edge_case_empty_media_carousel() -> None:
    """Verify MediaCarousel with empty items list."""
    payload = MediaCarousel(items=[])
    event = PresentationEvent(type=PresentationEventType.MEDIA_CAROUSEL, data=payload)

    dumped = event.model_dump(mode="json")
    assert dumped["data"]["items"] == []

    # Round trip
    loaded = PresentationEvent.model_validate(dumped)
    assert isinstance(loaded.data, MediaCarousel)
    assert loaded.data.items == []


def test_edge_case_citation_missing_optional() -> None:
    """Verify CitationItem handles missing optional snippet."""
    item = CitationItem(
        source_id="s1",
        uri="http://example.com",
        title="Title",
        # snippet is optional
    )
    assert item.snippet is None

    event = PresentationEvent(type=PresentationEventType.CITATION_BLOCK, data=CitationBlock(items=[item]))
    dumped = event.model_dump(mode="json")
    assert dumped["data"]["items"][0]["snippet"] is None


def test_thought_trace_payload() -> None:
    """Verify ThoughtTrace payload (generic dict)."""
    raw_dict = {"type": "thought_trace", "data": {"thought": "Reasoning...", "confidence": 0.9}}
    event = PresentationEvent.model_validate(raw_dict)
    assert event.type == PresentationEventType.THOUGHT_TRACE
    assert isinstance(event.data, dict)
    assert event.data["thought"] == "Reasoning..."


def test_invalid_payload_for_type() -> None:
    """Verify that providing invalid schema for a specific type raises ValidationError."""
    raw_dict = {
        "type": "progress_indicator",
        "data": {
            "label": "Missing status field"
            # status is required
        },
    }
    # This should fail inside the validator when it tries to coerce to ProgressUpdate
    with pytest.raises(ValidationError):
        PresentationEvent.model_validate(raw_dict)


def test_complex_roundtrip() -> None:
    """Verify round trip of a complex structure."""
    event = PresentationEvent(
        type=PresentationEventType.MEDIA_CAROUSEL,
        data=MediaCarousel(
            items=[
                MediaItem(url="http://a.com/1.png", mime_type="image/png"),
                MediaItem(url="http://b.com/2.jpg", mime_type="image/jpeg", alt_text="Alt"),
            ]
        ),
    )

    json_str = event.model_dump_json()
    loaded = PresentationEvent.model_validate_json(json_str)

    assert loaded.type == PresentationEventType.MEDIA_CAROUSEL
    assert isinstance(loaded.data, MediaCarousel)
    assert len(loaded.data.items) == 2
    assert loaded.data.items[1].alt_text == "Alt"


def test_progress_boundaries() -> None:
    """Test boundary values for ProgressUpdate."""
    # 0.0 is valid
    p0 = ProgressUpdate(label="Start", status="running", progress_percent=0.0)
    assert p0.progress_percent == 0.0

    # 1.0 is valid
    p1 = ProgressUpdate(label="End", status="complete", progress_percent=1.0)
    assert p1.progress_percent == 1.0

    # Slightly above 1.0
    with pytest.raises(ValidationError):
        ProgressUpdate(label="Over", status="failed", progress_percent=1.0000001)

    # Slightly below 0.0
    with pytest.raises(ValidationError):
        ProgressUpdate(label="Under", status="failed", progress_percent=-0.0000001)


def test_complex_urls() -> None:
    """Test CitationItem with complex URLs."""
    # Query parameters and fragments
    url = "https://example.com/path/to/resource?query=param&other=123#fragment"
    item = CitationItem(source_id="src1", uri=url, title="Complex URL")
    assert str(item.uri) == url

    # IP address URL
    url_ip = "http://192.168.1.1:8080/resource"
    item_ip = CitationItem(source_id="src2", uri=url_ip, title="IP URL")
    assert str(item_ip.uri) == url_ip

    # Localhost
    url_local = "http://localhost:3000"
    item_local = CitationItem(source_id="src3", uri=url_local, title="Localhost")
    assert str(item_local.uri) == f"{url_local}/"


def test_media_item_optional_fields() -> None:
    """Test MediaItem with optional fields missing or empty."""
    # Missing alt_text
    item = MediaItem(url="http://example.com/img.png", mime_type="image/png")
    assert item.alt_text is None

    # Empty string alt_text (valid, but effectively empty)
    item_empty = MediaItem(url="http://example.com/img.png", mime_type="image/png", alt_text="")
    assert item_empty.alt_text == ""


def test_user_error_payload() -> None:
    """Test USER_ERROR with generic dictionary payload."""
    error_data = {
        "code": 404,
        "message": "Not Found",
        "details": {"resource": "user-123"},
        "timestamp": "2023-01-01T00:00:00Z",
    }

    event = PresentationEvent(type=PresentationEventType.USER_ERROR, data=error_data)

    assert event.type == PresentationEventType.USER_ERROR
    assert isinstance(event.data, dict)
    assert event.data["code"] == 404
    assert event.data["details"]["resource"] == "user-123"

    # Verify serialization
    dumped = event.model_dump(mode="json")
    assert dumped["type"] == "user_error"
    assert dumped["data"]["code"] == 404
