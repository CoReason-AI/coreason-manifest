# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.simulation import SimulationScenario, ValidationLogic
from coreason_manifest.definitions.simulation_config import (
    AdversaryProfile,
    ChaosConfig,
    SimulationRequest,
)


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
