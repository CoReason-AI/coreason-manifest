# Copyright (c) 2026 CoReason, Inc.
# All rights reserved.
# Licensed under the Prosperity Public License 3.0 (the "License")

import pytest
from pydantic import ValidationError
from coreason_manifest.spec.ontology import (
    SpeculativeTokenNode,
    PolicyCoordinates,
    CausalRelationEdge,
    TransmutationReceipt,
)


def test_speculative_token_node_success():
    """Verify that a valid recursive SpeculativeTokenNode is successfully created and parsed."""
    child1 = SpeculativeTokenNode(
        token_id="tok_abc-123",
        token_value="propose",
        logit_probability=0.92,
        validation_status="speculative_draft",
    )
    child2 = SpeculativeTokenNode(
        token_id="tok_def.456",
        token_value="verify",
        logit_probability=0.74,
        validation_status="target_rejected",
    )
    root = SpeculativeTokenNode(
        token_id="tok_root",
        token_value="execute",
        logit_probability=0.88,
        validation_status="target_validated",
        associated_urn="urn:coreason:agent:speculative-prover",
        child_speculations=[child1, child2],
    )

    assert root.token_id == "tok_root"
    assert root.token_value == "execute"
    assert len(root.child_speculations) == 2
    assert root.child_speculations[0].token_id == "tok_abc-123"
    assert root.child_speculations[1].validation_status == "target_rejected"


def test_speculative_token_node_validation_failures():
    """Verify that invalid inputs to SpeculativeTokenNode trigger ValidationErrors."""
    # Invalid token_id regex pattern
    with pytest.raises(ValidationError):
        SpeculativeTokenNode(
            token_id="invalid_prefix_123",
            token_value="value",
            logit_probability=0.5,
            validation_status="speculative_draft",
        )

    # logit_probability out of bounds (> 1.0)
    with pytest.raises(ValidationError):
        SpeculativeTokenNode(
            token_id="tok_valid",
            token_value="value",
            logit_probability=1.05,
            validation_status="speculative_draft",
        )

    # logit_probability out of bounds (< 0.0)
    with pytest.raises(ValidationError):
        SpeculativeTokenNode(
            token_id="tok_valid",
            token_value="value",
            logit_probability=-0.1,
            validation_status="speculative_draft",
        )

    # Invalid Literal validation_status
    with pytest.raises(ValidationError):
        SpeculativeTokenNode(
            token_id="tok_valid",
            token_value="value",
            logit_probability=0.5,
            validation_status="invalid_status",
        )


def test_policy_coordinates_success():
    """Verify that valid PolicyCoordinates are successfully instantiated and bounded."""
    coords = PolicyCoordinates(
        dimension_id="dim_vfe_divergence",
        dimension_name="Variational Free Energy Gap",
        metric_value=0.45,
    )
    assert coords.dimension_id == "dim_vfe_divergence"
    assert coords.metric_value == 0.45


def test_policy_coordinates_failures():
    """Verify that metric_value clamping limits trigger Pydantic ValidationErrors."""
    with pytest.raises(ValidationError):
        PolicyCoordinates(
            dimension_id="dim_valid",
            dimension_name="name",
            metric_value=1.001,
        )

    with pytest.raises(ValidationError):
        PolicyCoordinates(
            dimension_id="dim_valid",
            dimension_name="name",
            metric_value=-0.0001,
        )


def test_causal_relation_edge_success():
    """Verify that valid CausalRelationEdge objects parse successfully."""
    edge = CausalRelationEdge(
        source_node_id="cid_parent_node_123",
        target_node_id="cid_child_node_456",
        relation_type="direct_cause",
    )
    assert edge.relation_type == "direct_cause"
    assert edge.source_node_id == "cid_parent_node_123"


def test_causal_relation_edge_failures():
    """Verify that invalid edge configurations or relations raise ValidationErrors."""
    # Invalid Literal relation_type
    with pytest.raises(ValidationError):
        CausalRelationEdge(
            source_node_id="cid_parent",
            target_node_id="cid_child",
            relation_type="invalid_relation",
        )


def test_transmutation_receipt_success():
    """Verify that valid TransmutationReceipt objects parse successfully."""
    receipt = TransmutationReceipt(
        transaction_id="tx_attestation_8892",
        originating_agent_urn="urn:coreason:agent:security-guardrail:v1",
        zk_snark_proof_hex="0x5f9a2b7c4d...",
        sd_jwt_attestation_hash="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        verification_timestamp="2026-05-23T12:48:43Z",
    )
    assert receipt.transaction_id == "tx_attestation_8892"
    assert receipt.sd_jwt_attestation_hash.startswith("2cf24dba")


def test_transmutation_receipt_failures():
    """Verify that invalid parameters in TransmutationReceipt raise ValidationErrors."""
    # Mismatching transaction_id min_length
    with pytest.raises(ValidationError):
        TransmutationReceipt(
            transaction_id="",
            originating_agent_urn="urn:agent",
            zk_snark_proof_hex="0x123",
            sd_jwt_attestation_hash="hash",
            verification_timestamp="timestamp",
        )
