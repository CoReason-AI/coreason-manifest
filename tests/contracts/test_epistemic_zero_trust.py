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
from authlib.jose import jwt
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CryptographicAttestationReceipt,
    EmpiricalFalsificationContract,
    EpistemicAxiomVerificationReceipt,
    EpistemicConstraintPolicy,
    EpistemicSecurityPolicy,
    EpistemicSecurityProfile,
    EpistemicZeroTrustContract,
    EpistemicZeroTrustReceipt,
    FalsificationContract,
    FederatedHandshakeIntent,
    FormalVerificationContract,
    PostQuantumSignatureReceipt,
)
from coreason_manifest.utils.mcp_adapters import DecentralizedIdentityGateway


def test_epistemic_constraint_policy_valid() -> None:
    policy = EpistemicConstraintPolicy(
        assertion_ast="outputs == inputs", remediation_prompt="Outputs must match inputs length."
    )
    assert policy.assertion_ast == "outputs == inputs"


def test_epistemic_constraint_policy_kinetic_call() -> None:
    with pytest.raises(ValidationError, match="Kinetic execution bleed detected"):
        EpistemicConstraintPolicy(assertion_ast="print('hello')", remediation_prompt="test")


def test_epistemic_constraint_policy_invalid_syntax() -> None:
    with pytest.raises(ValidationError, match="Invalid syntax in constraint AST"):
        EpistemicConstraintPolicy(assertion_ast="len( == 2", remediation_prompt="test")


def test_epistemic_zero_trust_contract_sort() -> None:
    p1 = EpistemicConstraintPolicy(assertion_ast="x == 2", remediation_prompt="test")
    p2 = EpistemicConstraintPolicy(assertion_ast="a == 1", remediation_prompt="test")

    contract = EpistemicZeroTrustContract(
        intent_id="intent-1",
        semantic_planning_task="Task",
        schema_blueprint_name="blueprint_1",
        structural_pre_conditions=[p1, p2],
        structural_post_conditions=[p1, p2],
    )

    assert contract.structural_pre_conditions[0].assertion_ast == "a == 1"
    assert contract.structural_pre_conditions[1].assertion_ast == "x == 2"
    assert contract.structural_post_conditions[0].assertion_ast == "a == 1"
    assert contract.structural_post_conditions[1].assertion_ast == "x == 2"


def test_epistemic_zero_trust_receipt_firewall_breach() -> None:
    with pytest.raises(ValidationError, match="Input should be False"):
        EpistemicZeroTrustReceipt(
            event_cid="receipt-1",
            timestamp=123.0,
            intent_reference_id="intent-1",
            llm_blind_plan_hash="a" * 64,
            remediation_epochs_consumed=2,
            transmuted_payload_hash="b" * 64,
            firewall_breach_detected=True,  # type: ignore
        )


def test_epistemic_constraint_policy_invalid_type() -> None:
    with pytest.raises(ValidationError):
        EpistemicConstraintPolicy(assertion_ast=123, remediation_prompt="test")  # type: ignore


def test_epistemic_zero_trust_receipt_firewall_breach_bypass() -> None:
    receipt = EpistemicZeroTrustReceipt(
        event_cid="receipt-1",
        timestamp=123.0,
        intent_reference_id="intent-1",
        llm_blind_plan_hash="a" * 64,
        remediation_epochs_consumed=2,
        transmuted_payload_hash="b" * 64,
    )

    # Force bypass the Literal validation to hit the model_validator
    object.__setattr__(receipt, "firewall_breach_detected", True)

    with pytest.raises(ValueError, match=r"Topological Collapse: Firewall breach detected\. Receipt invalid\."):
        receipt.verify_firewall_integrity()  # type: ignore[operator]


def test_epistemic_axiom_guillotine() -> None:
    with pytest.raises(
        ValidationError,
        match=r"Proof-Carrying Data required: Cannot verify axiom without a formal_backing_receipt_cid\.",
    ):
        EpistemicAxiomVerificationReceipt(
            event_cid="receipt-1",
            timestamp=123.0,
            source_prediction_cid="did:coreason:agent-1",
            sequence_similarity_score=0.9,
            fact_score_passed=True,
            formal_backing_receipt_cid=None,
        )


def test_formal_verification_contract_pointer() -> None:
    contract = FormalVerificationContract(
        proof_system="lean4",
        invariant_theorem="theorem1",
        compiled_proof_hash="a" * 64,
        verified_receipt_cid="did:coreason:receipt-1",
    )
    assert contract.verified_receipt_cid == "did:coreason:receipt-1"


def test_falsification_contract_instantiation() -> None:
    contract = FalsificationContract(
        target_hypothesis_cid="did:coreason:hyp-1", counter_model_receipt_cid="did:coreason:receipt-1"
    )
    assert contract.target_hypothesis_cid == "did:coreason:hyp-1"
    assert contract.counter_model_receipt_cid == "did:coreason:receipt-1"


def test_empirical_falsification_contract_instantiation() -> None:
    contract = EmpiricalFalsificationContract(
        condition_cid="condition-1", description="Test condition", falsifying_observation_signature="error.*"
    )
    assert contract.condition_cid == "condition-1"
    assert contract.falsifying_observation_signature == "error.*"


def test_volumetric_fuzzing_sd_jwt_payload_too_long() -> None:
    with pytest.raises(ValidationError):
        CryptographicAttestationReceipt(
            issuer_did="did:coreason:issuer-1",
            subject_did="did:coreason:subject-1",
            sd_jwt_payload="a.b.c" + "x" * 500000,
            pqc_signature=None,
        )


