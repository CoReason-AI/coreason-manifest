# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.simulation import (
    AdversaryProfile,
    ChaosConfig,
    SimulationRequest,
    SimulationScenario,
    SimulationStep,
    SimulationTrace,
    StepType,
    ValidationLogic,
)


def test_simulation_defaults() -> None:
    """Ensure UUIDs and Timestamps are auto-generated."""
    step = SimulationStep(
        type=StepType.INTERACTION,
        node_id="node_1",
        inputs={"msg": "hello"},
        snapshot={"state": "init"},
    )
    assert isinstance(step.step_id, UUID)
    assert isinstance(step.timestamp, datetime)
    assert step.timestamp.tzinfo == UTC

    trace = SimulationTrace(
        agent_id="agent-007",
        agent_version="1.0.0",
        metadata={"env": "test"},
    )
    assert isinstance(trace.trace_id, UUID)
    assert trace.steps == []


def test_simulation_serialization() -> None:
    """Create a SimulationTrace with 3 steps and check serialization."""
    steps = [
        SimulationStep(
            type=StepType.SYSTEM_EVENT,
            node_id="start",
            inputs={},
            snapshot={},
            thought="Starting up",
        ),
        SimulationStep(
            type=StepType.INTERACTION,
            node_id="process",
            inputs={"q": "hi"},
            snapshot={},
            action={"tool": "search", "args": {"q": "hi"}},
        ),
        SimulationStep(
            type=StepType.TOOL_EXECUTION,
            node_id="tool",
            inputs={"q": "hi"},
            snapshot={},
            observation={"result": "found"},
        ),
    ]

    trace = SimulationTrace(
        agent_id="test-agent",
        agent_version="0.1.0",
        steps=steps,
        metadata={"run": 1},
        score=0.95,
    )

    json_str = trace.model_dump_json()
    data = json.loads(json_str)

    assert data["agent_id"] == "test-agent"
    assert len(data["steps"]) == 3
    assert data["steps"][0]["type"] == "SYSTEM_EVENT"
    assert data["steps"][1]["action"]["tool"] == "search"
    assert data["score"] == 0.95


def test_simulation_nesting() -> None:
    """Ensure SimulationRequest correctly nests AdversaryProfile and ChaosConfig."""
    profile = AdversaryProfile(
        name="The Joker",
        goal="Chaos",
        strategy_model="gpt-4",
        attack_model="gpt-3.5",
        persona={"style": "manic"},
    )

    chaos = ChaosConfig(
        latency_ms=100,
        error_rate=0.1,
    )

    scenario = SimulationScenario(
        id="scen-1",
        description="Test basic flow",
        inputs={"user": "hello"},
        validation_logic=ValidationLogic.EXACT_MATCH,
    )

    request = SimulationRequest(
        scenario=scenario,
        profile=profile,
        chaos_config=chaos,
    )

    data = request.model_dump()
    assert data["scenario"]["id"] == "scen-1"
    assert data["profile"]["name"] == "The Joker"
    assert data["chaos_config"]["latency_ms"] == 100


def test_simulation_round_trip() -> None:
    """Verify round-trip serialization."""
    original_trace = SimulationTrace(
        agent_id="round-trip-agent",
        agent_version="1.0",
        steps=[
            SimulationStep(
                type=StepType.REASONING,
                node_id="think",
                inputs={"context": "none"},
                snapshot={},
                thought="I think therefore I am",
            )
        ],
        metadata={"tags": ["test"]},
    )

    json_str = original_trace.model_dump_json()
    restored_trace = SimulationTrace.model_validate_json(json_str)

    assert restored_trace.trace_id == original_trace.trace_id
    assert restored_trace.steps[0].thought == original_trace.steps[0].thought
    assert restored_trace.metadata == original_trace.metadata


def test_simulation_edge_cases() -> None:
    """Test various edge cases for validation and defaults."""
    # 1. Invalid Score (High)
    with pytest.raises(ValidationError):
        SimulationTrace(
            agent_id="test",
            agent_version="1.0",
            metadata={},
            score=1.1,
        )

    # 2. Invalid Score (Low)
    with pytest.raises(ValidationError):
        SimulationTrace(
            agent_id="test",
            agent_version="1.0",
            metadata={},
            score=-0.1,
        )

    # 3. Invalid Error Rate
    with pytest.raises(ValidationError):
        ChaosConfig(error_rate=1.5)

    # 4. Empty Steps List (Explicit)
    trace = SimulationTrace(
        agent_id="test",
        agent_version="1.0",
        steps=[],
        metadata={},
    )
    assert trace.steps == []

    # 5. Timestamp Handling
    # Pass a naive datetime, it should remain naive if not forced, but check how Pydantic handles it.
    # Actually, spec requires UTC default. Let's see if we pass a TZ-aware one.
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    step = SimulationStep(
        type=StepType.ERROR,
        node_id="err",
        inputs={},
        snapshot={},
        timestamp=dt,
    )
    assert step.timestamp == dt


def test_simulation_complex_trace() -> None:
    """Test a complex trace with mixed step types and nested data."""
    steps = [
        # System Start
        SimulationStep(
            type=StepType.SYSTEM_EVENT,
            node_id="root",
            inputs={"config": {"debug": True}},
            snapshot={"status": "started"},
        ),
        # Reasoning
        SimulationStep(
            type=StepType.REASONING,
            node_id="planner",
            inputs={"goal": "solve P vs NP"},
            thought="This is hard.",
            snapshot={"plan": ["step1", "step2"]},
        ),
        # Tool Call with nested args
        SimulationStep(
            type=StepType.TOOL_EXECUTION,
            node_id="executor",
            inputs={"cmd": "run"},
            action={
                "tool": "compute_engine",
                "args": {"cpu": 4, "env": {"VAR": "VAL"}},
            },
            observation={"stdout": "42", "stderr": ""},
            snapshot={"result": 42},
        ),
    ]

    trace = SimulationTrace(
        agent_id="deep-thought",
        agent_version="42.0.0",
        steps=steps,
        metadata={
            "run_id": "r-123",
            "tags": ["prod", "heavy-load"],
            "complex_meta": {"a": [1, 2], "b": {"c": 3}},
        },
        outcome={"answer": 42},
        score=1.0,
    )

    dumped = trace.model_dump()
    assert len(dumped["steps"]) == 3
    assert dumped["metadata"]["complex_meta"]["b"]["c"] == 3
    assert dumped["steps"][2]["action"]["args"]["env"]["VAR"] == "VAL"


def test_simulation_adversarial_config() -> None:
    """Test validation of adversarial and chaos configurations."""
    # Complex Adversary Profile
    profile = AdversaryProfile(
        name="Chaos Monkey",
        goal="Break everything",
        strategy_model="gpt-4-turbo",
        attack_model="local-llama-3",
        persona={
            "role": "hacker",
            "skills": ["sql-injection", "prompt-injection"],
            "tone": "aggressive",
        },
    )

    # Complex Chaos Config
    chaos = ChaosConfig(
        latency_ms=5000,
        error_rate=0.99,
        token_throttle=True,
    )

    req = SimulationRequest(
        scenario=SimulationScenario(
            id="attack-vector-1",
            description="inject prompts",
            inputs={"prompt": "Ignore all instructions"},
            validation_logic=ValidationLogic.LLM_JUDGE,
        ),
        profile=profile,
        chaos_config=chaos,
    )

    assert req.profile.persona["skills"][0] == "sql-injection"
    assert req.chaos_config.error_rate == 0.99
