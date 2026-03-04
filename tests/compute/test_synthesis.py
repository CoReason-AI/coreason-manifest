# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.compute.synthesis import (
    ContinuousSelfPlayConfig,
    EphemeralAdapterManifest,
    RLRewardCompiler,
)
from coreason_manifest.core.common.semantic import OptimizationIntent


def test_rl_reward_compiler_valid() -> None:
    """Test that RLRewardCompiler validates successfully with correct data."""
    optimization = OptimizationIntent(
        improvement_goal="Reduce hallucinations",
        metric_name="faithfulness",
        teacher_model="gpt-4",
        max_demonstrations=5,
    )

    compiler = RLRewardCompiler(
        base_optimization=optimization,
        target_metric_threshold=0.95,
        latency_penalty_weight=0.1,
        hallucination_penalty_weight=2.5,
        semantic_density_reward=1.2,
    )

    assert compiler.target_metric_threshold == 0.95
    assert compiler.hallucination_penalty_weight == 2.5
    assert compiler.base_optimization.improvement_goal == "Reduce hallucinations"


def test_rl_reward_compiler_invalid_threshold() -> None:
    """Test that RLRewardCompiler raises ValidationError when target_metric_threshold is out of bounds."""
    optimization = OptimizationIntent(
        improvement_goal="Maximize throughput",
        metric_name="accuracy",
    )

    with pytest.raises(ValidationError, match=r"target_metric_threshold must be between 0\.0 and 1\.0"):
        RLRewardCompiler(
            base_optimization=optimization,
            target_metric_threshold=1.5,  # Invalid
            latency_penalty_weight=0.1,
            hallucination_penalty_weight=2.5,
            semantic_density_reward=1.2,
        )

    with pytest.raises(ValidationError, match=r"target_metric_threshold must be between 0\.0 and 1\.0"):
        RLRewardCompiler(
            base_optimization=optimization,
            target_metric_threshold=-0.1,  # Invalid
            latency_penalty_weight=0.1,
            hallucination_penalty_weight=2.5,
            semantic_density_reward=1.2,
        )


def test_continuous_self_play_config_valid() -> None:
    """Test that ContinuousSelfPlayConfig validates successfully with correct data."""
    config = ContinuousSelfPlayConfig(
        sleep_cycle_cron="0 2 * * *",
        teacher_model_uri="frontier-model-v1",
        synthetic_edge_case_budget=1000,
        mutation_temperature=1.0,
    )

    assert config.sleep_cycle_cron == "0 2 * * *"
    assert config.mutation_temperature == 1.0


def test_continuous_self_play_config_invalid_temperature() -> None:
    """Test that ContinuousSelfPlayConfig raises ValidationError when mutation_temperature is out of bounds."""
    with pytest.raises(ValidationError, match=r"mutation_temperature must be between 0\.0 and 2\.0"):
        ContinuousSelfPlayConfig(
            sleep_cycle_cron="0 2 * * *",
            teacher_model_uri="frontier-model-v1",
            synthetic_edge_case_budget=1000,
            mutation_temperature=2.5,  # Invalid
        )

    with pytest.raises(ValidationError, match=r"mutation_temperature must be between 0\.0 and 2\.0"):
        ContinuousSelfPlayConfig(
            sleep_cycle_cron="0 2 * * *",
            teacher_model_uri="frontier-model-v1",
            synthetic_edge_case_budget=1000,
            mutation_temperature=-0.1,  # Invalid
        )


def test_ephemeral_adapter_manifest_valid() -> None:
    """Test that EphemeralAdapterManifest validates successfully with correct data."""
    manifest = EphemeralAdapterManifest(
        adapter_hash="a3f4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4",
        base_model_uri="base-model-v2",
        ttl_seconds=3600,
        training_steps_taken=150,
    )

    assert manifest.adapter_hash.startswith("a3f4b5c")
    assert manifest.ttl_seconds == 3600
    assert manifest.training_steps_taken == 150