def test_volumetric_fuzzing_sd_jwt_payload_malformed() -> None:
    with pytest.raises(ValidationError):
        CryptographicAttestationReceipt(
            issuer_did="did:coreason:issuer-1",
            subject_did="did:coreason:subject-1",
            sd_jwt_payload="invalid_token",
            pqc_signature=None,
        )


def test_federated_handshake_intent_sorts_requested_scopes() -> None:
    attestation = CryptographicAttestationReceipt(
        issuer_did="did:coreason:issuer-1",
        subject_did="did:coreason:subject-1",
        sd_jwt_payload="header.payload.signature",
        pqc_signature=None,
    )
    intent = FederatedHandshakeIntent(
        initiator_node_cid="did:coreason:subject-1",
        target_node_cid="did:coreason:target-1",
        attestation=attestation,
        requested_scopes=["scope_b", "scope_a", "scope_c"],
    )
    assert intent.requested_scopes == ["scope_a", "scope_b", "scope_c"]


def test_gateway_severance_did_resolution_failed() -> None:
    profile = EpistemicSecurityProfile(
        epistemic_security=EpistemicSecurityPolicy.STANDARD, network_isolation=False, egress_obfuscation=False
    )
    gateway = DecentralizedIdentityGateway(security_profile=profile, trusted_issuers={"did:coreason:issuer-1": "key"})

    attestation = CryptographicAttestationReceipt(
        issuer_did="did:coreason:unknown",
        subject_did="did:coreason:subject-1",
        sd_jwt_payload="header.payload.signature",
        pqc_signature=None,
    )
    intent = FederatedHandshakeIntent(
        initiator_node_cid="did:coreason:subject-1",
        target_node_cid="did:coreason:target-1",
        attestation=attestation,
        requested_scopes=["scope_a"],
    )

    with pytest.raises(PermissionError) as excinfo:
        gateway.process_handshake(intent)
    assert "did_resolution_failed" in str(excinfo.value)


def test_gateway_severance_sd_jwt_tampered() -> None:
    profile = EpistemicSecurityProfile(
        epistemic_security=EpistemicSecurityPolicy.STANDARD, network_isolation=False, egress_obfuscation=False
    )
    # create a basic symmetric key jwt just to have something decodable or failing decoding
    gateway = DecentralizedIdentityGateway(
        security_profile=profile, trusted_issuers={"did:coreason:issuer-1": "secret-key"}
    )

    attestation = CryptographicAttestationReceipt(
        issuer_did="did:coreason:issuer-1",
        subject_did="did:coreason:subject-1",
        sd_jwt_payload="header.payload.signature",
        pqc_signature=None,
    )
    intent = FederatedHandshakeIntent(
        initiator_node_cid="did:coreason:subject-1",
        target_node_cid="did:coreason:target-1",
        attestation=attestation,
        requested_scopes=["scope_a"],
    )

    with pytest.raises(PermissionError) as excinfo:
        gateway.process_handshake(intent)
    assert "sd_jwt_tampered" in str(excinfo.value)


def test_gateway_severance_pqc_signature_invalid() -> None:
    profile = EpistemicSecurityProfile(
        epistemic_security=EpistemicSecurityPolicy.CONFIDENTIAL, network_isolation=True, egress_obfuscation=True
    )

    import time

    exp_time = int(time.time()) + 3600
    header = {"alg": "HS256"}
    payload = {"sub": "did:coreason:subject-1", "iss": "did:coreason:issuer-1", "exp": exp_time}
    valid_jwt = jwt.encode(header, payload, "secret-key").decode("utf-8")

    gateway = DecentralizedIdentityGateway(
        security_profile=profile, trusted_issuers={"did:coreason:issuer-1": "secret-key"}
    )

    attestation = CryptographicAttestationReceipt(
        issuer_did="did:coreason:issuer-1",
        subject_did="did:coreason:subject-1",
        sd_jwt_payload=valid_jwt,
        pqc_signature=None,
    )
    intent = FederatedHandshakeIntent(
        initiator_node_cid="did:coreason:subject-1",
        target_node_cid="did:coreason:target-1",
        attestation=attestation,
        requested_scopes=["scope_a"],
    )

    with pytest.raises(PermissionError) as excinfo:
        gateway.process_handshake(intent)
    assert "pqc_signature_invalid" in str(excinfo.value)


def test_gateway_severance_pqc_signature_valid() -> None:
    profile = EpistemicSecurityProfile(
        epistemic_security=EpistemicSecurityPolicy.CONFIDENTIAL, network_isolation=True, egress_obfuscation=True
    )

    import time

    exp_time = int(time.time()) + 3600
    header = {"alg": "HS256"}
    payload = {"sub": "did:coreason:subject-1", "iss": "did:coreason:issuer-1", "exp": exp_time}
    valid_jwt = jwt.encode(header, payload, "secret-key").decode("utf-8")

    gateway = DecentralizedIdentityGateway(
        security_profile=profile, trusted_issuers={"did:coreason:issuer-1": "secret-key"}
    )

    pqc = PostQuantumSignatureReceipt(
        pq_algorithm="ml-dsa-44", pq_signature_blob="a" * 100, public_key_cid="did:coreason:issuer-1"
    )

    attestation = CryptographicAttestationReceipt(
        issuer_did="did:coreason:issuer-1",
        subject_did="did:coreason:subject-1",
        sd_jwt_payload=valid_jwt,
        pqc_signature=pqc,
    )
    intent = FederatedHandshakeIntent(
        initiator_node_cid="did:coreason:subject-1",
        target_node_cid="did:coreason:target-1",
        attestation=attestation,
        requested_scopes=["scope_a"],
    )

    # Should not raise
    assert gateway.process_handshake(intent)
