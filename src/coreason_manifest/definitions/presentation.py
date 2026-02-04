# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import Enum
from typing import List, Literal, Optional

from pydantic import ConfigDict, Field

from ..common import CoReasonBaseModel


class PresentationEventType(str, Enum):
    """Types of presentation events."""

    CITATION = "citation"
    ARTIFACT = "artifact"


class PresentationEvent(CoReasonBaseModel):
    """Base class for presentation events."""

    model_config = ConfigDict(frozen=True)

    type: PresentationEventType = Field(..., description="The type of presentation event.")


class CitationEvent(PresentationEvent):
    """An event representing a citation."""

    type: Literal[PresentationEventType.CITATION] = PresentationEventType.CITATION
    uri: str = Field(..., description="The source URI.")
    text: str = Field(..., description="The quoted text.")
    indices: Optional[List[int]] = Field(None, description="Start and end character indices.")


class ArtifactEvent(PresentationEvent):
    """An event representing a generated artifact."""

    type: Literal[PresentationEventType.ARTIFACT] = PresentationEventType.ARTIFACT
    artifact_id: str = Field(..., description="Unique ID of the artifact.")
    mime_type: str = Field(..., description="MIME type of the artifact.")
    url: Optional[str] = Field(None, description="Download URL if applicable.")
