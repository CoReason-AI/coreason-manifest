# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""
Synthesis Module

This module defines the data contracts for how an agent is algorithmically bootstrapped,
evaluated, and iteratively improved over time within the 2026 Autonomous Agent Synthesis architecture.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from coreason_manifest.core.common.semantic import OptimizationIntent


class RLRewardCompiler(BaseModel):
    """
    A schema linking an OptimizationIntent to specific judge evaluation weights.
    This replaces manual prompt tuning with Reinforcement Learning targets for autonomous agent synthesis.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    base_optimization: OptimizationIntent = Field(..., description="The OptimizationIntent this compiler targets.")
    target_metric_threshold: float = Field(
        ..., description="The minimum acceptable score (0.0 to 1.0) before an agent is considered 'compiled'."
    )
    latency_penalty_weight: float = Field(..., description="Multiplier for penalizing slow generation.")
    hallucination_penalty_weight: float = Field(..., description="Multiplier for penalizing factual deviations.")
    semantic_density_reward: float = Field(
        ..., description="Multiplier for rewarding concise, high-information outputs."
    )

    @field_validator("target_metric_threshold")
    @classmethod
    def check_threshold(cls, v: float) -> float:
        """Ensure target_metric_threshold is between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("target_metric_threshold must be between 0.0 and 1.0")
        return v


class ContinuousSelfPlayConfig(BaseModel):
    """
    A schema defining the boundaries for background idle compute (when the system tests agents against
    synthetic edge cases) in the autonomous self-play loops.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    sleep_cycle_cron: str = Field(
        ..., description="Standard cron expression defining when self-play is allowed (e.g., '0 2 * * *')."
    )
    teacher_model_uri: str = Field(
        ..., description="The identifier of the frontier model generating the synthetic test cases."
    )
    synthetic_edge_case_budget: int = Field(..., description="Maximum number of test scenarios generated per cycle.")
    mutation_temperature: float = Field(
        ...,
        description="How aggressively the teacher model mutates instructions upon failure (between 0.0 and 2.0).",
    )

    @field_validator("mutation_temperature")
    @classmethod
    def check_mutation_temperature(cls, v: float) -> float:
        """Ensure mutation_temperature is between 0.0 and 2.0 inclusive."""
        if not (0.0 <= v <= 2.0):
            raise ValueError("mutation_temperature must be between 0.0 and 2.0")
        return v


class EphemeralAdapterManifest(BaseModel):
    """
    A schema representing the output of a successful synthesis loop-a Just-In-Time
    compiled LoRA (Low-Rank Adaptation) adapter.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    adapter_hash: str = Field(..., description="A unique SHA-256 hash identifying the specific learned weights.")
    base_model_uri: str = Field(..., description="The underlying model this adapter attaches to.")
    ttl_seconds: int = Field(..., description="Time-to-live before this specialized adapter is purged from memory.")
    training_steps_taken: int = Field(
        ..., description="The number of synthetic iterations required to reach the target_metric_threshold."
    )


__all__ = [
    "ContinuousSelfPlayConfig",
    "EphemeralAdapterManifest",
    "RLRewardCompiler",
]
