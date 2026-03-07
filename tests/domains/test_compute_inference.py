import pytest
from pydantic import ValidationError

from coreason_manifest.compute.inference import AnalogicalMappingTask, InterventionalCausalTask


def test_analogical_mapping_task_valid() -> None:
    task = AnalogicalMappingTask(
        task_id="test_task",
        source_domain="physics",
        target_domain="economics",
        required_isomorphisms=3,
        divergence_temperature_override=1.5,
    )
    assert task.task_id == "test_task"


def test_analogical_mapping_task_invalid_isomorphisms() -> None:
    with pytest.raises(ValidationError):
        AnalogicalMappingTask(
            task_id="test_task",
            source_domain="physics",
            target_domain="economics",
            required_isomorphisms=0,
            divergence_temperature_override=1.5,
        )


def test_analogical_mapping_task_invalid_temperature() -> None:
    with pytest.raises(ValidationError):
        AnalogicalMappingTask(
            task_id="test_task",
            source_domain="physics",
            target_domain="economics",
            required_isomorphisms=3,
            divergence_temperature_override=-0.5,
        )


def test_interventional_causal_task_bounds() -> None:
    with pytest.raises(ValidationError) as exc:
        InterventionalCausalTask(
            task_id="task-1",
            target_hypothesis_id="hyp-1",
            intervention_variable="X",
            do_operator_state="1",
            expected_causal_information_gain=-0.1,  # Invalid
            execution_cost_budget_cents=100,
        )
    assert "Input should be greater than or equal to 0" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        InterventionalCausalTask(
            task_id="task-1",
            target_hypothesis_id="hyp-1",
            intervention_variable="X",
            do_operator_state="1",
            expected_causal_information_gain=1.1,  # Invalid
            execution_cost_budget_cents=100,
        )
    assert "Input should be less than or equal to 1" in str(exc.value)


def test_analogical_mapping_task_invalid_id() -> None:
    with pytest.raises(ValidationError):
        AnalogicalMappingTask(
            task_id="",
            source_domain="physics",
            target_domain="economics",
            required_isomorphisms=3,
            divergence_temperature_override=1.5,
        )
