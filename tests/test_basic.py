from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.core.compute.reasoning import CrossoverStrategy, EvolutionaryReasoning, ReasoningConfig
from coreason_manifest.core.primitives.types import DataClassification


def test_import() -> None:
    import coreason_manifest

    assert coreason_manifest is not None


@pytest.fixture
def mock_factory() -> Any:
    from coreason_manifest.toolkit.mock import MockFactory

    return MockFactory(seed=42)


def test_sota_passport_instantiation(mock_factory: Any) -> None:
    """
    Ensures the 2026+ Architectural Hardening fields are properly validated.
    Epic 6 is fully merged and models accept these kwargs.
    """
    # Test 1: Standard Multi-Dimensional Bounds
    passport = mock_factory.generate_mock_passport(classification=DataClassification.RESTRICTED)
    assert passport.delegation.max_tokens == 50_000
    assert passport.delegation.max_compute_time_ms == 120_000
    assert passport.delegation.max_data_classification == DataClassification.RESTRICTED
    assert passport.delegation.caep_stream_uri == "https://mock-ssf.local.coreason.ai/stream"
    assert passport.signature_algorithm == "ML-DSA-65"
    assert passport.parent_passport_id is None

    # Test 2: Swarm Lineage Fuzzing
    child_passport = mock_factory.generate_mock_passport(is_swarm_child=True)
    assert child_passport.parent_passport_id is not None
    assert "mock_parent_jti_" in child_passport.parent_passport_id


def test_swarm_orchestration_schema() -> None:
    from coreason_manifest.core.workflow.nodes.swarm import SwarmNode, TournamentConfig
    from pydantic import ValidationError

    # Valid Instantiation
    valid_swarm = SwarmNode(
        id="test_swarm",
        worker_profile="researcher",
        workload_variable="urls",
        output_variable="report",
        distribution_strategy="island_model",
        sub_swarm_count=3,
        isolation_turns=5,
        reducer_function="tournament",
        tournament_config=TournamentConfig(),
        max_concurrency=10,
        operational_policy=None,
    )
    assert valid_swarm.distribution_strategy == "island_model"

    # Invalid: Tournament without config
    with pytest.raises(ValidationError) as exc:
        SwarmNode(
            id="test_swarm", worker_profile="researcher", workload_variable="urls", output_variable="report",
            distribution_strategy="sharded", reducer_function="tournament",
            max_concurrency=10, operational_policy=None,
        )
    assert "requires a 'tournament_config'" in str(exc.value)

    # Invalid: Compute bound without operational policy
    with pytest.raises(ValidationError) as exc:
        SwarmNode(
            id="test_swarm", worker_profile="researcher", workload_variable="urls", output_variable="report",
            distribution_strategy="sharded", pruning_strategy="compute_bound",
            max_concurrency=10, reducer_function="concat", operational_policy=None,
        )
    assert "requires an 'operational_policy'" in str(exc.value)
def test_epistemic_tracking_config() -> None:
    from coreason_manifest.core.state.memory import KnowledgeScope, RetrievalStrategy, SemanticMemoryConfig

    # Default behavior: epistemic_tracking should be False
    config_default = SemanticMemoryConfig(
        graph_namespace="test_default",
        bitemporal_tracking=False,
        scope=KnowledgeScope.SESSION,
    )
    assert config_default.epistemic_tracking is False

    # Explicit behavior: testing EPISTEMIC retrieval strategy and epistemic_tracking=True
    config_epistemic = SemanticMemoryConfig(
        graph_namespace="test_epistemic",
        bitemporal_tracking=True,
        scope=KnowledgeScope.USER,
        epistemic_tracking=True,
        retrieval_strategy=RetrievalStrategy.EPISTEMIC,
    )
    assert config_epistemic.epistemic_tracking is True
    assert config_epistemic.retrieval_strategy == RetrievalStrategy.EPISTEMIC

    from pydantic import ValidationError

    # 3. Invalid behavior: testing EPISTEMIC strategy without tracking enabled
    with pytest.raises(ValidationError) as exc_info:
        SemanticMemoryConfig(
            graph_namespace="test_invalid",
            bitemporal_tracking=True,
            scope=KnowledgeScope.SESSION,
            epistemic_tracking=False,  # This should trigger the failure
            retrieval_strategy=RetrievalStrategy.EPISTEMIC,
        )
    assert "epistemic_tracking must be True" in str(exc_info.value)
