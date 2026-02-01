# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.base import CoReasonBaseModel

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


class TextPart(CoReasonBaseModel):
    """Represents text content sent to or received from the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["text"] = "text"
    content: str


class BlobPart(CoReasonBaseModel):
    """Represents blob binary data sent inline to the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["blob"] = "blob"
    content: str  # Base64 encoded string
    modality: Modality
    mime_type: Optional[str] = None


class FilePart(CoReasonBaseModel):
    """Represents an external referenced file sent to the model by file id."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["file"] = "file"
    file_id: str
    modality: Modality
    mime_type: Optional[str] = None


class UriPart(CoReasonBaseModel):
    """Represents an external referenced file sent to the model by URI."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["uri"] = "uri"
    uri: str
    modality: Modality
    mime_type: Optional[str] = None


class ToolCallRequestPart(CoReasonBaseModel):
    """Represents a tool call requested by the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["tool_call"] = "tool_call"
    name: str
    arguments: Union[Dict[str, Any], str]  # Structured arguments or JSON string
    id: Optional[str] = None

    @property
    def parsed_arguments(self) -> Dict[str, Any]:
        """Return arguments as a dictionary, parsing JSON if necessary."""
        if isinstance(self.arguments, dict):
            return self.arguments
        try:
            return json.loads(self.arguments)
        except (json.JSONDecodeError, TypeError):
            return {}


class ToolCallResponsePart(CoReasonBaseModel):
    """Represents a tool call result sent to the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["tool_call_response"] = "tool_call_response"
    response: Any  # The result of the tool call
    id: Optional[str] = None


class ReasoningPart(CoReasonBaseModel):
    """Represents reasoning/thinking content received from the model."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["reasoning"] = "reasoning"
    content: str


# --- Union of All Parts ---

Part = Annotated[
    Union[TextPart, BlobPart, FilePart, UriPart, ToolCallRequestPart, ToolCallResponsePart, ReasoningPart],
    Field(discriminator="type"),
]

# --- Main Message Model ---


class ChatMessage(CoReasonBaseModel):
    """Represents a message in a conversation with an LLM."""

    model_config = ConfigDict(extra="ignore")

    role: Role
    parts: List[Part] = Field(..., description="List of message parts that make up the message content.")
    name: Optional[str] = None

    @classmethod
    def user(cls, content: str, name: Optional[str] = None) -> "ChatMessage":
        """Factory method to create a user message with text content."""
        return cls(role=Role.USER, parts=[TextPart(content=content)], name=name)

    @classmethod
    def assistant(cls, content: str, name: Optional[str] = None) -> "ChatMessage":
        """Factory method to create an assistant message with text content."""
        return cls(role=Role.ASSISTANT, parts=[TextPart(content=content)], name=name)

    @classmethod
    def tool(cls, tool_call_id: str, content: Any) -> "ChatMessage":
        """Factory method to create a tool message with the result."""
        return cls(
            role=Role.TOOL, parts=[ToolCallResponsePart(id=tool_call_id, response=content)]
        )


# --- Backward Compatibility ---


class FunctionCall(CoReasonBaseModel):
    """Deprecated: Use ToolCallRequestPart instead."""

    name: str
    arguments: str


class ToolCall(CoReasonBaseModel):
    """Deprecated: Use ToolCallRequestPart instead."""

    id: str
    type: str = "function"
    function: FunctionCall


Message = ChatMessage
