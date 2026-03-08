# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable memory schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or kinetic execution parameters. All memory must be modeled as an
append-only, content-addressable Merkle-DAG. Focus purely on cryptographic event sourcing, hardware attestations,
and non-monotonic belief assertions and retractions."""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.state.argumentation import ArgumentGraph
from coreason_manifest.state.differentials import (
    DefeasibleCascade,
    MigrationContract,
    RollbackRequest,
    TemporalCheckpoint,
    TruthMaintenancePolicy,
)
from coreason_manifest.state.events import AnyStateEvent


class EvictionPolicy(CoreasonBaseModel):
    strategy: Literal["fifo", "salience_decay", "summarize"] = Field(
        description="The mathematical heuristic used to select which semantic memories are retracted or compressed."
    )
    max_retained_tokens: int = Field(
        gt=0, description="The strict geometric upper bound of the Epistemic Quarantine's token capacity."
    )
    protected_event_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit list of Content Identifiers (CIDs) the orchestrator is mathematically forbidden from retracting."
        ),
    )


class EpistemicLedger(CoreasonBaseModel):
    """The Committed Epistemic Ledger (crystallized truth), completely partitioned from volatile working memory
    or Epistemic Quarantine."""

    history: list[AnyStateEvent] = Field(
        max_length=10000, description="An append-only, cryptographic ledger of state events."
    )
    checkpoints: list[TemporalCheckpoint] = Field(
        default_factory=list, description="Hard temporal anchors allowing state restoration."
    )
    active_rollbacks: list[RollbackRequest] = Field(
        default_factory=list, description="Causal invalidations actively enforced on the execution tree."
    )
    eviction_policy: EvictionPolicy | None = Field(
        default=None,
        description="The strict mathematical boundary governing context window compression.",
    )
    migration_contracts: list[MigrationContract] = Field(
        default_factory=list,
        description="Declarative rules to translate historical states to the current active schema version.",
    )
    truth_maintenance_policy: TruthMaintenancePolicy | None = Field(
        default=None,
        description="The mathematical contract governing automated causal graph ablations and probabilistic decay.",
    )
    active_cascades: list[DefeasibleCascade] = Field(
        default_factory=list,
        description="The active state-differential payload muting specific causal subgraphs due to falsification.",
    )

    @model_validator(mode="after")
    def sort_history(self) -> Self:
        object.__setattr__(self, "history", sorted(self.history, key=lambda event: event.timestamp))
        return self


class TheoryOfMindSnapshot(CoreasonBaseModel):
    target_agent_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the agent whose mind is being modeled.",
    )
    assumed_shared_beliefs: list[str] = Field(
        description="A list of Content Identifiers (CIDs) acting as cryptographic Lineage Watermarks "
        "that the modeling agent assumes the target already possesses."
    )
    identified_knowledge_gaps: list[str] = Field(
        description="Specific topics or logical premises the target agent is assumed to be missing."
    )
    empathy_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical confidence (0.0 to 1.0) the agent has in its model of the target's mind.",
    )


class WorkingMemorySnapshot(CoreasonBaseModel):
    """Represents the Epistemic Quarantine, partitioned from the Committed Epistemic Ledger."""

    system_prompt: str = Field(
        description="The basal non-monotonic instruction set currently held in Epistemic Quarantine."
    )
    active_context: dict[str, str] = Field(
        description="The ephemeral latent variables and environmental bindings currently active "
        "in Epistemic Quarantine."
    )
    argumentation: ArgumentGraph | None = Field(
        default=None,
        description=(
            "The formal graph of non-monotonic claims and defeasible "
            "attacks currently active in the swarm's working memory."
        ),
    )
    theory_of_mind_models: list[TheoryOfMindSnapshot] = Field(
        default_factory=list,
        description="Empathetic models of other agents to compress and target outgoing communications.",
    )


class FederatedStateSnapshot(CoreasonBaseModel):
    topology_id: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the federated topology, if applicable.",
    )
