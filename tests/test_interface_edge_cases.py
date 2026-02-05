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


def test_empty_collections() -> None:
    """Test that empty collections are valid but empty."""
    # Empty Citation Block
    block = CitationBlock(items=[])
    assert block.items == []
    event = PresentationEvent(type=PresentationEventType.CITATION_BLOCK, data=block)
    assert isinstance(event.data, CitationBlock)
    assert len(event.data.items) == 0

    # Empty Media Carousel
    carousel = MediaCarousel(items=[])
    assert carousel.items == []
    event2 = PresentationEvent(type=PresentationEventType.MEDIA_CAROUSEL, data=carousel)
    assert isinstance(event2.data, MediaCarousel)
    assert len(event2.data.items) == 0


def test_missing_optional_fields() -> None:
    """Test that optional fields (snippets, alt_text, percent) can be omitted."""
    # Citation without snippet
    item = CitationItem(
        source_id="1",
        uri="https://example.com",
        title="Title",
        # snippet omitted
    )
    assert item.snippet is None

    # Media without alt_text
    media = MediaItem(url="https://example.com/img.png", mime_type="image/png")
    assert media.alt_text is None

    # Progress without percent
    prog = ProgressUpdate(label="Loading", status="running")
    assert prog.progress_percent is None


def test_extreme_values() -> None:
    """Test extreme values in fields."""
    # Progress percent > 1.0 or < 0.0 (technically allowed by float, logic might restrict but schema is float)
    prog = ProgressUpdate(label="Overflow", status="running", progress_percent=150.5)
    assert prog.progress_percent == 150.5

    prog_neg = ProgressUpdate(label="Underflow", status="running", progress_percent=-10.0)
    assert prog_neg.progress_percent == -10.0


def test_invalid_enum_coercion() -> None:
    """Test that invalid strings do not coerce to enums."""
    with pytest.raises(ValidationError):
        PresentationEvent(
            type="invalid_type",
            data={"foo": "bar"},
        )


def test_fallback_dictionary_behavior() -> None:
    """Test that arbitrary dicts are accepted if type doesn't match a specific model,
    or explicitly for user_error/thought_trace which map to dict in the Union."""

    # user_error maps to dict
    payload = {"message": "Error", "code": 500}
    event = PresentationEvent(type=PresentationEventType.USER_ERROR, data=payload)
    assert isinstance(event.data, dict)
    assert event.data["code"] == 500

    # Test mismatch: defined type (citation_block) but data is just a dict
    # that matches the structure. Pydantic might coerce it to CitationBlock.
    raw_citation = {"items": [{"source_id": "1", "uri": "https://a.com", "title": "A"}]}
    event_coerce = PresentationEvent(type=PresentationEventType.CITATION_BLOCK, data=raw_citation)

    # Because Union includes CitationBlock, Pydantic will try to validate against it first
    # (or left-to-right). Since the dict matches CitationBlock schema, it should become CitationBlock.
    assert isinstance(event_coerce.data, CitationBlock)

    # Now test a dict that DOES NOT match CitationBlock schema but type is citation_block.
    # It should fall back to 'dict' in the Union.
    bad_citation = {"foo": "bar"}  # Missing 'items'

    # Actually, with union_mode='left_to_right', it tries CitationBlock, fails, then tries next... finally dict.
    # So it should result in a dict.
    event_fallback = PresentationEvent(type=PresentationEventType.CITATION_BLOCK, data=bad_citation)
    assert isinstance(event_fallback.data, dict)
    assert event_fallback.data["foo"] == "bar"
