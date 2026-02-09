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
    MarkdownBlock,
    MediaCarousel,
    MediaItem,
    NodePresentation,
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
    # Invalid status
    with pytest.raises(ValidationError) as excinfo:
        ProgressUpdate(label="Thinking", status="thinking")  # "thinking" is not allowed  # type: ignore

    assert "status" in str(excinfo.value)

    # Invalid progress_percent (> 1.0)
    with pytest.raises(ValidationError) as excinfo:
        ProgressUpdate(label="Thinking", status="running", progress_percent=1.5)

    assert "progress_percent" in str(excinfo.value)
    assert "less than or equal to 1" in str(excinfo.value)

    # Valid statuses work
    assert ProgressUpdate(label="Running", status="running").status == "running"
    assert ProgressUpdate(label="Done", status="complete").status == "complete"
    assert ProgressUpdate(label="Failed", status="failed").status == "failed"


def test_url_validation() -> None:
    """Verify validation fails for invalid URL in CitationItem."""
    with pytest.raises(ValidationError) as excinfo:
        CitationItem(source_id="src1", uri="invalid-url", title="Title")

    assert "uri" in str(excinfo.value)


def test_deserialization_citation() -> None:
    """Verify deserialization from raw dictionary for CitationBlock."""
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


def test_deserialization_progress() -> None:
    """Verify deserialization from raw dictionary for ProgressUpdate."""
    raw_dict = {
        "type": "progress_indicator",
        "data": {
            "label": "Processing...",
            "status": "running",
            "progress_percent": 0.75,
        },
    }

    event = PresentationEvent.model_validate(raw_dict)

    assert event.type == PresentationEventType.PROGRESS_INDICATOR
    assert isinstance(event.data, ProgressUpdate)
    assert event.data.label == "Processing..."
    assert event.data.status == "running"
    assert event.data.progress_percent == 0.75


def test_deserialization_media() -> None:
    """Verify deserialization from raw dictionary for MediaCarousel."""
    raw_dict = {
        "type": "media_carousel",
        "data": {
            "items": [
                {
                    "url": "https://example.com/img.png",
                    "mime_type": "image/png",
                }
            ]
        },
    }

    event = PresentationEvent.model_validate(raw_dict)

    assert event.type == PresentationEventType.MEDIA_CAROUSEL
    assert isinstance(event.data, MediaCarousel)
    assert len(event.data.items) == 1
    assert str(event.data.items[0].url) == "https://example.com/img.png"


def test_deserialization_markdown() -> None:
    """Verify deserialization from raw dictionary for MarkdownBlock."""
    raw_dict = {
        "type": "markdown_block",
        "data": {
            "content": "# Hello World\n\nThis is markdown.",
        },
    }

    event = PresentationEvent.model_validate(raw_dict)

    assert event.type == PresentationEventType.MARKDOWN_BLOCK
    assert isinstance(event.data, MarkdownBlock)
    assert event.data.content == "# Hello World\n\nThis is markdown."


def test_immutability() -> None:
    """Verify immutability of the models."""
    progress = ProgressUpdate(label="Loading", status="running", progress_percent=0.5)
    event = PresentationEvent(type=PresentationEventType.PROGRESS_INDICATOR, data=progress)

    # Try to modify nested data
    assert isinstance(event.data, ProgressUpdate)
    with pytest.raises(ValidationError):
        event.data.label = "New Label"  # type: ignore[misc]

    # Try to modify event field
    with pytest.raises(ValidationError):
        event.type = PresentationEventType.MARKDOWN_BLOCK  # type: ignore[misc]


def test_node_presentation_valid() -> None:
    """Verify NodePresentation with valid inputs."""
    presentation = NodePresentation(x=100.5, y=200.0)
    assert presentation.x == 100.5
    assert presentation.y == 200.0
    assert presentation.color is None
    assert presentation.z_index == 0

    presentation = NodePresentation(x=0, y=0, color="#FF5733", label="Start", z_index=10)
    assert presentation.color == "#FF5733"
    assert presentation.label == "Start"
    assert presentation.z_index == 10


def test_node_presentation_color_validation() -> None:
    """Verify NodePresentation color validation."""
    # Valid colors
    assert NodePresentation(x=0, y=0, color="#000000").color == "#000000"
    assert NodePresentation(x=0, y=0, color="#ffffff").color == "#ffffff"
    assert NodePresentation(x=0, y=0, color="#ABCDEF").color == "#ABCDEF"

    # Invalid colors
    invalid_colors = ["red", "#123", "#GGGGGG", "123456", "#12345"]
    for color in invalid_colors:
        with pytest.raises(ValidationError) as excinfo:
            NodePresentation(x=0, y=0, color=color)
        assert "valid 6-char hex code" in str(excinfo.value)


def test_node_presentation_integration() -> None:
    """Verify integration of NodePresentation in RecipeNode."""
    from coreason_manifest import AgentNode

    # Create a node with presentation
    node = AgentNode(
        id="node-1",
        agent_ref="agent-v1",
        presentation=NodePresentation(x=150, y=300, color="#00FF00"),
    )

    dumped = node.model_dump(mode="json")
    assert dumped["presentation"]["x"] == 150.0
    assert dumped["presentation"]["y"] == 300.0
    assert dumped["presentation"]["color"] == "#00FF00"

    # Create a node without presentation
    node_no_pres = AgentNode(id="node-2", agent_ref="agent-v1")
    assert node_no_pres.presentation is None
