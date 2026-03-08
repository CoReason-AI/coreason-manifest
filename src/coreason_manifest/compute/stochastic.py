# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file contains the stochastic schemas for logit steganography, verifiable entropy,
mutation policies, and continuous distribution profiles. This is a STRICTLY KINETIC BOUNDARY. These schemas
represent friction, hardware limits, and physical execution. This boundary governs probabilistic tensor
logic, VRAM geometries, and exogenous spatial actuation.
"""

from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type DistributionType = Literal["gaussian", "uniform", "beta"]
type OptimizationDirection = Literal["maximize", "minimize"]
type CrossoverType = Literal["uniform_blend", "single_point", "heuristic"]


class DistributionProfile(CoreasonBaseModel):
    """Profile defining a probability density function."""

    distribution_type: DistributionType = Field(
        description="The mathematical shape of the probability density function for probabilistic tensor logic."
    )
    mean: float | None = Field(
        default=None,
        description="The expected value (mu) of the distribution bounding physical execution.",
    )
    variance: float | None = Field(
        default=None,
        description="The mathematical variance (sigma squared) of the execution bounds.",
    )
    confidence_interval_95: tuple[float, float] | None = Field(
        default=None,
        description="The 95% probabilistic execution bounds.",
    )

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> Any:
        if self.confidence_interval_95 is not None and self.confidence_interval_95[0] >= self.confidence_interval_95[1]:
            raise ValueError("confidence_interval_95 must have interval[0] < interval[1]")
        return self


class FitnessObjective(CoreasonBaseModel):
    """A specific objective function to optimize within a generation."""

    target_metric: str = Field(
        description="The specific telemetry or execution metric to evaluate (e.g., 'latency', 'accuracy') "
        "governed by hardware limits."
    )
    direction: OptimizationDirection = Field(
        description="Whether the algorithm should maximize or minimize this metric bounded by VRAM geometries."
    )
    weight: float = Field(
        default=1.0,
        description="The relative importance of this objective in a multi-objective generation "
        "dictating tensor routing.",
    )


class VerifiableEntropy(CoreasonBaseModel):
    """Passive cryptographic envelope for verifiable random functions."""

    vrf_proof: str = Field(
        min_length=10,
        description="The zero-knowledge cryptographic proof of fair random generation "
        "ensuring probabilistic tensor logic boundaries.",
    )
    public_key: str = Field(
        min_length=10,
        description="The public key of the oracle or node used to verify the VRF proof bounded by physical execution.",
    )
    seed_hash: str = Field(
        min_length=10,
        description="The SHA-256 hash of the origin seed used to initialize the VRF for exogenous spatial actuation.",
    )


class LogitSteganographyContract(CoreasonBaseModel):
    """Cryptographic contract for embedding undeniable, un-strippable provenance signatures
    directly into the token entropy."""

    verification_public_key_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "required by an auditor to reconstruct the PRF and verify the watermark."
    )
    prf_seed_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the cryptographic seed used to initialize the pseudo-random function (PRF).",
    )
    watermark_strength_delta: float = Field(
        gt=0.0,
        description="The exact logit scalar (bias) injected into the 'green list' vocabulary partition "
        "before Gumbel-Softmax sampling.",
    )
    target_bits_per_token: float = Field(
        gt=0.0,
        description="The information-theoretic density of the payload being embedded into the generative stream.",
    )
    context_history_window: int = Field(
        ge=0,
        description="The k-gram rolling window size of preceding tokens hashed into the PRF state "
        "to ensure robustness against text cropping.",
    )


class MutationPolicy(CoreasonBaseModel):
    """Constraints governing random heuristic mutations."""

    mutation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="The probabilistic execution bounds that a given agent parameter will "
        "randomly mutate between generations.",
    )
    temperature_shift_variance: float = Field(
        description="The maximum allowed delta for an agent's probabilistic tensor routing during mutation."
    )
    verifiable_entropy: VerifiableEntropy | None = Field(
        default=None,
        description="The cryptographic envelope proving the fairness of the applied mutation rate "
        "across VRAM geometries.",
    )


class CrossoverStrategy(CoreasonBaseModel):
    """The mathematical rules for combining elite agents."""

    strategy_type: CrossoverType = Field(
        description="The heuristic method for blending successful parent agents across execution bounds."
    )
    blending_factor: float = Field(
        ge=0.0,
        le=1.0,
        description="The proportional mix ratio when merging vector properties across VRAM geometries.",
    )
    verifiable_entropy: VerifiableEntropy | None = Field(
        default=None,
        description="The cryptographic envelope proving the fairness of the applied crossover logic "
        "bounded by physical execution.",
    )
