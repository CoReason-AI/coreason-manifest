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
    PresentationEvent,
    PresentationEventType,
    CitationBlock,
    MediaCarousel,
    ProgressUpdate,
    SessionHandle,
)
from typing import Any, List
from coreason_manifest.spec.common.identity import Identity
from coreason_manifest.spec.common.session import Interaction


def test_presentation_event_malformed_data() -> None:
    """Edge Case: Data payload does not match the expected structure for the type."""
    # mismatch: type is citation, data is media
    # The validator tries to cast. If it fails, it suppresses exception and leaves it as dict if allowed,
    # OR if the model validation allows it (it won't because fields are missing).
    # Since PresentationEvent.data includes `dict`, it might fall back to dict or fail depending on Pydantic's union mode.
    # We want to verify behavior.

    payload = {
        "type": "citation_block",
        "data": {
            "items": [
                {"url": "http://x", "mime_type": "image/png"} # Missing source_id, title for CitationItem
            ]
        }
    }

    # It should NOT cast to CitationBlock because validation fails.
    # It SHOULD fall back to dict because `dict` is in the Union.
    event = PresentationEvent.model_validate(payload)
    assert isinstance(event.data, dict)
    assert event.type == PresentationEventType.CITATION_BLOCK

    assert event.data["items"][0]["url"] == "http://x"


def test_presentation_event_unknown_type() -> None:
    """Edge Case: Unknown event type."""
    # Since PresentationEventType is an Enum, strict validation rejects unknown strings.
    with pytest.raises(ValidationError):
        PresentationEvent.model_validate({
            "type": "unknown_type",
            "data": {}
        })


def test_complex_nested_presentation() -> None:
    """Complex Case: deeply nested valid structure."""
    items = []
    for i in range(10):
        items.append({
            "source_id": f"s-{i}",
            "uri": f"https://example.com/{i}",
            "title": f"Title {i}",
            "snippet": "x" * 100
        })

    payload = {
        "type": "citation_block",
        "data": {
            "items": items
        }
    }

    event = PresentationEvent.model_validate(payload)
    assert isinstance(event.data, CitationBlock)
    assert len(event.data.items) == 10
    assert str(event.data.items[9].uri) == "https://example.com/9"


def test_polymorphic_list_preservation() -> None:
    """Complex Case: List of different events ensuring correct model resolution."""
    events_data = [
        {
            "type": "citation_block",
            "data": {"items": [{"source_id": "1", "uri": "https://a", "title": "A"}]}
        },
        {
            "type": "progress_indicator",
            "data": {"label": "Loading", "status": "running", "progress_percent": 50.0}
        },
        {
            "type": "media_carousel",
            "data": {"items": [{"url": "https://img", "mime_type": "image/jpeg"}]}
        },
        {
            "type": "user_error",
            "data": {"message": "oops"}
        }
    ]

    adapter = TypeAdapter(List[PresentationEvent])
    parsed = adapter.validate_python(events_data)

    assert isinstance(parsed[0].data, CitationBlock)
    assert isinstance(parsed[1].data, ProgressUpdate)
    assert isinstance(parsed[2].data, MediaCarousel)
    assert isinstance(parsed[3].data, dict) # user_error maps to dict

    assert parsed[1].data.status == "running"
    assert parsed[1].data.progress_percent == 50.0


def test_session_handle_exceptions() -> None:
    """Edge Case: SessionHandle implementation raising exceptions."""

    class FaultySession:
        @property
        def session_id(self) -> str: return "1"
        @property
        def identity(self) -> Identity: return Identity.anonymous()

        async def history(self, _limit: int = 10, _offset: int = 0) -> List[Interaction]:
            raise RuntimeError("DB Down")

        async def recall(self, _query: str, _limit: int = 5, _threshold: float = 0.7) -> List[str]:
            raise ValueError("Empty Query")

        async def store(self, _key: str, _value: Any) -> None:
            pass

        async def get(self, _key: str, _default: Any = None) -> Any:
            pass

    # Check that it still satisfies the protocol statically (if we were using mypy here)
    # runtime check:
    assert isinstance(FaultySession(), SessionHandle)
