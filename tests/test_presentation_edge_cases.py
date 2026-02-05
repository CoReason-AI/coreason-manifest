import pytest
from pydantic import ValidationError

from coreason_manifest import (
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
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
