# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>


from coreason_manifest.spec.ontology import (
    TemporalConflictResolutionPolicy,
    TemporalEdgeInvalidationIntent,
    TemporalGraphCRDTManifest,
)


def test_temporal_crdt_manifest_sorts_correctly() -> None:
    intent1 = TemporalEdgeInvalidationIntent(
        target_edge_cid="did:coreason:edge-B",
        invalidation_timestamp=1700000000.0,
        causal_justification_cid="did:coreason:obs-1",
    )

    intent2 = TemporalEdgeInvalidationIntent(
        target_edge_cid="did:coreason:edge-A",
        invalidation_timestamp=1700000000.0,
        causal_justification_cid="did:coreason:obs-1",
    )

    manifest = TemporalGraphCRDTManifest(
        diff_cid="did:coreason:diff-1",
        author_node_cid="did:coreason:agent-1",
        lamport_timestamp=1,
        vector_clock={"did:coreason:agent-1": 1},
        add_set=["did:coreason:node-Z", "did:coreason:node-A"],
        terminate_set=[intent1, intent2],
    )

    assert manifest.add_set == ["did:coreason:node-A", "did:coreason:node-Z"]
    assert manifest.terminate_set[0].target_edge_cid == "did:coreason:edge-A"
    assert manifest.terminate_set[1].target_edge_cid == "did:coreason:edge-B"


def test_temporal_conflict_resolution() -> None:
    policy = TemporalConflictResolutionPolicy(merge_algebra="lamport_dominance")
    assert policy.merge_algebra == "lamport_dominance"
    assert policy.enforce_idempotence
