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


def test_polymorphic_serialization() -> None:
    """Verify polymorphic serialization with MediaCarousel."""
    payload = MediaCarousel(
        items=[
            MediaItem(url="http://example.com/1.jpg", mime_type="image/jpeg", alt_text="Image 1"),
            MediaItem(url="http://example.com/2.png", mime_type="image/png"),
        ]
    )

    event = PresentationEvent(type=PresentationEventType.MEDIA_CAROUSEL, data=payload)

    dumped = event.model_dump(mode="json")

    assert dumped["type"] == "media_carousel"
    assert len(dumped["data"]["items"]) == 2
    assert dumped["data"]["items"][0]["mime_type"] == "image/jpeg"
    assert dumped["data"]["items"][1]["mime_type"] == "image/png"


def test_validation_logic() -> None:
    """Verify validation fails for invalid status in ProgressUpdate."""
    with pytest.raises(ValidationError) as excinfo:
        ProgressUpdate(label="Thinking", status="thinking")  # "thinking" is not allowed  # type: ignore

    assert "status" in str(excinfo.value)
    # Also verify valid statuses work
    assert ProgressUpdate(label="Running", status="running").status == "running"


def test_deserialization() -> None:
    """Verify deserialization from raw dictionary."""
    raw_dict = {
        "type": "citation_block",
        "data": {
            "items": [
                {
                    "source_id": "src1",
                    "uri": "https://example.com/ref",
                    "title": "Reference Title",
                    "snippet": "Some snippet",
                }
            ]
        },
    }

    event = PresentationEvent.model_validate(raw_dict)

    assert event.type == PresentationEventType.CITATION_BLOCK
    assert isinstance(event.data, CitationBlock)
    assert len(event.data.items) == 1
    item = event.data.items[0]
    assert isinstance(item, CitationItem)
    assert str(item.uri) == "https://example.com/ref"
    assert item.title == "Reference Title"


def test_immutability() -> None:
    """Verify immutability of the models."""
    progress = ProgressUpdate(label="Loading", status="running", progress_percent=0.5)
    event = PresentationEvent(type=PresentationEventType.PROGRESS_INDICATOR, data=progress)

    # Try to modify nested data
    # We must assert the type for MyPy before accessing fields, or use type ignore if we are intentionally breaking it
    assert isinstance(event.data, ProgressUpdate)
    with pytest.raises(ValidationError):
        event.data.label = "New Label"  # type: ignore[misc, unused-ignore]

    # Try to modify event field
    with pytest.raises(ValidationError):
        event.type = PresentationEventType.MARKDOWN_BLOCK  # type: ignore[misc, unused-ignore]
