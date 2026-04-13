import pytest

from coreason_manifest.spec.ontology import (
    TemporalConflictResolutionPolicy,
    TemporalEdgeInvalidationIntent,
    TemporalGraphCRDTManifest,
    _DNS_CACHE,
    _validate_ssrf_safety,
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


def test_ssrf_quarantine_mock() -> None:
    import socket
    from unittest.mock import patch

    with patch("socket.getaddrinfo", side_effect=socket.gaierror("mocked error")):
        _DNS_CACHE.cache.clear()
        with pytest.raises(ValueError, match=r"Unresolvable or invalid host: some-other-domain\.com"):
            _validate_ssrf_safety("http://some-other-domain.com")


def test_ssrf_quarantine_mock_bypass() -> None:
    import socket
    from unittest.mock import patch

    with patch("socket.getaddrinfo", side_effect=socket.gaierror("mocked error")):
        _DNS_CACHE.cache.clear()

        # Test success (example.com) - this should not raise because of our explicit bypass
        _validate_ssrf_safety("http://example.com")

        # Test success (unresolvable.domain.com) - this should raise because it's set to "unresolvable"
        with pytest.raises(ValueError, match=r"Unresolvable or invalid host: unresolvable\.domain\.com"):
            _validate_ssrf_safety("http://unresolvable.domain.com")


def test_temporal_conflict_resolution() -> None:
    policy = TemporalConflictResolutionPolicy(merge_algebra="lamport_dominance")
    assert policy.merge_algebra == "lamport_dominance"
    assert policy.enforce_idempotence
