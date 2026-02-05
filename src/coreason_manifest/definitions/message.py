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
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field

from ..common import CoReasonBaseModel


class Role(str, Enum):
    """The role of the message sender."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(CoReasonBaseModel):
    """A single message in a conversation."""

    model_config = ConfigDict(frozen=True)

    role: Role = Field(..., description="The role of the message sender.")
    content: str = Field(..., description="The content of the message.")
    name: Optional[str] = Field(None, description="The name of the author of this message.")
    tool_call_id: Optional[str] = Field(None, description="The tool call ID this message is responding to.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp of the message.",
    )


class AttachedFile(CoReasonBaseModel):
    """Represents a reference to a file uploaded to the blob storage."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="The unique file ID/UUID.")
    mime_type: Optional[str] = Field(None, description="The MIME type of the file (e.g., 'application/pdf').")


class ContentPart(CoReasonBaseModel):
    """A discrete unit of input that can contain text, attachments, or both."""

    model_config = ConfigDict(frozen=True)

    text: Optional[str] = Field(None, description="The textual instruction.")
    attachments: List[AttachedFile] = Field(default_factory=list, description="List of attached files.")


class MultiModalInput(CoReasonBaseModel):
    """The container for a rich user turn."""

    model_config = ConfigDict(frozen=True)

    parts: List[ContentPart] = Field(..., description="List of content parts.")
