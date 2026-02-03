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

from coreason_manifest.definitions.base import CoReasonBaseModel
from coreason_manifest.definitions.events import GraphEvent
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.message import MultiModalInput


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

    session_id: UUID = Field(..., description="Global identifier for the conversation thread")
    processor: Identity = Field(..., description="The agent/graph handling this session")
    user: Optional[Identity] = Field(None, description="The user participating in the session")
    created_at: datetime = Field(..., description="When the session was created")
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
