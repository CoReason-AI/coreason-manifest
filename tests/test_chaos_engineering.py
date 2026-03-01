import pytest
from pydantic import ValidationError

from coreason_manifest.core.telemetry_schemas import NodeState
from coreason_manifest.core.workflow.evals import AdversaryProfile, ChaosConfig, EvalsManifest, TestCase
from coreason_manifest.core.workflow.flow import FlowMetadata, LinearFlow
from coreason_manifest.core.workflow.nodes import AgentNode
from coreason_manifest.toolkit.mock import MockFactory


def test_chaos_config_and_adversary_parsing() -> None:
    """Test Pydantic correctly parses ChaosConfig and AdversaryProfile."""
    test_case = TestCase(
        expected_traversal_path=["node_1"],
        chaos_config=ChaosConfig(latency_ms=1000, error_rate=0.5, token_throttle=True),
        adversary=AdversaryProfile(goal="Extract PII", attack_strategy="crescendo"),
    )

    assert test_case.chaos_config is not None
    assert test_case.chaos_config.latency_ms == 1000
    assert test_case.chaos_config.error_rate == 0.5
    assert test_case.chaos_config.token_throttle is True
    assert test_case.adversary is not None
    assert test_case.adversary.goal == "Extract PII"
    assert test_case.adversary.attack_strategy == "crescendo"


def test_chaos_config_validation() -> None:
    """Test validation of chaos fields."""
    with pytest.raises(ValidationError):
        ChaosConfig(latency_ms=-1)  # Less than 0

    with pytest.raises(ValidationError):
        ChaosConfig(error_rate=1.5)  # Greater than 1.0

    with pytest.raises(ValidationError):
        ChaosConfig(error_rate=-0.1)  # Less than 0.0


def test_mock_factory_inflates_duration() -> None:
    """Test MockFactory duration trace increases with latency_ms."""
    factory = MockFactory(seed=42)

    # Base configuration without chaos
    evals_no_chaos = EvalsManifest(test_cases=[TestCase(expected_traversal_path=["node_1"])])
    flow = LinearFlow(
        metadata=FlowMetadata(name="test_flow", version="1.0"),
        steps=[AgentNode(id="node_1", profile="test_agent", operational_policy=None)],
    )
    trace_no_chaos = factory.simulate_trace(flow, evals=evals_no_chaos)

    # Configuration with latency
    evals_latency = EvalsManifest(
        test_cases=[
            TestCase(
                expected_traversal_path=["node_1"],
                chaos_config=ChaosConfig(latency_ms=5000),
            )
        ]
    )
    # Using same seed for deterministic output (base duration should be exactly the same)
    factory2 = MockFactory(seed=42)
    trace_latency = factory2.simulate_trace(flow, evals=evals_latency)

    assert len(trace_no_chaos) == 1
    assert len(trace_latency) == 1

    base_duration = trace_no_chaos[0].duration_ms
    inflated_duration = trace_latency[0].duration_ms

    assert inflated_duration == pytest.approx(base_duration + 5000)


def test_mock_factory_forces_failure() -> None:
    """Test MockFactory node fails and state is FAILED with error when error_rate = 1.0."""
    factory = MockFactory(seed=42)
    evals_fail = EvalsManifest(
        test_cases=[
            TestCase(
                expected_traversal_path=["node_1"],
                chaos_config=ChaosConfig(error_rate=1.0),
            )
        ]
    )
    flow = LinearFlow(
        metadata=FlowMetadata(name="test_flow", version="1.0"),
        steps=[AgentNode(id="node_1", profile="test_agent", operational_policy=None)],
    )
    trace_fail = factory.simulate_trace(flow, evals=evals_fail)

    assert len(trace_fail) == 1
    execution = trace_fail[0]

    assert execution.state == NodeState.FAILED
    assert execution.error == "HTTP 500 Internal Server Error"
    assert "error" not in execution.outputs
