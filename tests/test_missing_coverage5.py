import pytest
from coreason_manifest.spec.ontology import DynamicRoutingManifest, GlobalSemanticProfile, GlobalSemanticProfile, TemporalCheckpointState

def test_artifact_routing_manifest_modality():
    with pytest.raises(ValueError, match="Epistemic Violation: Cannot route to subgraph"):
        DynamicRoutingManifest(
            manifest_id="test", branch_budgets_magnitude={},
            artifact_profile=GlobalSemanticProfile(artifact_event_id="e1", detected_modalities=["text"],  token_density=10),
            active_subgraphs={"video": []}
        )
