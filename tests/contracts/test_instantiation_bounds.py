import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ConceptBottleneckPolicy,
    DAGTopologyManifest,
    EpistemicProvenanceReceipt,
    TokenMergingPolicy,
    WorkflowManifest,
)


def test_concept_bottleneck_zero_variance() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ConceptBottleneckPolicy(
            explanation_modality="contrastive", required_concept_vector={"concept_a": True}, bottleneck_temperature=0.1
        )
    assert "bottleneck_temperature" in str(exc_info.value)


def test_workflow_manifest_cryptographic_regex() -> None:
    # A base provenance for the DAG
    provenance = EpistemicProvenanceReceipt(extracted_by="did:agent:node-123", source_event_id="evt-456")

    # A base topology for the manifest
    topology = DAGTopologyManifest(type="dag", edges=[], allow_cycles=False, max_depth=10, max_fan_out=10, nodes={})

    # Sub-Test A - Length Bound
    with pytest.raises(ValidationError) as exc_info:
        WorkflowManifest(
            genesis_provenance=provenance,
            manifest_version="1.0.0",
            topology=topology,
            global_system_prompt_hash="a" * 63,  # 63 characters
        )
    assert "global_system_prompt_hash" in str(exc_info.value)

    # Sub-Test B - Regex Bound
    with pytest.raises(ValidationError) as exc_info2:
        WorkflowManifest(
            genesis_provenance=provenance,
            manifest_version="1.0.0",
            topology=topology,
            global_system_prompt_hash="g" * 64,  # invalid hex character 'g'
        )
    assert "global_system_prompt_hash" in str(exc_info2.value)


def test_token_merging_geometric_bounds() -> None:
    # Sub-Test A - Starvation
    with pytest.raises(ValidationError) as exc_info:
        TokenMergingPolicy(
            metric="cosine_similarity",
            matching_algorithm="bipartite_soft_matching",
            target_compression_ratio=0.5,
            layer_whitelist=[],
        )
    assert "layer_whitelist" in str(exc_info.value)

    # Sub-Test B - Negative Physics
    with pytest.raises(ValidationError) as exc_info2:
        TokenMergingPolicy(
            metric="cosine_similarity",
            matching_algorithm="bipartite_soft_matching",
            target_compression_ratio=0.5,
            layer_whitelist=[-1],
        )
    assert "layer_whitelist" in str(exc_info2.value)
