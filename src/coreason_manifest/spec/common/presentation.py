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
from typing import Any, Literal, Union
from uuid import UUID, uuid4

from pydantic import AnyUrl, ConfigDict, Field

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
    """A single citation item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str = Field(..., description="The ID of the source.")
    uri: AnyUrl = Field(..., description="The URI of the source.")
    title: str = Field(..., description="The title of the source.")
    snippet: str | None = Field(None, description="A snippet from the source.")


class CitationBlock(CoReasonBaseModel):
    """A block of citations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: list[CitationItem] = Field(default_factory=list, description="List of citation items.")


class ProgressUpdate(CoReasonBaseModel):
    """A progress update event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str = Field(..., description="Label for the progress.")
    status: Literal["running", "complete", "failed"] = Field(..., description="Status of the progress.")
    progress_percent: float | None = Field(None, description="Percentage of progress completed.")


class MediaItem(CoReasonBaseModel):
    """A single media item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: AnyUrl = Field(..., description="URL of the media.")
    mime_type: str = Field(..., description="MIME type of the media.")
    alt_text: str | None = Field(None, description="Alt text for the media.")


class MediaCarousel(CoReasonBaseModel):
    """A carousel of media items."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: list[MediaItem] = Field(default_factory=list, description="List of media items.")


class MarkdownBlock(CoReasonBaseModel):
    """A block of markdown content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    content: str = Field(..., description="Markdown content.")


class PresentationEvent(CoReasonBaseModel):
    """Container for presentation events."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4, description="Unique ID of the event.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the event.",
    )
    type: PresentationEventType = Field(..., description="The type of presentation event.")
    data: Union[CitationBlock, ProgressUpdate, MediaCarousel, MarkdownBlock, dict[str, Any]] = Field(
        ..., description="The event data.", union_mode="left_to_right"
    )
