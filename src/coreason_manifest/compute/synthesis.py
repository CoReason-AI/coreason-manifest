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

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.semantic import OptimizationIntent


class RLRewardCompiler(CoreasonModel):
    """
    A schema linking an OptimizationIntent to specific judge evaluation weights.
    This replaces manual prompt tuning with Reinforcement Learning targets for autonomous agent synthesis.
    """

    base_optimization: OptimizationIntent = Field(..., description="The OptimizationIntent this compiler targets.")
    target_metric_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The minimum acceptable score (0.0 to 1.0) before an agent is considered 'compiled'.",
    )
    latency_penalty_weight: float = Field(..., description="Multiplier for penalizing slow generation.")
    hallucination_penalty_weight: float = Field(..., description="Multiplier for penalizing factual deviations.")
    semantic_density_reward: float = Field(
        ..., description="Multiplier for rewarding concise, high-information outputs."
    )


class ContinuousSelfPlayConfig(CoreasonModel):
    """
    A schema defining the boundaries for background idle compute (when the system tests agents against
    synthetic edge cases) in the autonomous self-play loops.
    """

    sleep_cycle_cron: str = Field(
        ..., description="Standard cron expression defining when self-play is allowed (e.g., '0 2 * * *')."
    )
    teacher_model_uri: str = Field(
        ..., description="The identifier of the frontier model generating the synthetic test cases."
    )
    synthetic_edge_case_budget: int = Field(..., description="Maximum number of test scenarios generated per cycle.")
    mutation_temperature: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="How aggressively the teacher model mutates instructions upon failure (between 0.0 and 2.0).",
    )


class EphemeralAdapterManifest(CoreasonModel):
    """
    A schema representing the output of a successful synthesis loop-a Just-In-Time
    compiled LoRA (Low-Rank Adaptation) adapter.
    """

    adapter_hash: str = Field(..., description="A unique SHA-256 hash identifying the specific learned weights.")
    base_model_uri: str = Field(..., description="The underlying model this adapter attaches to.")
    ttl_seconds: int = Field(
        ..., gt=0, description="Time-to-live before this specialized adapter is purged from memory."
    )
    training_steps_taken: int = Field(
        ..., description="The number of synthetic iterations required to reach the target_metric_threshold."
    )


__all__ = [
    "ContinuousSelfPlayConfig",
    "EphemeralAdapterManifest",
    "RLRewardCompiler",
]
