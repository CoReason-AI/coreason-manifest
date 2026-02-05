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
from typing import Optional

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel


class MemoryStrategy(str, Enum):
    """Strategy for memory eviction."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUFFER = "token_buffer"
    SUMMARY = "summary"
    VECTOR_STORE = "vector_store"


class MemoryConfig(CoReasonBaseModel):
    """Configuration for agent memory and eviction policies."""

    model_config = ConfigDict(frozen=True)

    strategy: MemoryStrategy = Field(
        default=MemoryStrategy.SLIDING_WINDOW, description="Eviction strategy."
    )
    limit: int = Field(..., description="The 'N' parameter (turns or tokens).")
    summary_prompt: Optional[str] = Field(
        None, description="Instructions for summarization if strategy is SUMMARY."
    )
