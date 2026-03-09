# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable argumentation schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
monotonic logic, standard CRUD database paradigms, or kinetic execution parameters. These models represent computable
geometric graphs of cognition and causal inference."""

import math
from typing import Literal

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID

type AttackVector = Literal["rebuttal", "undercutter", "underminer"]


class EvidentiaryWarrant(CoreasonBaseModel):
    source_event_id: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for a specific "
        "observation in the EpistemicLedger.",
    )
    source_semantic_node_id: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for a specific "
        "concept in the Semantic Knowledge Graph.",
    )
    justification: str = Field(description="The logical premise explaining why this evidence supports the claim.")


class ArgumentClaim(CoreasonBaseModel):
    claim_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this "
            "specific logical proposition."
        )
    )
    proponent_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the agent or "
        "system that advanced this claim."
    )
    text_chunk: str = Field(max_length=50000, description="The natural language representation of the proposition.")
    warrants: list[EvidentiaryWarrant] = Field(
        default_factory=list, description="The foundational premises supporting this claim."
    )


class DefeasibleAttack(CoreasonBaseModel):
    attack_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this directed attack edge."
        )
    )
    source_claim_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the claim "
        "mounting the attack."
    )
    target_claim_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the claim "
        "being attacked."
    )
    attack_vector: AttackVector = Field(description="Geometric matrices of undercutting defeaters.")


class ArgumentGraph(CoreasonBaseModel):
    """A Truth Maintenance System (TMS) calculating dialectical justification for non-monotonic belief retraction."""

    claims: dict[str, ArgumentClaim] = Field(
        max_length=10000, description="Components of an Abstract Argumentation Framework."
    )
    attacks: dict[str, DefeasibleAttack] = Field(
        default_factory=dict,
        max_length=10000,
        description="Geometric matrices of undercutting defeaters.",
    )


class EnsembleTopologySpec(CoreasonBaseModel):
    """
    AGENT INSTRUCTION: Declarative mapping of concurrent topology branches for test-time superposition.
    Must map to strict W3C DIDs (NodeIDs) and provide an explicit wave-collapse opcode.
    """

    concurrent_branch_ids: list[NodeID] = Field(..., min_length=2)
    fusion_function: Literal["weighted_consensus", "highest_confidence", "brier_score_collapse"]


class UtilityJustificationGraph(CoreasonBaseModel):
    """
    AGENT INSTRUCTION: Immutable cryptographic receipt of multi-dimensional utility routing.
    If variance threshold falls below delta, fallback to deterministic ensemble superposition.
    """

    optimizing_vectors: dict[str, float] = Field(default_factory=dict)
    degrading_vectors: dict[str, float] = Field(default_factory=dict)
    superposition_variance_threshold: float = Field(..., ge=0.0, allow_inf_nan=False)
    ensemble_spec: EnsembleTopologySpec | None = None

    @model_validator(mode="after")
    def _enforce_mathematical_interlocks(self) -> "UtilityJustificationGraph":
        # Constraint 1: Superposition Escrow
        if self.ensemble_spec is not None and self.superposition_variance_threshold == 0.0:
            raise ValueError(
                "Topological Interlock Failed: ensemble_spec defined but variance threshold is 0.0. "
                "Mathematical certainty prohibits superposition."
            )

        # Constraint 2: NaN / Inf Purge on Vectors
        for vectors in (self.optimizing_vectors, self.degrading_vectors):
            for key, val in vectors.items():
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Tensor Poisoning Detected: Vector '{key}' contains invalid float {val}.")

        return self
