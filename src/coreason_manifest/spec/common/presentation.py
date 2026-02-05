# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel
from .error import ErrorDomain


class PresentationEventType(StrEnum):
    """Types of presentation events."""

    CITATION = "citation"
    ARTIFACT = "artifact"
    USER_ERROR = "user_error"


class PresentationEvent(CoReasonBaseModel):
    """Base class for presentation events."""

    model_config = ConfigDict(frozen=True)

    type: PresentationEventType = Field(..., description="The type of presentation event.")


class CitationEvent(PresentationEvent):
    """An event representing a citation."""

    type: Literal[PresentationEventType.CITATION] = PresentationEventType.CITATION
    uri: str = Field(..., description="The source URI.")
    text: str = Field(..., description="The quoted text.")
    indices: list[int] | None = Field(None, description="Start and end character indices.")


class ArtifactEvent(PresentationEvent):
    """An event representing a generated artifact."""

    type: Literal[PresentationEventType.ARTIFACT] = PresentationEventType.ARTIFACT
    artifact_id: str = Field(..., description="Unique ID of the artifact.")
    mime_type: str = Field(..., description="MIME type of the artifact.")
    url: str | None = Field(None, description="Download URL if applicable.")


class UserErrorEvent(PresentationEvent):
    """An event representing a user-facing error."""

    type: Literal[PresentationEventType.USER_ERROR] = PresentationEventType.USER_ERROR
    message: str = Field(..., description="The human-readable message.")
    code: int | None = Field(None, description="Semantic integer code, e.g. 400, 503.")
    domain: ErrorDomain = Field(ErrorDomain.SYSTEM, description="The domain of the error.")
    retryable: bool = Field(False, description="Whether the error is retryable.")


AnyPresentationEvent = CitationEvent | ArtifactEvent | UserErrorEvent
