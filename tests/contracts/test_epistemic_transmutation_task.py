from coreason_manifest.spec.ontology import EpistemicCompressionSLA, EpistemicTransmutationTask


def test_epistemic_transmutation_task() -> None:
    sla = EpistemicCompressionSLA(
        strict_probability_retention=True, max_allowed_entropy_loss=0.5, required_grounding_density="dense"
    )
    task = EpistemicTransmutationTask(
        task_id="t1",
        artifact_event_id="e1",
        target_modalities=["tabular_grid", "raster_image"],
        compression_sla=sla,
        execution_cost_budget_magnitude=10,
    )
    assert task.target_modalities == ["raster_image", "tabular_grid"]
