# tests/test_simulation_schemas.py

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

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
    assert step.timestamp.tzinfo == UTC
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


def test_edge_cases_empty_inputs() -> None:
    """Test edge case with empty inputs and outputs."""
    step = SimulationStep(
        type=StepType.INTERACTION,
        node_id="empty_node",
        inputs={},
        observation={},
    )
    assert step.inputs == {}
    assert step.observation == {}

    trace = SimulationTrace(
        agent_id="empty-agent",
        agent_version="0.0.0",
        steps=[],
    )
    assert trace.steps == []
    assert trace.outcome is None


def test_edge_cases_timestamps() -> None:
    """Test explicit timestamp handling."""
    custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    step = SimulationStep(
        type=StepType.SYSTEM_EVENT,
        node_id="time_node",
        timestamp=custom_time,
    )
    assert step.timestamp == custom_time
    assert step.timestamp.tzinfo == UTC


def test_edge_cases_enum_validation() -> None:
    """Test that invalid enum values raise validation errors."""
    with pytest.raises(ValidationError):
        SimulationStep(
            type="invalid_type",  # type: ignore
            node_id="fail_node",
        )

    with pytest.raises(ValidationError):
        SimulationScenario(
            id="bad_scenario",
            description="fail",
            inputs={},
            validation_logic="random_logic",  # type: ignore
        )


def test_complex_trace_serialization() -> None:
    """Test a complex trace with mixed step types and nested data."""
    steps = [
        SimulationStep(
            type=StepType.SYSTEM_EVENT,
            node_id="boot",
            inputs={"config": {"debug": True}},
        ),
        SimulationStep(
            type=StepType.INTERACTION,
            node_id="user_input",
            inputs={"query": "Calculate complex math"},
        ),
        SimulationStep(
            type=StepType.REASONING,
            node_id="cot",
            thought="I need to use python for this.\nStep 1: import math...",
        ),
        SimulationStep(
            type=StepType.TOOL_EXECUTION,
            node_id="exec_python",
            action={
                "tool_name": "python_repl",
                "code": "import math\nprint(math.pi ** 2)",
            },
            observation={"stdout": "9.869604401089358"},
        ),
    ]

    trace = SimulationTrace(
        agent_id="complex-agent",
        agent_version="2.0.0-beta",
        steps=steps,
        outcome={"result": 9.8696},
        score=0.95,
        metadata={
            "run_id": "12345",
            "env": "prod",
            "tags": ["math", "complex"],
        },
    )

    # Round trip
    json_str = trace.model_dump_json()
    restored = SimulationTrace.model_validate_json(json_str)

    assert len(restored.steps) == 4
    assert restored.steps[3].type == StepType.TOOL_EXECUTION
    # Use explicit type casting/checking for nested dict access to satisfy type checkers
    action = restored.steps[3].action
    assert action is not None
    assert action["tool_name"] == "python_repl"
    assert restored.metadata["tags"] == ["math", "complex"]


def test_optional_fields_none() -> None:
    """Test that optional fields correctly handle None."""
    req = SimulationRequest(
        scenario=SimulationScenario(
            id="minimal",
            description="min",
            inputs={},
            validation_logic=ValidationLogic.FUZZY,
        ),
        profile=None,
        chaos_config=None,
    )
    assert req.profile is None
    assert req.chaos_config is None

    dumped = req.model_dump(exclude_none=True)
    assert "profile" not in dumped
    assert "chaos_config" not in dumped
