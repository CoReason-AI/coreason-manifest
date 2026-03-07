import pytest
from pydantic import ValidationError

from coreason_manifest.compute.inference import AnalogicalMappingTask


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


def test_analogical_mapping_task_invalid_id() -> None:
    with pytest.raises(ValidationError):
        AnalogicalMappingTask(
            task_id="",
            source_domain="physics",
            target_domain="economics",
            required_isomorphisms=3,
            divergence_temperature_override=1.5,
        )
