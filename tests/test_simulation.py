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
import uuid
from datetime import datetime, timezone

from coreason_manifest.definitions.simulation import (
    SimulationMetrics,
    SimulationScenario,
    SimulationStep,
    SimulationTrace,
    ValidationLogic,
)


def test_trace_validity() -> None:
    """Ensure a trace can correctly serialize a list of steps."""
    step_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    step = SimulationStep(
        step_id=step_id,
        timestamp=now,
        node_id="node_1",
        inputs={"query": "test"},
        thought="thinking...",
        action={"tool": "search"},
        observation={"result": "found"},
    )

    trace = SimulationTrace(
        trace_id=trace_id,
        agent_version="1.0.0",
        steps=[step],
        outcome={"success": True},
        metrics=SimulationMetrics(turn_count=1, total_tokens=100),
    )

    # Verify serialization
    json_str = trace.model_dump_json()
    data = json.loads(json_str)

    assert data["trace_id"] == str(trace_id)
    assert len(data["steps"]) == 1
    assert data["steps"][0]["step_id"] == str(step_id)
    assert data["steps"][0]["thought"] == "thinking..."


def test_scenario_creation() -> None:
    """Test scenario creation."""
    scenario = SimulationScenario(
        id="scen_1",
        name="Test Scenario",
        objective="Do something",
        difficulty=2,
        expected_outcome="Done",
        validation_logic=ValidationLogic.EXACT_MATCH,
    )
    assert scenario.difficulty == 2
    assert scenario.validation_logic == "exact_match"
