with open("tests/contracts/test_epistemic_zero_trust.py", "r") as f:
    content = f.read()

new_content = """import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EpistemicConstraintPolicy,
    EpistemicZeroTrustContract,
    EpistemicZeroTrustReceipt,
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
"""

with open("tests/contracts/test_epistemic_zero_trust.py", "w") as f:
    f.write(new_content)
