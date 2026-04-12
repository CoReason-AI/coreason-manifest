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
    EpistemicAxiomVerificationReceipt,
    EpistemicConstraintPolicy,
    EpistemicZeroTrustContract,
    EpistemicZeroTrustReceipt,
    FormalVerificationContract,
)


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
