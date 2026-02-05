# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from pydantic import AnyUrl

from coreason_manifest.spec.common.capabilities import (
    AgentCapabilities,
    CapabilityType,
    DeliveryMode,
)
from coreason_manifest.spec.common.identity import Identity
from coreason_manifest.spec.common.presentation import (
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
)
from coreason_manifest.spec.common.session import Interaction
from coreason_manifest.spec.interfaces.session import SessionHandle


def test_presentation_serialization_media_carousel() -> None:
    media_item = MediaItem(
        url=AnyUrl("https://example.com/image.png"),
        mime_type="image/png",
        alt_text="An example image",
    )
    carousel = MediaCarousel(items=[media_item])
    event = PresentationEvent(type=PresentationEventType.MEDIA_CAROUSEL, data=carousel)

    json_output = event.model_dump_json()
    assert '"type":"media_carousel"' in json_output
    # Pydantic V2 compact JSON
    assert '"mime_type":"image/png"' in json_output

    # Test validator with dict input
    event_dict = {
        "type": "media_carousel",
        "data": {
            "items": [
                {
                    "url": "https://example.com/image.png",
                    "mime_type": "image/png",
                    "alt_text": "An example image",
                }
            ]
        },
    }
    event_from_dict = PresentationEvent.model_validate(event_dict)
    assert isinstance(event_from_dict.data, MediaCarousel)
    assert event_from_dict.data.items[0].mime_type == "image/png"


def test_capabilities_defaults() -> None:
    caps = AgentCapabilities()
    assert caps.type == CapabilityType.GRAPH
    assert caps.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert caps.history_support is True


def test_memory_protocol() -> None:
    class MockSession:
        @property
        def session_id(self) -> str:
            return "123"

        @property
        def identity(self) -> Identity:
            return Identity.anonymous()

        async def history(self, _limit: int = 10, _offset: int = 0) -> list[Interaction]:
            return []

        async def recall(
            self, _query: str, _limit: int = 5, _threshold: float = 0.7
        ) -> list[str]:
            return []

        async def store(self, _key: str, value: Any) -> None:
            pass

        async def get(self, _key: str, default: Any = None) -> Any:
            return default

    # Verify runtime checkable
    assert isinstance(MockSession(), SessionHandle)
