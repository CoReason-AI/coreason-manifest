# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import List

from pydantic import TypeAdapter

from coreason_manifest import (
    AnyPresentationEvent,
    ArtifactEvent,
    CitationEvent,
    PresentationEventType,
)


def test_parse_any_presentation_event() -> None:
    """Test parsing a list of mixed presentation events using AnyPresentationEvent."""
    data = [
        {
            "type": "citation",
            "uri": "https://example.com/ref",
            "text": "This is a citation.",
            "indices": [0, 10],
        },
        {
            "type": "artifact",
            "artifact_id": "art-123",
            "mime_type": "text/markdown",
            "url": "https://example.com/download",
        },
    ]

    adapter = TypeAdapter(List[AnyPresentationEvent])
    parsed_events = adapter.validate_python(data)

    assert len(parsed_events) == 2

    # Check first event
    assert isinstance(parsed_events[0], CitationEvent)
    assert parsed_events[0].type == PresentationEventType.CITATION
    assert parsed_events[0].uri == "https://example.com/ref"

    # Check second event
    assert isinstance(parsed_events[1], ArtifactEvent)
    assert parsed_events[1].type == PresentationEventType.ARTIFACT
    assert parsed_events[1].artifact_id == "art-123"
