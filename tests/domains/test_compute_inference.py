import pytest
from pydantic import ValidationError

from coreason_manifest.compute.inference import (
    AnalogicalMappingTask,
    EpistemicCompressionSLA,
    EpistemicTransmutationTask,
    InterventionalCausalTask,
)


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
            execution_cost_budget_magnitude=100,
        )
    assert "Input should be greater than or equal to 0" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        InterventionalCausalTask(
            task_id="task-1",
            target_hypothesis_id="hyp-1",
            intervention_variable="X",
            do_operator_state="1",
            expected_causal_information_gain=1.1,  # Invalid
            execution_cost_budget_magnitude=100,
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


def test_epistemic_transmutation_task_valid() -> None:
    sla = EpistemicCompressionSLA(
        strict_probability_retention=True, max_allowed_entropy_loss=0.1, required_grounding_density="dense"
    )
    task = EpistemicTransmutationTask(
        task_id="transmute-1",
        artifact_event_id="hash-123",
        target_modalities=["text", "tabular_grid"],
        compression_sla=sla,
    )
    assert task.task_id == "transmute-1"
    assert "tabular_grid" in task.target_modalities


def test_epistemic_transmutation_validation_failure() -> None:
    sla_sparse = EpistemicCompressionSLA(
        strict_probability_retention=True, max_allowed_entropy_loss=0.5, required_grounding_density="sparse"
    )
    with pytest.raises(ValidationError, match="Visual or tabular modalities require strict spatial tracking"):
        EpistemicTransmutationTask(
            task_id="transmute-2",
            artifact_event_id="hash-123",
            target_modalities=["raster_image"],
            compression_sla=sla_sparse,
        )


def test_epistemic_transmutation_text_allows_sparse() -> None:
    sla_sparse = EpistemicCompressionSLA(
        strict_probability_retention=False, max_allowed_entropy_loss=0.8, required_grounding_density="sparse"
    )
    task = EpistemicTransmutationTask(
        task_id="transmute-3", artifact_event_id="hash-123", target_modalities=["text"], compression_sla=sla_sparse
    )
    assert task.compression_sla.required_grounding_density == "sparse"
