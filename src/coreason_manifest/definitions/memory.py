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

from coreason_manifest.definitions.base import CoReasonBaseModel


class MemoryStrategy(str, Enum):
    """Strategy for memory management."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUFFER = "token_buffer"
    SUMMARY = "summary"
    VECTOR_STORE = "vector_store"


class MemoryConfig(CoReasonBaseModel):
    """Configuration for memory management.

    Attributes:
        strategy: The strategy to use for memory management.
        limit: The limit for the strategy (e.g., number of turns for SLIDING_WINDOW).
        summary_prompt: Instructions for the summarizer (if strategy is SUMMARY).
    """

    model_config = ConfigDict(frozen=True)

    strategy: MemoryStrategy = Field(
        default=MemoryStrategy.SLIDING_WINDOW, description="The strategy to use for memory management."
    )
    limit: int = Field(default=20, description="The limit for the strategy (e.g., number of turns).")
    summary_prompt: Optional[str] = Field(
        None, description="Instructions for the summarizer (e.g., 'Focus on user preferences')."
    )
