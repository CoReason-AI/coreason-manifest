# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from uuid import uuid4

from coreason_manifest.definitions.agent import Persona
from coreason_manifest.definitions.simulation import (
    SimulationMetrics,
    SimulationScenario,
    SimulationStep,
    SimulationTrace,
    StepType,
    ValidationLogic,
)
from coreason_manifest.definitions.simulation_config import AdversaryProfile, ChaosConfig, SimulationRequest


def test_adversary_profile() -> None:
    profile = AdversaryProfile(name="Attacker", goal="Break stuff", strategy_model="gpt-4", attack_model="llama-3")
    assert profile.name == "Attacker"
    assert profile.goal == "Break stuff"


def test_chaos_config_defaults() -> None:
    config = ChaosConfig()
    assert config.latency_ms == 0
    assert config.error_rate == 0.0


def test_simulation_request() -> None:
    scenario = SimulationScenario(
        id="scen-1",
        name="Scenario 1",
        objective="Do it",
        difficulty=1,
        expected_outcome="Done",
        validation_logic=ValidationLogic.EXACT_MATCH,
    )
    profile = AdversaryProfile(name="Attacker", goal="Break stuff", strategy_model="gpt-4", attack_model="llama-3")
    req = SimulationRequest(scenario=scenario, profile=profile)
    assert req.chaos_config.latency_ms == 0


def test_simulation_metrics() -> None:
    metrics = SimulationMetrics(turn_count=5, total_tokens=100)
    assert metrics.turn_count == 5
    assert metrics.total_tokens == 100
    assert metrics.cost_usd is None


def test_simulation_step_system_event() -> None:
    step = SimulationStep(
        step_id=uuid4(),
        timestamp=datetime.now(),
        type=StepType.SYSTEM_EVENT,
        node_id="system",
        inputs={"error": "failed"},
        # thought, action, observation are optional now
    )
    assert step.type == StepType.SYSTEM_EVENT
    assert step.thought is None
    assert step.action is None
    assert step.observation is None


def test_simulation_trace_with_metrics() -> None:
    step = SimulationStep(
        step_id=uuid4(),
        timestamp=datetime.now(),
        node_id="node-1",
        inputs={},
        thought="Thinking",
        action={"tool": "call"},
        observation={"result": "ok"},
    )
    metrics = SimulationMetrics(turn_count=1)
    trace = SimulationTrace(
        trace_id=uuid4(), agent_version="1.0.0", steps=[step], outcome={"status": "success"}, metrics=metrics
    )
    assert trace.metrics.turn_count == 1


def test_persona() -> None:
    persona = Persona(name="Helper", description="A helpful assistant", directives=["Be nice", "Help user"])
    assert persona.name == "Helper"
    assert len(persona.directives) == 2
