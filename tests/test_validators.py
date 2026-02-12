import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.engines import AdaptiveReasoning
from coreason_manifest.spec.core.nodes import HumanNode, SwarmNode


def test_human_node_validators_coverage() -> None:
    """Test validation logic in HumanNode to ensure 100% coverage."""

    # Test 1: Shadow mode without shadow_timeout_seconds (Should raise ValueError)
    with pytest.raises(ValidationError, match="HumanNode in 'shadow' mode requires 'shadow_timeout_seconds'"):
        HumanNode(
            id="h1",
            metadata={},
            supervision=None,
            type="human",
            prompt="p",
            timeout_seconds=10,
            interaction_mode="shadow",
            shadow_timeout_seconds=None,
        )

    # Test 2: Blocking mode with shadow_timeout_seconds (Should raise ValueError)
    with pytest.raises(ValidationError, match="HumanNode in 'blocking' mode must not have 'shadow_timeout_seconds'"):
        HumanNode(
            id="h2",
            metadata={},
            supervision=None,
            type="human",
            prompt="p",
            timeout_seconds=10,
            interaction_mode="blocking",
            shadow_timeout_seconds=5,
        )


def test_swarm_node_validators_coverage() -> None:
    """Test validation logic in SwarmNode to ensure 100% coverage."""

    # Test 1: Summarize reducer without aggregator_model (Should raise ValueError)
    with pytest.raises(ValidationError, match="SwarmNode with reducer='summarize' requires an 'aggregator_model'"):
        SwarmNode(
            id="s1",
            metadata={},
            supervision=None,
            type="swarm",
            worker_profile="p1",
            workload_variable="v1",
            distribution_strategy="sharded",
            max_concurrency=5,
            failure_tolerance_percent=0.1,
            reducer_function="summarize",
            aggregator_model=None,
            output_variable="out",
        )

    # Test 2: Valid SwarmNode to hit the 'return self' statement
    valid_swarm = SwarmNode(
        id="s2",
        metadata={},
        supervision=None,
        type="swarm",
        worker_profile="p1",
        workload_variable="v1",
        distribution_strategy="sharded",
        max_concurrency=5,
        failure_tolerance_percent=0.1,
        reducer_function="vote",
        aggregator_model=None,
        output_variable="out",
    )
    assert valid_swarm.reducer_function == "vote"


def test_adaptive_reasoning_validators_coverage() -> None:
    """Test validation logic in AdaptiveReasoning."""

    # Test 1: Invalid max_compute_tokens <= 0
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        AdaptiveReasoning(
            model="o1",
            max_compute_tokens=0,
            max_duration_seconds=10.0,
            scaling_mode="hybrid",
            min_confidence_score=0.5,
            verifier_model="v1",
        )
