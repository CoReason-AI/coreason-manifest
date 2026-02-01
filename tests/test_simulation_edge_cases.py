# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.simulation import (
    SimulationScenario,
    SimulationStep,
    SimulationTrace,
    ValidationLogic,
)


def test_scenario_difficulty_bounds() -> None:
    """Test that scenario difficulty must be between 1 and 3."""
    # Valid
    SimulationScenario(
        id="s1",
        name="n",
        objective="o",
        difficulty=1,
        expected_outcome="e",
        validation_logic=ValidationLogic.EXACT_MATCH,
    )
    SimulationScenario(
        id="s2",
        name="n",
        objective="o",
        difficulty=3,
        expected_outcome="e",
        validation_logic=ValidationLogic.EXACT_MATCH,
    )

    # Invalid < 1
    with pytest.raises(ValidationError) as exc:
        SimulationScenario(
            id="s3",
            name="n",
            objective="o",
            difficulty=0,
            expected_outcome="e",
            validation_logic=ValidationLogic.EXACT_MATCH,
        )
    assert "Input should be greater than or equal to 1" in str(exc.value)

    # Invalid > 3
    with pytest.raises(ValidationError) as exc:
        SimulationScenario(
            id="s4",
            name="n",
            objective="o",
            difficulty=4,
            expected_outcome="e",
            validation_logic=ValidationLogic.EXACT_MATCH,
        )
    assert "Input should be less than or equal to 3" in str(exc.value)


def test_scenario_invalid_validation_logic() -> None:
    """Test invalid validation logic enum."""
    with pytest.raises(ValidationError):
        SimulationScenario(
            id="s5",
            name="n",
            objective="o",
            difficulty=2,
            expected_outcome="e",
            validation_logic="random_logic",
        )


def test_trace_empty_steps() -> None:
    """Test that a trace with empty steps is valid."""
    trace = SimulationTrace(
        trace_id=uuid.uuid4(),
        agent_version="1.0.0",
        steps=[],
        outcome={},
        metrics={},
    )
    assert len(trace.steps) == 0


def test_step_complex_inputs() -> None:
    """Test step with complex inputs and outputs."""
    step = SimulationStep(
        step_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        node_id="node_x",
        inputs={"a": [1, 2], "b": {"c": "d"}},
        thought="t",
        action={"tool": "search", "args": {"q": "python"}},
        observation={"results": [{"title": "Python", "url": "..."}]},
    )
    assert step.inputs["a"] == [1, 2]
    assert step.observation["results"][0]["title"] == "Python"


def test_invalid_step_id() -> None:
    """Test that step_id must be a valid UUID."""
    with pytest.raises(ValidationError):
        SimulationStep(
            step_id="not-a-uuid",
            timestamp=datetime.now(timezone.utc),
            node_id="node_x",
            inputs={},
            thought="t",
            action={},
            observation={},
        )
