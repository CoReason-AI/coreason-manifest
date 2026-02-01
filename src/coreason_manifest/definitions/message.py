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
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# --- Enums ---


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


# --- Message Parts ---


class TextPart(BaseModel):
    """Represents text content sent to or received from the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["text"] = "text"
    content: str


class BlobPart(BaseModel):
    """Represents blob binary data sent inline to the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["blob"] = "blob"
    content: str  # Base64 encoded string
    modality: Modality
    mime_type: Optional[str] = None


class FilePart(BaseModel):
    """Represents an external referenced file sent to the model by file id."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["file"] = "file"
    file_id: str
    modality: Modality
    mime_type: Optional[str] = None


class UriPart(BaseModel):
    """Represents an external referenced file sent to the model by URI."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["uri"] = "uri"
    uri: str
    modality: Modality
    mime_type: Optional[str] = None


class ToolCallRequestPart(BaseModel):
    """Represents a tool call requested by the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["tool_call"] = "tool_call"
    name: str
    arguments: Dict[str, Any]  # Structured arguments
    id: Optional[str] = None


class ToolCallResponsePart(BaseModel):
    """Represents a tool call result sent to the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["tool_call_response"] = "tool_call_response"
    response: Any  # The result of the tool call
    id: Optional[str] = None


class ReasoningPart(BaseModel):
    """Represents reasoning/thinking content received from the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["reasoning"] = "reasoning"
    content: str


# --- Union of All Parts ---

Part = Union[TextPart, BlobPart, FilePart, UriPart, ToolCallRequestPart, ToolCallResponsePart, ReasoningPart]

# --- Main Message Model ---


class ChatMessage(BaseModel):
    """Represents a message in a conversation with an LLM."""

    model_config = ConfigDict(extra="ignore")

    role: Role
    parts: List[Part] = Field(..., description="List of message parts that make up the message content.")
    name: Optional[str] = None


# --- Backward Compatibility ---


class FunctionCall(BaseModel):
    """Deprecated: Use ToolCallRequestPart instead."""

    name: str
    arguments: str


class ToolCall(BaseModel):
    """Deprecated: Use ToolCallRequestPart instead."""

    id: str
    type: str = "function"
    function: FunctionCall


Message = ChatMessage
