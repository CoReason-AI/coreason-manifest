# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest

from coreason_manifest.spec.ontology import (
    BeliefMutationEvent,
    DefeasibleCascadeEvent,
    DerivationMode,
    EpistemicLedgerState,
    EpistemicProvenanceReceipt,
    ObservationEvent,
    SemanticNodeState,
)


def test_sybil_resistance() -> None:
    # Write a Pytest asserting that a BeliefMutationEvent fails validation if quorum_signatures contains duplicate strings.
    with pytest.raises(ValueError, match=r"Sybil Attack Detected: Duplicate signatures found in quorum\."):
        BeliefMutationEvent(
            event_cid="test-event-1", timestamp=0.0, payload={}, quorum_signatures=["sig1", "sig2", "sig1"]
        )


def test_defeasible_quarantine() -> None:
    # Write a Pytest proving that an EpistemicLedgerState crashes if a key in defeasible_claims is also listed in the quarantined_event_cids of an active cascade.

    with pytest.raises(
        ValueError, match=r"Epistemic Contagion Detected: Quarantined node found in active defeasible claims\."
    ):
        EpistemicLedgerState(
            history=[],
            defeasible_claims={
                "claim1": SemanticNodeState(
                    node_cid="claim1",
                    label="test",
                    text_chunk="test",
                    provenance=EpistemicProvenanceReceipt(
                        source_event_cid="test_event",
                        extracted_by="did:coreason:agent-1",
                        derivation_mode=DerivationMode.DIRECT_TRANSLATION,
                    ),
                )
            },
            active_cascades=[
                DefeasibleCascadeEvent(
                    cascade_cid="cascade1",
                    root_falsified_event_cid="root_event",
                    propagated_decay_factor=0.5,
                    quarantined_event_cids=["claim1"],
                )
            ],
        )


def test_merkle_chain() -> None:
    # Write a Pytest proving that an EpistemicLedgerState rejects a history array where the second event lacks a prior_event_hash.

    with pytest.raises(ValueError, match="Merkle Chain Broken: Event missing prior_event_hash"):
        EpistemicLedgerState(
            history=[
                ObservationEvent(event_cid="event1", timestamp=1.0, payload={}),
                ObservationEvent(event_cid="event2", timestamp=2.0, payload={}, prior_event_hash=None),
            ]
        )
