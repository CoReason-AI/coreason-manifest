import pytest

from coreason_manifest.spec.core.flow import FlowDefinitions, validate_integrity
from coreason_manifest.spec.core.nodes import CognitiveProfile, SwarmNode


def test_swarm_integrity_validation() -> None:
    """Test that SwarmNode integrity checks work correctly."""

    # Define a valid profile
    profile = CognitiveProfile(role="worker", persona="worker persona", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"worker-1": profile})

    # Case 1: Valid SwarmNode
    valid_swarm = SwarmNode(
        id="s1",
        metadata={},
        supervision=None,
        type="swarm",
        worker_profile="worker-1",
        workload_variable="v1",
        distribution_strategy="sharded",
        max_concurrency=5,
        failure_tolerance_percent=0.1,
        reducer_function="vote",
        aggregator_model=None,
        output_variable="out",
    )

    # Should not raise
    validate_integrity(definitions, [valid_swarm])

    # Case 2: Invalid SwarmNode (undefined profile)
    invalid_swarm = SwarmNode(
        id="s2",
        metadata={},
        supervision=None,
        type="swarm",
        worker_profile="ghost-worker",
        workload_variable="v1",
        distribution_strategy="sharded",
        max_concurrency=5,
        failure_tolerance_percent=0.1,
        reducer_function="vote",
        aggregator_model=None,
        output_variable="out",
    )

    with pytest.raises(ValueError, match="SwarmNode 's2' references undefined worker profile ID 'ghost-worker'"):
        validate_integrity(definitions, [invalid_swarm])


if __name__ == "__main__":
    test_swarm_integrity_validation()
    print("Swarm integrity validation test passed!")
