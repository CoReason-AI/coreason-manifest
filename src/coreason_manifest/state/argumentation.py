# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable argumentation schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel

type AttackVector = Literal["rebuttal", "undercutter", "underminer"]


class EvidentiaryWarrant(CoreasonBaseModel):
    source_event_id: str | None = Field(
        default=None, description="A link to a specific observation in the EpistemicLedger."
    )
    source_semantic_node_id: str | None = Field(
        default=None, description="A link to a specific concept in the Semantic Knowledge Graph."
    )
    justification: str = Field(description="The logical premise explaining why this evidence supports the claim.")


class ArgumentClaim(CoreasonBaseModel):
    claim_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this "
            "specific logical proposition."
        )
    )
    proponent_id: str = Field(description="The NodeID of the agent or system that advanced this claim.")
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
    source_claim_id: str = Field(description="The Content Identifier (CID) of the claim mounting the attack.")
    target_claim_id: str = Field(description="The Content Identifier (CID) of the claim being attacked.")
    attack_vector: AttackVector = Field(
        description="The specific defeasible logic vector (e.g., attacking the premise, the link, or the conclusion)."
    )


class ArgumentGraph(CoreasonBaseModel):
    claims: dict[str, ArgumentClaim] = Field(
        max_length=10000, description="A registry of all active claims, keyed by claim_id."
    )
    attacks: dict[str, DefeasibleAttack] = Field(
        default_factory=dict,
        max_length=10000,
        description="A registry of all directed attack edges, keyed by attack_id.",
    )
