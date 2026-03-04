import pytest
from pydantic import ValidationError

from coreason_manifest.compute.evolutionary_v2 import (
    CostAwareFitnessMetric,
    EvolutionaryReasoningTopology,
    HybridMCTSEvolutionConfig,
    ShadowPopulationConfig,
)


def test_hybrid_mcts_config_valid():
    config = HybridMCTSEvolutionConfig(
        population_limit=10,
        mcts_lookahead_depth=5,
        exploration_weight_c_puct=1.2,
        crossover_strategy="semantic_blend"
    )
    assert config.population_limit == 10
    assert config.crossover_strategy == "semantic_blend"


def test_hybrid_mcts_config_invalid_population_zero():
    with pytest.raises(ValueError, match="population_limit must be greater than 0"):
        HybridMCTSEvolutionConfig(
            population_limit=0,
            mcts_lookahead_depth=5,
            exploration_weight_c_puct=1.2,
            crossover_strategy="semantic_blend"
        )


def test_hybrid_mcts_config_invalid_population_negative():
    with pytest.raises(ValueError, match="population_limit must be greater than 0"):
        HybridMCTSEvolutionConfig(
            population_limit=-5,
            mcts_lookahead_depth=5,
            exploration_weight_c_puct=1.2,
            crossover_strategy="semantic_blend"
        )


def test_cost_aware_fitness_metric():
    metric = CostAwareFitnessMetric(
        base_reward_metric_uri="s3://metrics/acc.json",
        token_bloat_penalty=-0.01,
        latency_penalty_ms=-0.005,
        max_acceptable_cost_usd=5.0
    )
    assert metric.token_bloat_penalty == -0.01


def test_shadow_population_config_valid():
    config = ShadowPopulationConfig(
        background_mutation_rate=0.5,
        hot_swap_threshold=0.1,
        telemetry_feedback_sync=True
    )
    assert config.background_mutation_rate == 0.5


def test_shadow_population_config_invalid_mutation_high():
    with pytest.raises(ValueError, match="background_mutation_rate must be between 0.0 and 1.0"):
        ShadowPopulationConfig(
            background_mutation_rate=1.5,
            hot_swap_threshold=0.1,
            telemetry_feedback_sync=True
        )


def test_shadow_population_config_invalid_mutation_low():
    with pytest.raises(ValueError, match="background_mutation_rate must be between 0.0 and 1.0"):
        ShadowPopulationConfig(
            background_mutation_rate=-0.1,
            hot_swap_threshold=0.1,
            telemetry_feedback_sync=True
        )


def test_evolutionary_reasoning_topology_instantiation():
    mcts_config = HybridMCTSEvolutionConfig(
        population_limit=10,
        mcts_lookahead_depth=3,
        exploration_weight_c_puct=1.0,
        crossover_strategy="tool_swap"
    )
    fitness_eval = CostAwareFitnessMetric(
        base_reward_metric_uri="local://test",
        token_bloat_penalty=0.5,
        latency_penalty_ms=0.1,
        max_acceptable_cost_usd=10.0
    )
    shadow_config = ShadowPopulationConfig(
        background_mutation_rate=0.2,
        hot_swap_threshold=0.05,
        telemetry_feedback_sync=False
    )

    node = EvolutionaryReasoningTopology(
        id="evo_node_1",
        target_intent="Solve complex problem",
        mcts_config=mcts_config,
        fitness_evaluator=fitness_eval,
        shadow_deployment=shadow_config
    )

    assert node.id == "evo_node_1"
    assert node.target_intent == "Solve complex problem"
    assert node.mcts_config.population_limit == 10
    assert node.fitness_evaluator.max_acceptable_cost_usd == 10.0
    assert node.shadow_deployment is not None
    assert node.shadow_deployment.background_mutation_rate == 0.2
    assert node.type == "evolutionary_reasoning"
