# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.ontology import (
    AgentAttestationReceipt,
    BoundedJSONRPCIntent,
    SemanticDiscoveryIntent,
    ToolInvocationEvent,
    VectorEmbeddingState,
    ZeroKnowledgeReceipt,
)
from coreason_manifest.utils.algebra import extract_mcp_tool_call, wrap_intent_in_jsonrpc


def test_wrap_intent_in_jsonrpc() -> None:
    query_vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")

    intent = SemanticDiscoveryIntent(
        query_vector=query_vector, required_structural_types=["database", "retrieval"], min_isometry_score=0.85
    )

    rpc_intent = wrap_intent_in_jsonrpc(intent, 123)

    assert isinstance(rpc_intent, BoundedJSONRPCIntent)
    assert rpc_intent.jsonrpc == "2.0"
    assert rpc_intent.method == "mcp.intent.semantic_discovery"
    assert rpc_intent.id == 123

    # Assert params is a dictionary containing the serialized keys of the intent
    assert rpc_intent.params is not None
    assert isinstance(rpc_intent.params, dict)

    # Check that keys are present (serialization handles the actual conversion)
    assert "query_vector" in rpc_intent.params
    assert "required_structural_types" in rpc_intent.params
    assert "min_isometry_score" in rpc_intent.params
    assert "type" in rpc_intent.params

    assert rpc_intent.params["min_isometry_score"] == 0.85
    assert rpc_intent.params["required_structural_types"] == ["database", "retrieval"]
    assert rpc_intent.params["type"] == "semantic_discovery"


def test_extract_mcp_tool_call() -> None:
    rpc_intent = BoundedJSONRPCIntent(
        jsonrpc="2.0",
        method="tools/call",
        params={"name": "execute_query", "arguments": {"sql": "SELECT 1"}},
        id=456,
    )

    agent_attestation = AgentAttestationReceipt(
        training_lineage_hash="a" * 64, developer_signature="test-signature", capability_merkle_root="b" * 64
    )

    zk_proof = ZeroKnowledgeReceipt(
        proof_protocol="zk-SNARK", public_inputs_hash="c" * 64, verifier_key_id="key-123", cryptographic_blob="dGVzdA=="
    )

    event = extract_mcp_tool_call(
        rpc_request=rpc_intent,
        event_id="evt-123",
        timestamp=123456789.0,
        agent_attestation=agent_attestation,
        zk_proof=zk_proof,
    )

    assert isinstance(event, ToolInvocationEvent)
    assert event.tool_name == "execute_query"
    assert event.parameters == {"sql": "SELECT 1"}

    # Physical identity checks
    assert event.agent_attestation is agent_attestation
    assert event.zk_proof is zk_proof
