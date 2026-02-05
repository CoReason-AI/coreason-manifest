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
    AgentCapabilities,
    CapabilityType,
    DeliveryMode,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
)


def test_presentation_polymorphism() -> None:
    """Test Case 1: Presentation Polymorphism"""
    carousel = MediaCarousel(
        items=[
            MediaItem(
                url="https://example.com/image.png",
                mime_type="image/png",
                alt_text="Example Image",
            )
        ]
    )
    event = PresentationEvent(type=PresentationEventType.MEDIA_CAROUSEL, data=carousel)

    # Serialize
    json_str = event.to_json()
    assert "media_carousel" in json_str
    assert "https://example.com/image.png" in json_str

    # Deserialize
    restored = PresentationEvent.model_validate_json(json_str)
    assert restored.type == PresentationEventType.MEDIA_CAROUSEL
    assert isinstance(restored.data, MediaCarousel)
    assert len(restored.data.items) == 1
    assert str(restored.data.items[0].url) == "https://example.com/image.png"


def test_progress_validation() -> None:
    """Test Case 2: Progress Validation"""
    # Valid
    ProgressUpdate(label="Processing", status="running", progress_percent=0.5)

    # Invalid status
    with pytest.raises(ValidationError) as exc:
        ProgressUpdate(label="Thinking", status="thinking")
    assert "Input should be 'running', 'complete' or 'failed'" in str(exc.value)


def test_capability_contracts() -> None:
    """Test Case 3: Capability Contracts"""
    caps = AgentCapabilities(type=CapabilityType.ATOMIC, delivery_mode=DeliveryMode.SERVER_SENT_EVENTS)

    assert caps.type == CapabilityType.ATOMIC
    assert caps.delivery_mode == "server_sent_events"
    assert caps.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS

    # Immutability Check
    with pytest.raises(ValidationError):
        setattr(caps, "delivery_mode", DeliveryMode.REQUEST_RESPONSE)  # noqa: B010
