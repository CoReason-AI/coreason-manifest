# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable state differential schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from typing import Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type PatchOperation = Literal["add", "remove", "replace", "copy", "move", "test"]


class StatePatch(CoreasonBaseModel):
    op: PatchOperation = Field(
        description=("The strict RFC 6902 JSON Patch operation, acting as a deterministic state vector mutation.")
    )
    path: str = Field(description="The JSON pointer indicating the exact state vector to mutate deterministically.")
    value: Any | None = Field(
        default=None,
        description=("The payload to insert or test, if applicable, for this deterministic state vector mutation."),
    )


class StateDiff(CoreasonBaseModel):
    diff_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this state differential."
        )
    )
    author_node_id: str = Field(
        description=("The exact Lineage Watermark of the agent or system that authored this state mutation.")
    )
    lamport_timestamp: int = Field(
        ge=0,
        description="Strict scalar logical clock used for deterministic LWW (Last-Writer-Wins) conflict resolution.",
    )
    vector_clock: dict[str, int] = Field(
        description=(
            "Causal history mapping of all known Lineage Watermarks to their latest logical "
            "mutation count at the time of authoring."
        )
    )
    patches: list[StatePatch] = Field(
        default_factory=list, description=("The exact, ordered sequence of deterministic state vector mutations.")
    )


class TruthMaintenancePolicy(CoreasonBaseModel):
    decay_propagation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Entropy Penalty applied per edge traversal during a defeasible cascade.",
    )
    epistemic_quarantine_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "The minimum certainty boundary. If an event's propagated confidence drops "
            "below this threshold, it is legally quarantined."
        ),
    )
    enforce_cross_agent_quarantine: bool = Field(
        default=False,
        description=(
            "If True, the orchestrator must automatically emit global QuarantineOrders to sever "
            "infected SemanticEdges across the swarm to prevent epistemic contagion."
        ),
    )
    max_cascade_depth: int = Field(gt=0, description="The absolute recursion depth limit for state retractions.")
    max_quarantine_blast_radius: int = Field(
        gt=0, description="The maximum number of nodes allowed to be severed in a single defeasible event."
    )


class DefeasibleCascade(CoreasonBaseModel):
    cascade_id: str = Field(
        min_length=1,
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this "
            "automated truth maintenance operation."
        ),
    )
    root_falsified_event_id: str = Field(
        description=(
            "The source BeliefUpdateEvent or HypothesisGenerationEvent Content Identifier "
            "(CID) that collapsed and triggered this cascade."
        )
    )
    propagated_decay_factor: float = Field(
        ge=0.0, le=1.0, description="The calculated Entropy Penalty applied to this specific subgraph."
    )
    quarantined_event_ids: list[str] = Field(
        min_length=1,
        description=(
            "The strict list of downstream event Content Identifiers (CIDs) isolated and "
            "muted by this cascade to prevent Epistemic Contagion."
        ),
    )
    cross_boundary_quarantine_issued: bool = Field(
        default=False,
        description="Cryptographic proof that this cascade was broadcast to the Swarm to halt epistemic contagion.",
    )


class MigrationContract(CoreasonBaseModel):
    contract_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this "
            "structural migration mapping."
        )
    )
    source_version: str = Field(description="The exact semantic version string of the payload before migration.")
    target_version: str = Field(description="The exact semantic version string of the payload after migration.")
    path_transformations: dict[str, str] = Field(
        default_factory=dict, description="A strict mapping of old RFC 6902 JSON Pointers to new JSON Pointers."
    )
    dropped_paths: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit whitelist of JSON Pointers that are safely deprecated and intentionally dropped during migration."
        ),
    )


class RollbackRequest(CoreasonBaseModel):
    request_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the causal rollback operation."
        )
    )
    target_event_id: str = Field(
        description=("The Content Identifier (CID) of the corrupted event in the EpisodicTraceMemory to revert to.")
    )
    invalidated_node_ids: list[str] = Field(
        default_factory=list,
        description="A list of nodes whose operational histories are causally tainted and must be flushed.",
    )

    @model_validator(mode="after")
    def sort_invalidated_nodes(self) -> Self:
        object.__setattr__(self, "invalidated_node_ids", sorted(self.invalidated_node_ids))
        return self


class TemporalCheckpoint(CoreasonBaseModel):
    checkpoint_id: str = Field(
        description=("A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the temporal anchor.")
    )
    ledger_index: int = Field(
        description="The exact array index in the EpisodicTraceMemory this checkpoint represents."
    )
    state_hash: str = Field(
        description="The canonical RFC 8785 SHA-256 hash of the entire topology at this exact index."
    )
