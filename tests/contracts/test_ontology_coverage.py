# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DefeasibleCascadeEvent,
    EphemeralNamespacePartitionState,
    LatentScratchpadReceipt,
    SecureSubSessionState,
    ThoughtBranchState,
)


def test_secure_sub_session_state_sort_arrays() -> None:
    session = SecureSubSessionState(
        session_id="session-1",
        allowed_vault_keys=["z-key", "a-key", "m-key"],
        max_ttl_seconds=3600,
        description="Test session",
    )
    assert session.allowed_vault_keys == ["a-key", "m-key", "z-key"]


def test_defeasible_cascade_event_sort_arrays() -> None:
    event = DefeasibleCascadeEvent(
        cascade_id="c1",
        root_falsified_event_id="e1",
        propagated_decay_factor=0.5,
        quarantined_event_ids=["e3", "e1", "e2"],
        cross_boundary_quarantine_issued=True,
    )
    assert event.quarantined_event_ids == ["e1", "e2", "e3"]


def test_latent_scratchpad_receipt_referential_integrity_valid() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    tb2 = ThoughtBranchState(branch_id="b2", latent_content_hash="b" * 64)
    receipt = LatentScratchpadReceipt(
        trace_id="t1",
        explored_branches=[tb2, tb1],
        discarded_branches=["b2"],
        resolution_branch_id="b1",
        total_latent_tokens=100,
    )
    assert receipt.resolution_branch_id == "b1"
    assert receipt.discarded_branches == ["b2"]
    # Verify sorting
    assert receipt.explored_branches[0].branch_id == "b1"
    assert receipt.explored_branches[1].branch_id == "b2"


def test_latent_scratchpad_receipt_invalid_resolution_branch() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    with pytest.raises(ValidationError, match="resolution_branch_id 'b99' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[tb1],
            discarded_branches=[],
            resolution_branch_id="b99",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_invalid_discarded_branch() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    with pytest.raises(ValidationError, match="discarded branch 'b99' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[tb1],
            discarded_branches=["b99"],
            resolution_branch_id="b1",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_sort_discarded_branches() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    tb2 = ThoughtBranchState(branch_id="b2", latent_content_hash="b" * 64)
    tb3 = ThoughtBranchState(branch_id="b3", latent_content_hash="c" * 64)
    receipt = LatentScratchpadReceipt(
        trace_id="t1",
        explored_branches=[tb1, tb2, tb3],
        discarded_branches=["b3", "b1"],
        resolution_branch_id="b2",
        total_latent_tokens=100,
    )
    assert receipt.discarded_branches == ["b1", "b3"]


def test_ephemeral_namespace_partition_state_valid() -> None:
    hash1 = "a" * 64
    hash2 = "b" * 64
    state = EphemeralNamespacePartitionState(
        partition_id="p1",
        execution_runtime="wasm32-wasi",
        authorized_bytecode_hashes=[hash2, hash1],
        max_ttl_seconds=3600,
        max_vram_mb=1024,
    )
    assert state.authorized_bytecode_hashes == [hash1, hash2]


def test_ephemeral_namespace_partition_state_invalid_hash() -> None:
    with pytest.raises(ValidationError, match="Invalid SHA-256 hash in whitelist: invalid-hash"):
        EphemeralNamespacePartitionState(
            partition_id="p1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["invalid-hash"],
            max_ttl_seconds=3600,
            max_vram_mb=1024,
        )

def test_taxonomic_routing_policy_valid_domain_extension() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import TaxonomicRoutingPolicy


    # If no context is provided, it should fail because "ext:custom_intent" is not in allowed_ext_intents
    # Wait, the prompt says "allowed_exts = (info.context or {}).get("allowed_ext_intents", set())"
    # Actually, we can validate with context:
    validated_policy = TaxonomicRoutingPolicy.model_validate(
        {
            "policy_id": "policy-1",
            "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
            "fallback_heuristic": "entity_centric",
        },
        context={"allowed_ext_intents": {"ext:custom_intent"}}
    )
    assert "ext:custom_intent" in validated_policy.intent_to_heuristic_matrix

    with pytest.raises(ValidationError, match="Domain Extension Violation"):
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "policy-1",
                "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
                "fallback_heuristic": "entity_centric",
            },
            context={"allowed_ext_intents": {"ext:other"}}
        )

def test_intent_classification_receipt_sorting() -> None:
    from coreason_manifest.spec.ontology import IntentClassificationReceipt
    receipt = IntentClassificationReceipt(
        primary_intent="informational_inform",
        concurrent_intents={
            "ext:z_intent": 0.5,
            "ext:a_intent": 0.8,
            "semantic_discovery": 0.2
        }
    )
    keys = list(receipt.concurrent_intents.keys())
    assert keys == ["ext:a_intent", "ext:z_intent", "semantic_discovery"]
