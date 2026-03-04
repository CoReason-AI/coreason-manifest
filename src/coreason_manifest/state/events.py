from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


@runtime_checkable
class ContextEnvelopeProtocol(Protocol):
    """
    Mock protocol for external telemetry envelopes representing hardware,
    prompt version, agent signature, etc.
    """

    hardware_cluster: str
    agent_signature: str
    prompt_version: str


class EventType(StrEnum):
    """
    The type of epistemic event occurring in the system.
    """

    STRUCTURAL_PARSED = "STRUCTURAL_PARSED"
    SEMANTIC_EXTRACTED = "SEMANTIC_EXTRACTED"
    GRAPH_RETRIEVAL_TRACE = "GRAPH_RETRIEVAL_TRACE"
    # Other event types can be added here


class GraphRetrievalTrace(CoreasonModel):
    """
    A cryptographic trace linking a semantic traversal request to its topological response.
    """

    traversal_request_hash: str = Field(..., description="SHA-256 of the semantic request.")
    subgraph_topology_hash: str = Field(..., description="SHA-256 of the returned normalized subgraph.")
    nodes_retrieved_count: int = Field(..., description="Number of nodes returned.")
    edges_retrieved_count: int = Field(..., description="Number of edges returned.")


class EpistemicAnchor(CoreasonModel):
    """
    A reference to maintain the Chain of Custody.
    """

    parent_event_id: str | None = Field(
        default=None, description="The ID of the parent event that caused this event, if any."
    )
    spatial_coordinates: list[float] | None = Field(
        default=None, description="Bounding box coordinates (e.g., [x1, y1, x2, y2]) to anchor to a specific region."
    )


class EpistemicEvent(CoreasonModel):
    """
    An immutable event appended to the ledger representing a state mutation.
    """

    event_id: str = Field(..., description="A unique UUID/ULID for the event.")
    timestamp: datetime = Field(..., description="UTC datetime when the event occurred.")
    context_envelope: dict[str, Any] = Field(
        ..., description="A generic dict or Protocol representing hardware, prompt version, agent signature."
    )
    event_type: EventType = Field(..., description="The type of the event.")
    payload: dict[str, Any] | GraphRetrievalTrace = Field(..., description="The actual data mutation.")
    epistemic_anchor: EpistemicAnchor = Field(
        ..., description="A reference to the parent event and spatial coordinates."
    )

    @model_validator(mode="after")
    def validate_utc(self) -> "EpistemicEvent":
        """Ensure the timestamp is UTC."""
        if self.timestamp.tzinfo is None or self.timestamp.tzinfo != UTC:
            # We enforce UTC strictly for the distributed ledger
            raise ValueError("Timestamp must be timezone-aware and set to UTC.")
        return self
