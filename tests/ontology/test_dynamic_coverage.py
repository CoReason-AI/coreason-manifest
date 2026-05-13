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
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DiscourseTreeManifest,
    EpistemicZeroTrustReceipt,
    InterventionReceipt,
    OntologicalAlignmentPolicy,
    RedactionPolicy,
    SemanticClassificationProfile,
    SpatialBillboardContract,
    VectorEmbeddingState,
    WetwareAttestationContract,
)
from coreason_manifest.utils.algebra import calculate_latent_alignment, compute_merkle_directory_cid


def test_intervention_receipt_attestation_nonce_failure() -> None:
    attest = WetwareAttestationContract(
        mechanism="urn:coreason:mech1",
        did_subject="did:example:123",
        cryptographic_payload="ABCD",
        dag_node_nonce="diff-nonce",
        liveness_challenge_hash="a" * 64,
    )
    with pytest.raises(ValueError, match="Anti-Replay Lock Triggered"):
        InterventionReceipt(
            intervention_request_cid="cid112345",
            target_node_cid="did:example:cid212345",
            approved=True,
            feedback=None,
            attestation=attest,
            event_cid="event112345",
            timestamp=123.0,
        )


def test_epistemic_zero_trust_receipt_failure() -> None:
    with pytest.raises(ValidationError, match="2 validation errors for EpistemicZeroTrustReceipt"):
        EpistemicZeroTrustReceipt.model_validate(
            {
                "event_cid": "event112345",
                "timestamp": 123.0,
                "intent_reference_cid": "cid112345",
                "llm_blind_plan_hash": "a" * 64,
                "firewall_breach_detected": True,
                "remediation_epochs_consumed": 1,
            }
        )


def test_billboard_manifold() -> None:
    with pytest.raises(ValidationError, match="1 validation error for SpatialBillboardContract"):
        SpatialBillboardContract(
            anchoring_node_cid="cid1", spherical_cylindrical_lock="none", distance_scaling_factor=1.0
        )


def test_data_sanitization_rule() -> None:
    policy = RedactionPolicy(
        rule_cid="rule1",
        classification=SemanticClassificationProfile.CONFIDENTIAL,
        target_pattern="test",
        target_regex_pattern=".*",
        action="redact",
        context_exclusion_zones=["zone2", "zone1"],
    )
    assert policy.context_exclusion_zones == ["zone1", "zone2"]


def test_discourse_tree_manifest() -> None:
    with pytest.raises(ValueError, match="root_node_cid not found in discourse_nodes"):
        DiscourseTreeManifest(manifest_cid="manifest123", root_node_cid="did:example:123", discourse_nodes={})


def test_algebra_coverage() -> None:
    # Test compute_merkle_directory_cid
    cid = compute_merkle_directory_cid({"file.txt": b"content"})
    assert cid.startswith("sha256:")

    # Test calculate_latent_alignment invalid v2
    v1 = VectorEmbeddingState(
        foundation_matrix_name="matrix1",
        dimensionality=1,
        vector_base64="AAAAAA==",  # valid base64 (4 bytes)
    )
    v2 = VectorEmbeddingState(
        foundation_matrix_name="matrix1",
        dimensionality=1,
        vector_base64="A==",  # invalid base64 (incorrect padding)
    )
    policy = OntologicalAlignmentPolicy(min_cosine_similarity=0.5, require_isometry_proof=False)

    with pytest.raises(ValueError, match=r"Topological Contradiction: Invalid base64 encoding\."):
        calculate_latent_alignment(v1, v2, policy)
