# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from enum import StrEnum
from typing import List, Literal, Union, Any, Optional
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field, AnyUrl, model_validator

from coreason_manifest.spec.common_base import CoReasonBaseModel


class PresentationEventType(StrEnum):
    """Types of presentation events."""

    THOUGHT_TRACE = "thought_trace"
    CITATION_BLOCK = "citation_block"
    PROGRESS_INDICATOR = "progress_indicator"
    MEDIA_CAROUSEL = "media_carousel"
    MARKDOWN_BLOCK = "markdown_block"
    USER_ERROR = "user_error"


class CitationItem(CoReasonBaseModel):
    """A single citation item."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    uri: AnyUrl
    title: str
    snippet: Optional[str] = None


class CitationBlock(CoReasonBaseModel):
    """A block of citations."""

    model_config = ConfigDict(frozen=True)

    items: List[CitationItem]


class ProgressUpdate(CoReasonBaseModel):
    """A progress update event."""

    model_config = ConfigDict(frozen=True)

    label: str
    status: Literal["running", "complete", "failed"]
    progress_percent: Optional[float] = None


class MediaItem(CoReasonBaseModel):
    """A single media item."""

    model_config = ConfigDict(frozen=True)

    url: AnyUrl
    mime_type: str
    alt_text: Optional[str] = None


class MediaCarousel(CoReasonBaseModel):
    """A carousel of media items."""

    model_config = ConfigDict(frozen=True)

    items: List[MediaItem]


class MarkdownBlock(CoReasonBaseModel):
    """A block of markdown content."""

    model_config = ConfigDict(frozen=True)

    content: str


class PresentationEvent(CoReasonBaseModel):
    """Container for presentation events."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: PresentationEventType
    data: Union[CitationBlock, ProgressUpdate, MediaCarousel, MarkdownBlock, dict]

    @model_validator(mode="before")
    @classmethod
    def validate_data_payload(cls, values: Any) -> Any:
        """Validate and cast the data payload based on the event type."""
        if not isinstance(values, dict):
            return values

        event_type = values.get("type")
        data = values.get("data")

        if not event_type or not isinstance(data, dict):
            return values

        # Map types to models
        model_map = {
            PresentationEventType.CITATION_BLOCK: CitationBlock,
            PresentationEventType.PROGRESS_INDICATOR: ProgressUpdate,
            PresentationEventType.MEDIA_CAROUSEL: MediaCarousel,
            PresentationEventType.MARKDOWN_BLOCK: MarkdownBlock,
        }

        if event_type in model_map:
            try:
                values["data"] = model_map[event_type](**data)
            except Exception:
                # If validation fails, let Pydantic handle the error or fallback to dict if allowed
                pass

        return values
