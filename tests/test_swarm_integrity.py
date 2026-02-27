import pytest

from coreason_manifest.spec.core.flow import FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.nodes import CognitiveProfile, SwarmNode
from coreason_manifest.utils.validator import validate_flow


def test_swarm_integrity_validation() -> None:
    """Test that SwarmNode integrity checks work correctly."""

    # Define a valid profile
    profile = CognitiveProfile(role="worker", persona="worker persona", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"worker-1": profile})
    metadata = FlowMetadata(name="test_swarm", version="1.0.0")

    # Case 1: Valid SwarmNode
    valid_swarm = SwarmNode(
        id="s1",
        metadata={},
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

    # Should not report errors
    flow_valid = LinearFlow(
        metadata=metadata,
        definitions=definitions,
        steps=[valid_swarm]
    )
    errors_valid = validate_flow(flow_valid)
    assert len(errors_valid) == 0

    # Case 2: Invalid SwarmNode (undefined profile)
    invalid_swarm = SwarmNode(
        id="s2",
        metadata={},
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

    flow_invalid = LinearFlow(
        metadata=metadata,
        definitions=definitions,
        steps=[invalid_swarm]
    )
    errors_invalid = validate_flow(flow_invalid)

    # The fix to validator.py changed this from integrity error to validation error
    assert len(errors_invalid) > 0
    # Depending on implementation, message might vary slightly but should contain profile ID
    assert any("ghost-worker" in e.message or "missing profile" in e.message for e in errors_invalid)


if __name__ == "__main__":
    test_swarm_integrity_validation()
    print("Swarm integrity validation test passed!")
