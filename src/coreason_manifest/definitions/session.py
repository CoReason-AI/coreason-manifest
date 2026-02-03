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
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel
from coreason_manifest.definitions.events import GraphEvent
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.memory import MemoryStrategy
from coreason_manifest.definitions.message import MultiModalInput


class UserContext(CoReasonBaseModel):
    """Immutable context about the user associated with a session."""

    model_config = ConfigDict(frozen=True)

    user_id: str = Field(..., description="The stable ID of the user")
    email: Optional[str] = Field(None, description="User email address")
    tier: str = Field(..., description="User tier (e.g., free, pro)")
    locale: str = Field(..., description="User locale (e.g., en-US)")


class TraceContext(CoReasonBaseModel):
    """Immutable distributed tracing context."""

    model_config = ConfigDict(frozen=True)

    trace_id: UUID = Field(..., description="Global distributed trace ID")
    span_id: UUID = Field(..., description="Current span ID")
    parent_id: Optional[UUID] = Field(None, description="Parent span ID")


class SessionContext(CoReasonBaseModel):
    """Immutable context accompanying a session request."""

    model_config = ConfigDict(frozen=True)

    session_id: UUID = Field(..., description="Unique session identifier")
    agent_id: UUID = Field(..., description="The specific agent instance being invoked")
    user: UserContext = Field(..., description="User context")
    trace: TraceContext = Field(..., description="Tracing context")
    permissions: List[str] = Field(..., description="Scopes granted for this specific run")
    created_at: datetime = Field(..., description="When the session context was created")


class LineageMetadata(CoReasonBaseModel):
    """Metadata tracking the Chain of Custody for this interaction."""

    model_config = ConfigDict(frozen=True)

    root_request_id: Optional[str] = Field(
        None, description="The ID of the original request that started the entire chain"
    )
    parent_interaction_id: Optional[str] = Field(
        None, description="The ID of the specific interaction that triggered this one"
    )


class Interaction(CoReasonBaseModel):
    """Represents a single 'turn' or request/response cycle in a session."""

    model_config = ConfigDict(frozen=True)

    interaction_id: UUID = Field(default_factory=uuid4, description="Unique ID for this turn")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the interaction (UTC)"
    )
    input: Union[MultiModalInput, Dict[str, Any]] = Field(..., description="The raw input payload")
    output: Dict[str, Any] = Field(..., description="The final output payload")
    events: List[GraphEvent] = Field(
        default_factory=list, description="A log of intermediate events emitted during this turn"
    )
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata (Latency, cost, model used, etc.)")
    lineage: Optional[LineageMetadata] = Field(None, description="Chain of Custody metadata")


class SessionState(CoReasonBaseModel):
    """The portable object that contains the entire conversation history and user context."""

    model_config = ConfigDict(frozen=True)

    context: SessionContext = Field(..., description="Immutable context for the session")
    processor: Identity = Field(..., description="The agent/graph handling this session")
    last_updated_at: datetime = Field(..., description="When the session was last updated")
    history: List[Interaction] = Field(default_factory=list, description="Chronological list of interactions")
    context_variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="A 'scratchpad' for long-term memory or variables that persist across turns",
    )

    def add_interaction(self, interaction: Interaction) -> "SessionState":
        """Appends a new Interaction to the history and returns a new SessionState."""
        new_history = list(self.history)
        new_history.append(interaction)
        return self.model_copy(
            update={
                "history": new_history,
                "last_updated_at": datetime.now(timezone.utc),
            }
        )

    def prune(self, strategy: MemoryStrategy, limit: int) -> "SessionState":
        """Prunes the session history based on the given strategy and limit.

        Args:
            strategy: The memory strategy to use.
            limit: The limit for the strategy.

        Returns:
            A new SessionState with pruned history.
        """
        if strategy == MemoryStrategy.SLIDING_WINDOW:
            if limit <= 0:
                new_history = []
            else:
                new_history = self.history[-limit:]
            return self.model_copy(update={"history": new_history})
        else:
            raise NotImplementedError(
                "Kernel only supports SLIDING_WINDOW pruning. Complex strategies require an Engine."
            )
