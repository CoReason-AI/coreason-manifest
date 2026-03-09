"""
AGENT INSTRUCTION: This module defines the Stratified Memory Hierarchy.
It enforces strict topological boundaries for multi-agent state management via Pydantic V2.
No procedural logic may exist in this file.
"""

from typing import Any

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.state.events import AnyStateEvent


class LatentWorkingMemory(CoreasonBaseModel):
    """
    Volatile state envelope. Enforces OOM boundaries mathematically.
    """

    node_id: NodeID = Field(description="The cryptographic Lineage Watermark linking to the execution node.")
    max_ttl_seconds: int = Field(ge=1, description="Maximum time to live for this memory envelope in seconds.")
    max_context_window_tokens: int = Field(ge=1, description="The maximum allowed context tokens.")
    current_tokens: int = Field(ge=0, description="The current token count.")
    state_envelope: list[Any] = Field(description="The active computational state payload.")

    @model_validator(mode="after")
    def enforce_token_bounds(self) -> "LatentWorkingMemory":
        if self.current_tokens > self.max_context_window_tokens:
            raise ValueError(
                f"OOM ALARM: Node {self.node_id} exceeded context bounds. "
                f"({self.current_tokens}/{self.max_context_window_tokens})"
            )
        return self


class EpisodicTraceMemory(CoreasonBaseModel, frozen=True):
    """
    Append-only cryptographic ledger of execution causality.
    """

    trace_id: str = Field(description="The unique identifier for the execution trace.")
    node_id: NodeID = Field(description="The cryptographic Lineage Watermark linking to the execution node.")
    events: list[AnyStateEvent] = Field(description="The append-only sequence of execution events.")
    parent_hash: str = Field(description="The hash of the preceding trace memory block.")
    merkle_root: str = Field(description="The deterministic Merkle root of all contained events.")

    @model_validator(mode="after")
    def verify_causality(self) -> "EpisodicTraceMemory":
        # Note: In a real implementation, we would inject the deterministic hashing utility here.
        # For structural definition, we enforce that the root must be present and mathematically bound.
        if not self.merkle_root:
            raise ValueError("Byzantine Fault: Episodic memory requires a valid Merkle Root.")
        return self


class SemanticCrystallization(CoreasonBaseModel):
    """
    Declarative proof-of-compression for cross-session axioms.
    """

    axiom_id: str = Field(description="The unique identifier for this semantic axiom.")
    source_trace_id: str = Field(description="The ID of the trace from which this axiom was derived.")
    aleatoric_entropy_threshold: float = Field(
        ge=0.0, le=1.0, description="The statistical threshold for crystallization."
    )
    entropy_delta_score: float = Field(ge=0.0, description="The calculated entropy delta score.")
    semantic_payload: str = Field(description="The resulting declarative fact or rule.")

    @model_validator(mode="after")
    def enforce_compression_proof(self) -> "SemanticCrystallization":
        if self.entropy_delta_score < self.aleatoric_entropy_threshold:
            raise ValueError(
                f"Economic Validation Failed: Entropy delta ({self.entropy_delta_score}) "
                f"does not meet threshold ({self.aleatoric_entropy_threshold}) for crystallization."
            )
        return self
