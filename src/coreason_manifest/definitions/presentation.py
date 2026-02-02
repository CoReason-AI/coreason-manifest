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
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from pydantic import Field

from coreason_manifest.definitions.base import CoReasonBaseModel


class PresentationBlockType(str, Enum):
    """Enumeration of presentation block types."""
    THOUGHT = "THOUGHT"
    DATA = "DATA"
    MARKDOWN = "MARKDOWN"
    ERROR = "ERROR"


def _generate_uuid() -> str:
    return str(uuid4())


class PresentationBlock(CoReasonBaseModel):
    """Base model for all presentation blocks."""
    block_type: PresentationBlockType
    id: str = Field(default_factory=_generate_uuid)
    title: Optional[str] = None


class ThinkingBlock(PresentationBlock):
    """Presentation block for internal monologue and planning."""
    block_type: Literal[PresentationBlockType.THOUGHT] = PresentationBlockType.THOUGHT
    content: str
    status: Literal["IN_PROGRESS", "COMPLETE"] = "IN_PROGRESS"


class DataBlock(PresentationBlock):
    """Presentation block for structured data."""
    block_type: Literal[PresentationBlockType.DATA] = PresentationBlockType.DATA
    data: Dict[str, Any]
    view_hint: Literal["TABLE", "JSON", "LIST", "KEY_VALUE"] = "JSON"


class MarkdownBlock(PresentationBlock):
    """Presentation block for rich text content."""
    block_type: Literal[PresentationBlockType.MARKDOWN] = PresentationBlockType.MARKDOWN
    content: str


class UserErrorBlock(PresentationBlock):
    """Presentation block for user-facing errors."""
    block_type: Literal[PresentationBlockType.ERROR] = PresentationBlockType.ERROR
    user_message: str
    technical_details: Optional[Dict[str, Any]] = None
    recoverable: bool = False
