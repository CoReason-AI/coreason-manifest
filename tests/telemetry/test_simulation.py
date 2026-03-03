import pytest
from pydantic import ValidationError

from coreason_manifest.core.telemetry.simulation import JSONPatchOperation, PatchOp, SimulationStep, SimulationTrace


def test_json_patch_operation_valid() -> None:
    """Test valid JSON patch creation."""
    patch = JSONPatchOperation(op=PatchOp.REPLACE, path="/state/key", value="new_value")
    assert patch.op == PatchOp.REPLACE
    assert patch.path == "/state/key"
    assert patch.value == "new_value"


def test_simulation_step_valid() -> None:
    """Test valid simulation step creation."""
    patch = JSONPatchOperation(op=PatchOp.ADD, path="/state/test", value=123)
    step = SimulationStep(
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="congo=t61rcWkgMzE",
        state_mutations=[patch],
        execution_hash="a" * 64,
        thought="I am thinking",
    )
    assert step.traceparent == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    assert step.tracestate == "congo=t61rcWkgMzE"
    assert len(step.state_mutations) == 1
    assert step.state_mutations[0] == patch
    assert step.execution_hash == "a" * 64
    assert step.thought == "I am thinking"


def test_simulation_trace_valid() -> None:
    """Test valid simulation trace creation."""
    step = SimulationStep(
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="congo=t61rcWkgMzE",
        state_mutations=[],
        execution_hash="a" * 64,
    )
    trace = SimulationTrace(steps=[step])
    assert len(trace.steps) == 1
    assert trace.steps[0] == step


def test_simulation_step_missing_required_fields() -> None:
    """Test missing required fields in SimulationStep."""
    with pytest.raises(ValidationError) as exc_info:
        SimulationStep(
            tracestate="congo=t61rcWkgMzE",
            execution_hash="a" * 64,
        )  # type: ignore[call-arg]
    assert "traceparent" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        SimulationStep(
            traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            execution_hash="a" * 64,
        )  # type: ignore[call-arg]
    assert "tracestate" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        SimulationStep(
            traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            tracestate="congo=t61rcWkgMzE",
        )  # type: ignore[call-arg]
    assert "execution_hash" in str(exc_info.value)


def test_simulation_step_immutability() -> None:
    """Test that SimulationStep is frozen (immutable)."""
    step = SimulationStep(
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="congo=t61rcWkgMzE",
        state_mutations=[],
        execution_hash="a" * 64,
    )

    with pytest.raises(ValidationError) as exc_info:
        step.traceparent = "new-traceparent"  # type: ignore[misc]
    assert "Instance is frozen" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        step.thought = "New thought"  # type: ignore[misc]
    assert "Instance is frozen" in str(exc_info.value)
