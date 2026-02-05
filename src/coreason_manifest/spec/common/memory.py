# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Self

from pydantic import ConfigDict, Field, model_validator

from ..common_base import CoReasonBaseModel
from .session import MemoryStrategy


class MemoryConfig(CoReasonBaseModel):
    """Configuration for agent memory and eviction policies."""

    model_config = ConfigDict(frozen=True)

    strategy: MemoryStrategy = Field(default=MemoryStrategy.SLIDING_WINDOW, description="Eviction strategy.")
    limit: int = Field(..., gt=0, description="The 'N' parameter (turns or tokens).")
    summary_prompt: str | None = Field(None, description="Instructions for summarization if strategy is SUMMARY.")

    @model_validator(mode="after")
    def validate_summary_strategy(self) -> Self:
        """Ensure summary_prompt is present if strategy is SUMMARY."""
        if self.strategy == MemoryStrategy.SUMMARY and not self.summary_prompt:
            raise ValueError("summary_prompt is required when strategy is SUMMARY")
        return self
