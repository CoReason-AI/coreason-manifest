# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from pydantic import TypeAdapter

from coreason_manifest import (
    CitationBlock,
    MediaCarousel,
    PresentationEvent,
    PresentationEventType,
)


def test_parse_presentation_events() -> None:
    """Test parsing a list of mixed presentation events using PresentationEvent."""
    data = [
        {
            "type": "citation_block",
            "data": {
                "items": [
                    {
                        "source_id": "src-1",
                        "uri": "https://example.com/ref",
                        "title": "Citation Title",
                        "snippet": "This is a citation.",
                    }
                ]
            },
        },
        {
            "type": "media_carousel",
            "data": {
                "items": [
                    {
                        "url": "https://example.com/download",
                        "mime_type": "text/markdown",
                        "alt_text": "art-123",
                    }
                ]
            },
        },
    ]

    adapter = TypeAdapter(list[PresentationEvent])
    parsed_events = adapter.validate_python(data)

    assert len(parsed_events) == 2

    # Check first event
    assert parsed_events[0].type == PresentationEventType.CITATION_BLOCK
    assert isinstance(parsed_events[0].data, CitationBlock)
    assert parsed_events[0].data.items[0].snippet == "This is a citation."
    assert str(parsed_events[0].data.items[0].uri) == "https://example.com/ref"

    # Check second event
    assert parsed_events[1].type == PresentationEventType.MEDIA_CAROUSEL
    assert isinstance(parsed_events[1].data, MediaCarousel)
    assert str(parsed_events[1].data.items[0].url) == "https://example.com/download"
