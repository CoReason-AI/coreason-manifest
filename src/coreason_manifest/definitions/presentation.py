# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, ConfigDict

from coreason_manifest.definitions.base import CoReasonBaseModel


class PresentationEventType(str, Enum):
    """Types of presentation events for UI rendering.

    Values:
        THOUGHT_TRACE: For inner monologue/reasoning chains.
        CITATION_BLOCK: For sourcing facts.
        PROGRESS_INDICATOR: For UI spinners/status bars.
        MEDIA_CAROUSEL: For images/diagrams.
        MARKDOWN_BLOCK: For standard text output.
    """

    THOUGHT_TRACE = "THOUGHT_TRACE"
    CITATION_BLOCK = "CITATION_BLOCK"
    PROGRESS_INDICATOR = "PROGRESS_INDICATOR"
    MEDIA_CAROUSEL = "MEDIA_CAROUSEL"
    MARKDOWN_BLOCK = "MARKDOWN_BLOCK"


class CitationItem(CoReasonBaseModel):
    """An individual citation item sourcing a fact.

    Attributes:
        source_id: Unique identifier for the source.
        uri: The URI of the source.
        title: The title of the source.
        snippet: A relevant snippet from the source (optional).
        confidence: Confidence score (0.0 to 1.0).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    uri: AnyUrl
    title: str
    snippet: Optional[str] = None
    confidence: float


class CitationBlock(CoReasonBaseModel):
    """A block containing multiple citations.

    Attributes:
        citations: List of CitationItem objects.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    citations: List[CitationItem]


class ProgressUpdate(CoReasonBaseModel):
    """Status update for a long-running process.

    Attributes:
        label: Descriptive label for the current task (e.g., "Searching Google...").
        status: Current status ("running", "complete", "failed").
        progress_percent: Percentage of completion (0.0 to 1.0, optional).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    status: Literal["running", "complete", "failed"]
    progress_percent: Optional[float] = None


class MediaItem(CoReasonBaseModel):
    """A media item like an image or diagram.

    Attributes:
        url: URL of the media item.
        mime_type: MIME type of the media (e.g., "image/png").
        alt_text: Alternative text for accessibility (optional).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    url: AnyUrl
    mime_type: str
    alt_text: Optional[str] = None


class MediaCarousel(CoReasonBaseModel):
    """A collection of media items to be displayed in a carousel.

    Attributes:
        items: List of MediaItem objects.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    items: List[MediaItem]


class PresentationEvent(CoReasonBaseModel):
    """Wrapper for presentation events to be emitted to the UI.

    Attributes:
        id: Unique identifier for the event.
        timestamp: Time when the event was created.
        type: The type of presentation event.
        data: The payload data for the event.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    timestamp: datetime
    type: PresentationEventType
    data: Union[CitationBlock, ProgressUpdate, MediaCarousel, Dict[str, Any]]
