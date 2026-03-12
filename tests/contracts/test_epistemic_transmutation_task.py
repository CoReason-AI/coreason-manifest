import hypothesis.strategies as st
import pytest
from hypothesis import given
from pydantic import ValidationError

from coreason_manifest.spec.ontology import EpistemicCompressionSLA, EpistemicTransmutationTask


@given(
    modalities=st.lists(
        st.sampled_from(["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]),
        min_size=1,
        max_size=10,
    )
)
def test_epistemic_transmutation_task_deterministic_sort(modalities: list[str]) -> None:
    """Prove commutative modality arrays are deterministically sorted for canonical hashing."""
    sla = EpistemicCompressionSLA(
        strict_probability_retention=True, max_allowed_entropy_loss=0.5, required_grounding_density="dense"
    )

    task = EpistemicTransmutationTask(
        task_id="t1",
        artifact_event_id="e1",
        target_modalities=modalities,  # type: ignore
        compression_sla=sla,
    )

    assert task.target_modalities == sorted(modalities)


@pytest.mark.parametrize("visual_modality", ["tabular_grid", "raster_image"])
def test_multimodal_grounding_density_alignment(visual_modality: str) -> None:
    """Prove the topological interlock: visual modalities strictly require dense grounding."""
    sla_sparse = EpistemicCompressionSLA(
        strict_probability_retention=True, max_allowed_entropy_loss=0.5, required_grounding_density="sparse"
    )

    with pytest.raises(ValidationError, match="Visual or tabular modalities require strict spatial tracking"):
        EpistemicTransmutationTask(
            task_id="task_visual_test",
            artifact_event_id="artifact_1",
            target_modalities=[visual_modality],  # type: ignore
            compression_sla=sla_sparse,
        )