def test_evolutionary_reasoning_schema() -> None:
    # 1. Valid instantiation
    valid_evo = EvolutionaryReasoning(
        model="gpt-4",
        fitness_evaluator_model="gpt-4o",
        population_size=10,
        generations=5,
        mutation_rate=0.2,
        crossover_strategy=CrossoverStrategy.SINGLE_POINT,
    )
    assert valid_evo.type == "evolutionary"
    assert valid_evo.population_size == 10
    assert valid_evo.generations == 5
    assert valid_evo.mutation_rate == 0.2
    assert valid_evo.crossover_strategy == CrossoverStrategy.SINGLE_POINT
    assert valid_evo.fitness_evaluator_model == "gpt-4o"

    # Default values check
    default_evo = EvolutionaryReasoning(model="gpt-4", fitness_evaluator_model="claude-3")
    assert default_evo.population_size == 5
    assert default_evo.generations == 3
    assert default_evo.mutation_rate == 0.15
    assert default_evo.crossover_strategy == CrossoverStrategy.SEMANTIC_BLENDING

    # 2. Invalid instantiation (mutation_rate out of bounds)
    with pytest.raises(ValidationError) as exc_info:
        EvolutionaryReasoning(
            model="gpt-4",
            fitness_evaluator_model="gpt-4o",
            mutation_rate=1.5,
        )
    assert "mutation_rate" in str(exc_info.value)
    assert "Input should be less than or equal to 1" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        EvolutionaryReasoning(
            model="gpt-4",
            fitness_evaluator_model="gpt-4o",
            mutation_rate=-0.1,
        )
    assert "mutation_rate" in str(exc_info.value)
    assert "Input should be greater than or equal to 0" in str(exc_info.value)

    # 2. Invalid instantiation (missing fitness_evaluator_model)
    with pytest.raises(ValidationError) as exc_info:
        EvolutionaryReasoning(model="gpt-4")  # type: ignore[call-arg]
    assert "fitness_evaluator_model" in str(exc_info.value)
    assert "Field required" in str(exc_info.value)

    # 3. Polymorphic Union Test
    adapter = TypeAdapter(ReasoningConfig)
    parsed = adapter.validate_python(
        {
            "type": "evolutionary",
            "model": "gpt-4",
            "fitness_evaluator_model": "gpt-4o",
        }
    )
    assert isinstance(parsed, EvolutionaryReasoning)


def test_symbolic_execution_inspector_node() -> None:
    from pydantic import ValidationError

    from coreason_manifest.core.workflow.nodes.oversight import InspectorNode

    # Valid symbolic execution
    node = InspectorNode(
        id="test-node",
        target_variable="code",
        criteria="must compile",
        output_variable="result",
        mode="symbolic_execution",
        target_solver="lean4",
    )
    assert node.mode == "symbolic_execution"
    assert node.target_solver == "lean4"

    # Invalid symbolic execution (missing solver)
    with pytest.raises(ValidationError):
        InspectorNode(
            id="test-node-invalid",
            target_variable="code",
            criteria="must compile",
            output_variable="result",
            mode="symbolic_execution",
        )

    from coreason_manifest.core.oversight.resilience import RetryStrategy

    # Valid resilience config
    valid_retry = RetryStrategy(max_attempts=3, symbolic_repair_budget=5)
    assert valid_retry.symbolic_repair_budget == 5

    # Invalid resilience config (negative budget)
    with pytest.raises(ValidationError):
        RetryStrategy(max_attempts=3, symbolic_repair_budget=-1)
