# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class LineageMetadata(CoReasonBaseModel):
    """Metadata for tracking request lineage across boundaries."""

    model_config = ConfigDict(frozen=True)

    root_request_id: str
    parent_interaction_id: str | None = None


class Interaction(CoReasonBaseModel):
    """External boundary interaction model."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    input: Any = None
    lineage: LineageMetadata | None = None


class MemoryStrategy(str, Enum):
    ALL = "all"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUFFER = "token_buffer"


class SessionState(CoReasonBaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    history: list[Interaction] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)

    def prune(self, strategy: MemoryStrategy, limit: int) -> "SessionState":
        """Prunes history based on strategy, returning a new instance."""
        if strategy == MemoryStrategy.ALL:
            return self

        new_history = self.history
        if strategy == MemoryStrategy.SLIDING_WINDOW:
            new_history = [] if limit <= 0 else self.history[-limit:]

            return self.model_copy(
                update={
                    "history": new_history,
                    "updated_at": datetime.now(),
                }
            )

        return self
