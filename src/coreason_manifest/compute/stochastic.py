# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type DistributionType = Literal["gaussian", "uniform", "beta"]
type OptimizationDirection = Literal["maximize", "minimize"]
type CrossoverType = Literal["uniform_blend", "single_point", "heuristic"]


class DistributionProfile(CoreasonBaseModel):
    """Profile defining a probability density function."""

    distribution_type: DistributionType = Field(
        description="The mathematical shape of the probability density function."
    )
    mean: float | None = Field(default=None, description="The expected value (mu) of the distribution.")
    variance: float | None = Field(default=None, description="The mathematical variance (sigma squared).")
    confidence_interval_95: tuple[float, float] | None = Field(default=None, description="The 95% probability bounds.")

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> Any:
        if self.confidence_interval_95 is not None and self.confidence_interval_95[0] >= self.confidence_interval_95[1]:
            raise ValueError("confidence_interval_95 must have interval[0] < interval[1]")
        return self


class FitnessObjective(CoreasonBaseModel):
    """A specific objective function to optimize within a generation."""

    target_metric: str = Field(
        description="The specific telemetry or execution metric to evaluate (e.g., 'latency', 'accuracy')."
    )
    direction: OptimizationDirection = Field(
        description="Whether the algorithm should maximize or minimize this metric."
    )
    weight: float = Field(
        default=1.0, description="The relative importance of this objective in a multi-objective generation."
    )


class VerifiableEntropy(CoreasonBaseModel):
    """Passive cryptographic envelope for verifiable random functions."""

    vrf_proof: str = Field(
        min_length=10, description="The zero-knowledge cryptographic proof of fair random generation."
    )
    public_key: str = Field(
        min_length=10, description="The public key of the oracle or node used to verify the VRF proof."
    )
    seed_hash: str = Field(min_length=10, description="The SHA-256 hash of the origin seed used to initialize the VRF.")


class MutationPolicy(CoreasonBaseModel):
    """Constraints governing random heuristic mutations."""

    mutation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="The probability that a given agent parameter will randomly mutate between generations.",
    )
    temperature_shift_variance: float = Field(
        description="The maximum allowed delta for an agent's temperature during mutation."
    )
    verifiable_entropy: VerifiableEntropy | None = Field(
        default=None, description="The cryptographic envelope proving the fairness of the applied mutation rate."
    )


class CrossoverStrategy(CoreasonBaseModel):
    """The mathematical rules for combining elite agents."""

    strategy_type: CrossoverType = Field(description="The heuristic method for blending successful parent agents.")
    blending_factor: float = Field(
        ge=0.0, le=1.0, description="The proportional mix ratio when merging vector properties."
    )
    verifiable_entropy: VerifiableEntropy | None = Field(
        default=None, description="The cryptographic envelope proving the fairness of the applied crossover logic."
    )
