import pytest
from coreason_manifest.spec.ontology import DynamicRoutingManifest, GlobalSemanticProfile, BypassReceipt

def test_artifact_routing_manifest_bypass():
    with pytest.raises(ValueError, match="Merkle Violation: BypassReceipt artifact_event_id does not match"):
        DynamicRoutingManifest(
            manifest_id="test",
            branch_budgets_magnitude={},
            artifact_profile=GlobalSemanticProfile(artifact_event_id="e1", detected_modalities=["text"],  token_density=10),
            active_subgraphs={"text": []},
            bypassed_steps=[BypassReceipt(bypassed_node_id="did:abc:123", artifact_event_id="e2e2e2e2", justification="modality_mismatch", cryptographic_null_hash="a"*64)]
        )
