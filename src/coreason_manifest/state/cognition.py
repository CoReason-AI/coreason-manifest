# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable cognitive schemas. This is a STRICTLY EPISTEMIC BOUNDARY.

These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from pydantic import Field

from coreason_manifest.compute.neuromodulation import ActivationSteeringContract, CognitiveRoutingDirective
from coreason_manifest.core.base import CoreasonBaseModel


class CognitiveUncertaintyProfile(CoreasonBaseModel):
    aleatoric_entropy: float = Field(
        ge=0.0, le=1.0, description="Irreducible ambiguity detected in the input task or environment."
    )
    epistemic_uncertainty: float = Field(
        ge=0.0, le=1.0, description="The model's internal lack of knowledge, calculated via semantic disagreement."
    )
    semantic_consistency_score: float = Field(
        ge=0.0, le=1.0, description="The degree to which multiple sampled latent thoughts align on the same conclusion."
    )
    requires_abductive_escalation: bool = Field(
        description="True if epistemic_uncertainty breaches the safety threshold, requiring System 2 test-time compute."
    )


class CognitiveStateProfile(CoreasonBaseModel):
    urgency_index: float = Field(
        ge=0.0, le=1.0, description="Drives latency requirements; high urgency forces fast, heuristic System 1 routing."
    )
    caution_index: float = Field(
        ge=0.0, le=1.0, description="Drives precision; high caution injects analytical/falsification steering vectors."
    )
    divergence_tolerance: float = Field(
        ge=0.0,
        le=1.0,
        description="The 'curiosity' metric; dictates how far the MoE router is allowed to stray "
        "from high-probability distributions.",
    )
    activation_steering: ActivationSteeringContract | None = Field(
        default=None,
        description="The precise mathematical contract for altering the LLM's residual stream to enforce this mood.",
    )
    moe_routing_directive: CognitiveRoutingDirective | None = Field(
        default=None,
        description="The physical hardware mandate overriding default MoE token routing to "
        "enforce this cognitive state.",
    )
