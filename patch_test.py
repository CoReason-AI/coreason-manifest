with open("tests/contracts/test_epistemic_zero_trust.py", "r") as f:
    content = f.read()

new_content = content + """
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

    with pytest.raises(ValueError, match="Topological Collapse: Firewall breach detected. Receipt invalid."):
        receipt.verify_firewall_integrity()

"""

with open("tests/contracts/test_epistemic_zero_trust.py", "w") as f:
    f.write(new_content)
