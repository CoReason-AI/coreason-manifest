# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from coreason_manifest.spec.ontology import (
    AlgebraicRefinementContract,
    CapabilityForgeTopologyManifest,
    HoareLogicProofReceipt,
    SemanticDiscoveryIntent,
    TeleologicalIsometryReceipt,
    VectorEmbeddingState,
)


def test_teleological_isometry_threshold() -> None:
    source_intent_cid = "intent-id-12345"
    target_intent_vector = VectorEmbeddingState(
        vector_base64="abc", dimensionality=10, foundation_matrix_name="test-model"
    )
    forged_output_vector = VectorEmbeddingState(
        vector_base64="xyz", dimensionality=10, foundation_matrix_name="test-model"
    )

    receipt_passed = TeleologicalIsometryReceipt(
        source_intent_cid=source_intent_cid,
        target_intent_vector=target_intent_vector,
        forged_output_vector=forged_output_vector,
        measured_cosine_similarity=0.90,
        alignment_threshold_passed=True,
    )
    assert receipt_passed.alignment_threshold_passed is True

    receipt_failed = TeleologicalIsometryReceipt(
        source_intent_cid=source_intent_cid,
        target_intent_vector=target_intent_vector,
        forged_output_vector=forged_output_vector,
        measured_cosine_similarity=0.80,
        alignment_threshold_passed=True,
    )
    assert receipt_failed.alignment_threshold_passed is False


def test_hoare_logic_proof_receipt_canonical_sorting() -> None:
    contract_b = AlgebraicRefinementContract(target_property="b_prop", mathematical_predicate="x > 0")
    contract_a = AlgebraicRefinementContract(target_property="a_prop", mathematical_predicate="x < 100")
    contract_c = AlgebraicRefinementContract(target_property="c_prop", mathematical_predicate="x == 5")

    receipt = HoareLogicProofReceipt(
        capability_cid="cap-id-123",
        preconditions=[contract_b, contract_c, contract_a],
        postconditions=[contract_c, contract_a, contract_b],
        proof_system="lean4",
        verified_theorem_hash="a" * 64,
    )

    assert receipt.preconditions[0].target_property == "a_prop"
    assert receipt.preconditions[1].target_property == "b_prop"
    assert receipt.preconditions[2].target_property == "c_prop"

    assert receipt.postconditions[0].target_property == "a_prop"
    assert receipt.postconditions[1].target_property == "b_prop"
    assert receipt.postconditions[2].target_property == "c_prop"


def test_capability_forge_topology_compile() -> None:
    intent = SemanticDiscoveryIntent(
        query_vector=VectorEmbeddingState(vector_base64="abc", dimensionality=10, foundation_matrix_name="test-model"),
        min_isometry_score=0.9,
        required_structural_types=["test"],
    )
    manifest = CapabilityForgeTopologyManifest(
        target_epistemic_deficit=intent,
        generator_node_cid="did:coreason:agent-1",
        formal_verifier_cid="did:coreason:system-1",
        fuzzing_engine_cid="did:coreason:system-2",
        nodes={},
    )

    dag = manifest.compile_to_base_topology()

    assert len(dag.nodes) == 3
    assert "did:coreason:agent-1" in dag.nodes
    assert "did:coreason:system-1" in dag.nodes
    assert "did:coreason:system-2" in dag.nodes

    assert len(dag.edges) == 2

    assert ("did:coreason:agent-1", "did:coreason:system-1") in dag.edges
    assert ("did:coreason:system-1", "did:coreason:system-2") in dag.edges
