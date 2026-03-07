# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

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
    active_steering_vector_hash: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the specific Representation Engineering control vector "
        "applied to the residual stream.",
    )
