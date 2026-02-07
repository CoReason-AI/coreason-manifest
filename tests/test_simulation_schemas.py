# tests/test_simulation_schemas.py

import json
from uuid import UUID

from coreason_manifest import (
    AdversaryProfile,
    ChaosConfig,
    SimulationRequest,
    SimulationScenario,
    SimulationStep,
    SimulationTrace,
    StepType,
    ValidationLogic,
)


def test_simulation_step_serialization() -> None:
    """Test serialization of a SimulationStep."""
    step = SimulationStep(
        type=StepType.REASONING,
        node_id="node_1",
        thought="Thinking about the problem",
        inputs={"query": "Who is the president?"},
    )

    # Verify defaults
    assert isinstance(step.step_id, UUID)
    assert step.timestamp is not None
    assert step.snapshot == {}

    # Verify serialization
    dumped = step.model_dump_json()
    assert "step_id" in dumped
    assert "timestamp" in dumped
    assert "reasoning" in dumped


def test_simulation_trace_integrity() -> None:
    """Test trace integrity and serialization."""
    step1 = SimulationStep(
        type=StepType.INTERACTION,
        node_id="start",
        inputs={"user_input": "Hello"},
    )
    step2 = SimulationStep(
        type=StepType.TOOL_EXECUTION,
        node_id="tool_node",
        action={"tool": "search", "args": {"q": "Hello"}},
    )

    trace = SimulationTrace(
        agent_id="agent-007",
        agent_version="1.0.0",
        steps=[step1, step2],
    )

    assert len(trace.steps) == 2
    assert trace.steps[0].node_id == "start"
    assert trace.steps[1].node_id == "tool_node"

    # Test serialization
    json_str = trace.model_dump_json()
    data = json.loads(json_str)

    assert data["agent_id"] == "agent-007"
    assert len(data["steps"]) == 2
    # Check if UUIDs are serialized as strings
    assert isinstance(data["trace_id"], str)
    assert isinstance(data["steps"][0]["step_id"], str)


def test_simulation_defaults() -> None:
    """Test default values for SimulationStep."""
    step = SimulationStep(
        type=StepType.SYSTEM_EVENT,
        node_id="init",
    )

    assert isinstance(step.step_id, UUID)
    assert step.timestamp is not None
    assert step.inputs == {}
    assert step.snapshot == {}
    assert step.thought is None


def test_nesting_simulation_request() -> None:
    """Test nesting of objects in SimulationRequest."""
    profile = AdversaryProfile(
        name="RedTeamer",
        goal="Break stuff",
        strategy_model="gpt-4",
        attack_model="gpt-3.5",
    )

    scenario = SimulationScenario(
        id="scenario-1",
        description="Test basic interaction",
        inputs={"text": "Hi"},
        validation_logic=ValidationLogic.EXACT_MATCH,
    )

    chaos = ChaosConfig(
        latency_ms=100,
        error_rate=0.01,
    )

    req = SimulationRequest(
        scenario=scenario,
        profile=profile,
        chaos_config=chaos,
    )

    # Serialize and deserialize
    json_str = req.model_dump_json()
    restored = SimulationRequest.model_validate_json(json_str)

    assert restored.scenario.id == "scenario-1"
    assert restored.profile is not None
    assert restored.profile.name == "RedTeamer"
    assert restored.chaos_config is not None
    assert restored.chaos_config.latency_ms == 100
