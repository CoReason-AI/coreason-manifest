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
    ContinuousObservationStream,
    DAGTopologyManifest,
    EpistemicLedgerState,
    ObservationEvent,
    SpeculativeExecutionBoundary,
    StreamingDisfluencyContract,
    SystemNodeProfile,
)


def test_continuous_observation_stream() -> None:
    stream = ContinuousObservationStream(
        stream_id="stream-123",
        token_buffer=["c", "b", "a"],
        temporal_decay_matrix={1: 0.5},
        latest_confidence_score=0.9,
    )
    assert stream.stream_id == "stream-123"
    # Token buffer should NOT be sorted because of topological exemption!
    assert stream.token_buffer == ["c", "b", "a"]


def test_streaming_disfluency_contract() -> None:
    contract = StreamingDisfluencyContract(repair_marker_regex=".*", decay_threshold=0.5, max_lookback_window=10)
    assert contract.repair_marker_regex == ".*"
    assert contract.decay_threshold == 0.5
    assert contract.max_lookback_window == 10


def test_speculative_execution_boundary() -> None:
    boundary = SpeculativeExecutionBoundary(
        boundary_id="bound-123",
        commit_probability=0.5,
        rollback_pointers=["pointer-b", "pointer-a"],
        competing_hypotheses=["hyp-b", "hyp-a"],
    )
    assert boundary.boundary_id == "bound-123"
    assert boundary.commit_probability == 0.5
    # Should be sorted
    assert boundary.rollback_pointers == ["pointer-a", "pointer-b"]
    assert boundary.competing_hypotheses == ["hyp-a", "hyp-b"]


def test_dag_topology_manifest_speculative_boundaries() -> None:
    boundary_b = SpeculativeExecutionBoundary(boundary_id="b-bound", commit_probability=0.5)
    boundary_a = SpeculativeExecutionBoundary(boundary_id="a-bound", commit_probability=0.5)

    node_a = SystemNodeProfile(description="node a for test")
    node_b = SystemNodeProfile(description="node b for test")

    manifest = DAGTopologyManifest(
        nodes={"did:test:node-id-a": node_a, "did:test:node-id-b": node_b},
        speculative_boundaries=[boundary_b, boundary_a],
        max_depth=10,
        max_fan_out=10,
    )
    # Should be sorted
    assert manifest.speculative_boundaries[0].boundary_id == "a-bound"
    assert manifest.speculative_boundaries[1].boundary_id == "b-bound"


def test_epistemic_ledger_state() -> None:
    event = ObservationEvent(event_id="obs-1", timestamp=100.0, payload={"data": "test"})
    ledger = EpistemicLedgerState(history=[event], retracted_nodes=["node-b", "node-a"])
    assert ledger.retracted_nodes == ["node-a", "node-b"]
