# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import AnyUrl, ConfigDict, Field, field_validator, model_validator

from ..common_base import ManifestBaseModel


class NodePresentation(ManifestBaseModel):
    """Visual presentation metadata for a graph node."""

    model_config = ConfigDict(frozen=True)

    x: float = Field(..., description="X coordinate on the canvas")
    y: float = Field(..., description="Y coordinate on the canvas")
    label: str | None = Field(None, description="Human-readable label override")
    color: str | None = Field(None, description="Hex color code")
    icon: str | None = Field(None, description="Icon name (e.g. 'lucide:brain')")
    z_index: int = Field(0, description="Z-index for rendering order")

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid 6-char hex code (e.g. #FF0000)")
        return v


class PresentationEventType(StrEnum):
    """Types of presentation events."""

    THOUGHT_TRACE = "thought_trace"
    CITATION_BLOCK = "citation_block"
    PROGRESS_INDICATOR = "progress_indicator"
    MEDIA_CAROUSEL = "media_carousel"
    MARKDOWN_BLOCK = "markdown_block"
    USER_ERROR = "user_error"


class CitationItem(ManifestBaseModel):
    """An individual citation item."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    uri: AnyUrl
    title: str
    snippet: str | None = None


class CitationBlock(ManifestBaseModel):
    """A block of citations."""

    model_config = ConfigDict(frozen=True)

    items: list[CitationItem]


class ProgressUpdate(ManifestBaseModel):
    """A progress update event."""

    model_config = ConfigDict(frozen=True)

    label: str
    status: Literal["running", "complete", "failed"]
    progress_percent: float | None = Field(None, ge=0.0, le=1.0)


class MediaItem(ManifestBaseModel):
    """An individual media item."""

    model_config = ConfigDict(frozen=True)

    url: AnyUrl
    mime_type: str
    alt_text: str | None = None


class MediaCarousel(ManifestBaseModel):
    """A carousel of media items."""

    model_config = ConfigDict(frozen=True)

    items: list[MediaItem]


class MarkdownBlock(ManifestBaseModel):
    """A block of markdown content."""

    model_config = ConfigDict(frozen=True)

    content: str


class PresentationEvent(ManifestBaseModel):
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


class GraphTheme(ManifestBaseModel):
    """Configuration for graph visualization styling."""

    orientation: Literal["TD", "LR"] = "TD"
    node_styles: dict[str, str] = Field(
        default_factory=lambda: {
            "agent": "fill:#e3f2fd,stroke:#1565c0",
            "human": "fill:#fff3e0,stroke:#e65100",
        }
    )
    node_shapes: dict[str, str] = Field(
        default_factory=dict, description="Map of node type to shape (rect, diamond, hexagon, etc.)"
    )
    primary_color: str | None = None
    secondary_color: str | None = None
    font_family: str | None = None
    interaction_callback: str = "call_interaction_handler"


class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RuntimeStateSnapshot(ManifestBaseModel):
    """A frozen snapshot of execution state for visualization."""

    node_states: dict[str, NodeStatus]
    active_path: list[str] = Field(default_factory=list)
