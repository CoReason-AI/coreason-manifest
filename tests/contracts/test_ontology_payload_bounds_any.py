from coreason_manifest.spec.ontology import (
    BargeInInterruptEvent,
    BaseNodeProfile,
    BoundedJSONRPCIntent,
    DraftingIntent,
    EscalationIntent,
    MCPPromptReferenceState,
    VerifiableCredentialPresentationReceipt,
)


def test_bounded_json_rpc_intent_payload_coverage() -> None:
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"key": "value"})
    assert intent.params == {"key": "value"}


def test_drafting_intent_payload_coverage() -> None:
    intent = DraftingIntent(context_prompt="test", resolution_schema={"type": "string"}, timeout_action="terminate")
    assert intent.resolution_schema == {"type": "string"}


def test_barge_in_interrupt_event_payload_coverage() -> None:
    event = BargeInInterruptEvent(
        target_event_id="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi1234567890",
        epistemic_disposition="discard",
        retained_partial_payload={"key": "value"},
        timestamp=100.0,
        event_id="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi1234567890",
    )
    assert event.retained_partial_payload == {"key": "value"}


def test_escalation_intent_payload_coverage() -> None:
    intent = EscalationIntent(
        tripped_rule_id="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi1234567890",
        resolution_schema={"type": "string"},
        timeout_action="terminate",
    )
    assert intent.resolution_schema == {"type": "string"}


def test_base_node_profile_payload_coverage() -> None:
    profile = BaseNodeProfile(description="test", domain_extensions={"key": "value"})
    assert profile.domain_extensions == {"key": "value"}


def test_mcp_prompt_reference_state_payload_coverage() -> None:
    state = MCPPromptReferenceState(server_id="test", prompt_name="test", arguments={"key": "value"})
    assert state.arguments == {"key": "value"}


def test_verifiable_credential_presentation_receipt_payload_coverage() -> None:
    receipt = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:coreason:agent-1",
        cryptographic_proof_blob="test",
        authorization_claims={"clearance": "RESTRICTED"},
    )
    assert receipt.authorization_claims == {"clearance": "RESTRICTED"}
