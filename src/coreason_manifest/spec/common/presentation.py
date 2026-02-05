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
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import AnyUrl, ConfigDict, Field, model_validator

from ..common_base import CoReasonBaseModel


class PresentationEventType(StrEnum):
    """Types of presentation events."""

    THOUGHT_TRACE = "thought_trace"
    CITATION_BLOCK = "citation_block"
    PROGRESS_INDICATOR = "progress_indicator"
    MEDIA_CAROUSEL = "media_carousel"
    MARKDOWN_BLOCK = "markdown_block"
    USER_ERROR = "user_error"


class CitationItem(CoReasonBaseModel):
    """An individual citation item."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    uri: AnyUrl
    title: str
    snippet: str | None = None


class CitationBlock(CoReasonBaseModel):
    """A block of citations."""

    model_config = ConfigDict(frozen=True)

    items: list[CitationItem]


class ProgressUpdate(CoReasonBaseModel):
    """A progress update event."""

    model_config = ConfigDict(frozen=True)

    label: str
    status: Literal["running", "complete", "failed"]
    progress_percent: float | None = Field(None, ge=0.0, le=1.0)


class MediaItem(CoReasonBaseModel):
    """An individual media item."""

    model_config = ConfigDict(frozen=True)

    url: AnyUrl
    mime_type: str
    alt_text: str | None = None


class MediaCarousel(CoReasonBaseModel):
    """A carousel of media items."""

    model_config = ConfigDict(frozen=True)

    items: list[MediaItem]


class MarkdownBlock(CoReasonBaseModel):
    """A block of markdown content."""

    model_config = ConfigDict(frozen=True)

    content: str


class PresentationEvent(CoReasonBaseModel):
    """A container for presentation events."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # noqa: UP017
    type: PresentationEventType
    data: CitationBlock | ProgressUpdate | MediaCarousel | MarkdownBlock | dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def validate_data_payload(cls, values: Any) -> Any:
        """Validate data payload based on type."""
        if isinstance(values, dict):
            t = values.get("type")
            d = values.get("data")

            if t and d and isinstance(d, dict):
                # Coerce to specific model if applicable
                if t == PresentationEventType.CITATION_BLOCK:
                    values["data"] = CitationBlock.model_validate(d)
                elif t == PresentationEventType.PROGRESS_INDICATOR:
                    values["data"] = ProgressUpdate.model_validate(d)
                elif t == PresentationEventType.MEDIA_CAROUSEL:
                    values["data"] = MediaCarousel.model_validate(d)
                elif t == PresentationEventType.MARKDOWN_BLOCK:
                    values["data"] = MarkdownBlock.model_validate(d)
        return values
