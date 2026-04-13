from coreason_manifest.spec.ontology import TemporalGraphCRDTManifest, TemporalEdgeInvalidationIntent
from typing import Any

def test_temporal_crdt_manifest_sorts_correctly() -> None:
    intent1 = TemporalEdgeInvalidationIntent(
        target_edge_cid="did:coreason:edge-B",
        invalidation_timestamp=1700000000.0,
        causal_justification_cid="did:coreason:obs-1"
    )

    intent2 = TemporalEdgeInvalidationIntent(
        target_edge_cid="did:coreason:edge-A",
        invalidation_timestamp=1700000000.0,
        causal_justification_cid="did:coreason:obs-1"
    )

    manifest = TemporalGraphCRDTManifest(
        diff_cid="did:coreason:diff-1",
        author_node_cid="did:coreason:agent-1",
        lamport_timestamp=1,
        vector_clock={"did:coreason:agent-1": 1},
        add_set=["did:coreason:node-Z", "did:coreason:node-A"],
        terminate_set=[intent1, intent2]
    )

    assert manifest.add_set == ["did:coreason:node-A", "did:coreason:node-Z"]
    assert manifest.terminate_set[0].target_edge_cid == "did:coreason:edge-A"
    assert manifest.terminate_set[1].target_edge_cid == "did:coreason:edge-B"
