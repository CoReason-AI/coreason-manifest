# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel


class Role(StrEnum):
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
    name: str | None = Field(None, description="The name of the author of this message.")
    tool_call_id: str | None = Field(None, description="The tool call ID this message is responding to.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="The timestamp of the message.",
    )
