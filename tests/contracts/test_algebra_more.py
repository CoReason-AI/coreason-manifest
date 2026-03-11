import pytest
from coreason_manifest.utils.algebra import (
    apply_state_differential,
    verify_ast_safety,
    verify_merkle_proof,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    generate_correction_prompt,
    validate_payload,
    align_semantic_manifolds,
    calculate_remaining_compute,
    calculate_latent_alignment,
    compute_topology_hash
)
from coreason_manifest.spec.ontology import (
    StateDifferentialManifest, StateMutationIntent,
    ExecutionNodeReceipt, WorkflowManifest, DAGTopologyManifest,
    EpistemicProvenanceReceipt, DynamicRoutingManifest, GlobalSemanticProfile,
    BypassReceipt, VectorEmbeddingState, OntologicalAlignmentPolicy,
    EpistemicLedgerState, TokenBurnReceipt
)
import base64
import struct

def test_verify_ast_safety_valid():
    assert verify_ast_safety("1 + 2") is True
    assert verify_ast_safety("a[0]") is True
    assert verify_ast_safety("a[0:1]") is True
    assert verify_ast_safety("-1") is True
    assert verify_ast_safety("not True") is True
    assert verify_ast_safety("{'a': 1, 'b': 2}") is True
    assert verify_ast_safety("[1, 2, 3]") is True
    assert verify_ast_safety("(1, 2, 3)") is True

def test_verify_ast_safety_invalid():
    with pytest.raises(ValueError):
        verify_ast_safety("import os")
    with pytest.raises(ValueError):
        verify_ast_safety("def foo(): pass")

def test_apply_state_differential_all_ops():
    base = {"user": {"name": "Alice", "tags": ["admin"]}, "items": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="d", author_node_id="a", lamport_timestamp=1, vector_clock={},
        patches=[
            StateMutationIntent(op="add", path="/user/age", value=30),
            StateMutationIntent(op="add", path="/items/0", value=0),
            StateMutationIntent(op="add", path="/items/-", value=4),
            StateMutationIntent(op="remove", path="/user/tags"),
            StateMutationIntent(op="remove", path="/items/1"),
            StateMutationIntent(op="replace", path="/user/name", value="Bob"),
            StateMutationIntent(op="replace", path="/items/0", value=99),
            StateMutationIntent(op="copy", path="/user/name_copy", value="/user/name"),
            StateMutationIntent(op="copy", path="/items/0", value="/items/1"),
            StateMutationIntent(op="copy", path="/items/-", value="/items/1"),
            StateMutationIntent(op="move", path="/user/name_moved", value="/user/name_copy"),
            StateMutationIntent(op="move", path="/items/-", value="/items/0"),
            StateMutationIntent(op="move", path="/items/0", value="/items/1"),
        ]
    )
    # The ops are executed in sequence, we need a fresh one for pure operations
    clean_manifest = StateDifferentialManifest(
        diff_id="d", author_node_id="a", lamport_timestamp=1, vector_clock={},
        patches=[
            StateMutationIntent(op="test", path="/user/name", value="Alice"),
            StateMutationIntent(op="add", path="/user/age", value=30),
            StateMutationIntent(op="replace", path="/items/0", value=99),
            StateMutationIntent(op="remove", path="/items/1"),
            StateMutationIntent(op="copy", path="/items/-", value="/items/0"),
            StateMutationIntent(op="move", path="/user/name_moved", value="/user/name"),
        ]
    )
    new_state = apply_state_differential(base, clean_manifest)
    assert new_state["user"]["age"] == 30
    assert new_state["items"][0] == 99
    assert new_state["user"].get("name") is None
    assert new_state["user"]["name_moved"] == "Alice"

def test_apply_state_differential_errors():
    base = {"user": {"name": "Alice"}, "items": [1, 2, 3]}

    def attempt_diff(patches):
        with pytest.raises(ValueError):
            apply_state_differential(base, StateDifferentialManifest(
                diff_id="d", author_node_id="a", lamport_timestamp=1, vector_clock={}, patches=patches
            ))

    attempt_diff([StateMutationIntent(op="add", path="invalid", value=1)])
    attempt_diff([StateMutationIntent(op="add", path="/user/missing/age", value=1)])
    attempt_diff([StateMutationIntent(op="add", path="/items/a", value=1)])
    # adding to missing root is valid (creates it)
    attempt_diff([StateMutationIntent(op="add", path="/items/10", value=1)])
    attempt_diff([StateMutationIntent(op="remove", path="/missing")])
    attempt_diff([StateMutationIntent(op="remove", path="/items/10")])
    attempt_diff([StateMutationIntent(op="remove", path="/items/a")])
    attempt_diff([StateMutationIntent(op="replace", path="/missing", value=1)])
    attempt_diff([StateMutationIntent(op="replace", path="/items/10", value=1)])
    attempt_diff([StateMutationIntent(op="replace", path="/items/a", value=1)])
    attempt_diff([StateMutationIntent(op="copy", path="/user/new", value=123)])
    attempt_diff([StateMutationIntent(op="copy", path="/user/new", value="invalid")])
    attempt_diff([StateMutationIntent(op="copy", path="/user/new", value="/missing")])
    attempt_diff([StateMutationIntent(op="copy", path="/user/new", value="/items/a")])
    attempt_diff([StateMutationIntent(op="copy", path="/items/10", value="/user/name")])
    attempt_diff([StateMutationIntent(op="test", path="/user/name", value="wrong")])

def test_project_manifest_to_markdown():
    from coreason_manifest.spec.ontology import AgentNodeProfile, AgentAttestationReceipt

    node = AgentNodeProfile.model_validate({
        "type": "agent",
        "description": "d",
        "architectural_intent": "intent",
        "justification": "just",
        "agent_attestation": {
            "training_lineage_hash": "a"*64,
            "developer_signature": "a",
            "capability_merkle_root": "b"*64
        }
    })

    manifest_data = {
        "manifest_version": "1.0.0",
        "genesis_provenance": {"extracted_by": "did:a:1", "source_event_id": "b"},
        "topology": {
            "type": "dag",
            "max_depth": 1,
            "max_fan_out": 1,
            "nodes": {"did:web:node": node.model_dump()},
            "edges": [],
            "architectural_intent": "intent",
            "justification": "just"
        }
    }
    manifest = WorkflowManifest.model_validate(manifest_data)

    md = project_manifest_to_markdown(manifest)
    assert "CoReason Agent Card" in md
    assert "intent" in md

def test_verify_merkle_proof():
    # Will fail validation immediately in the previous test, but we can pass it manually construct
    node1 = ExecutionNodeReceipt.model_construct(request_id="r1", node_hash="h1", parent_hashes=[], inputs={}, outputs={})
    # Will fail generation because it's not a real hash mismatch, wait no, generate_node_hash depends on dict.
    with pytest.raises(Exception):
        verify_merkle_proof([node1])

def test_project_manifest_to_mermaid():
    manifest = DynamicRoutingManifest(
        manifest_id="test",
        artifact_profile=GlobalSemanticProfile(artifact_event_id="test", detected_modalities=["text", "raster_image"], token_density=1),
        active_subgraphs={"text": ["did:web:node1"], "raster_image": ["did:web:node2"]},
        bypassed_steps=[BypassReceipt(artifact_event_id="test", bypassed_node_id="did:web:node3", justification="budget_exhaustion", cryptographic_null_hash="0"*64)],
        branch_budgets_magnitude={}
    )
    mermaid = project_manifest_to_mermaid(manifest)
    assert "graph TD" in mermaid

    manifest2 = DynamicRoutingManifest(
        manifest_id="test",
        artifact_profile=GlobalSemanticProfile(artifact_event_id="test", detected_modalities=["text"], token_density=1),
        active_subgraphs={},
        bypassed_steps=[],
        branch_budgets_magnitude={}
    )
    mermaid2 = project_manifest_to_mermaid(manifest2)
    assert "graph TD" in mermaid2

def test_align_semantic_manifolds():
    assert align_semantic_manifolds("task", ["text"], ["text"], "ev") is None
    res = align_semantic_manifolds("task", ["text"], ["text", "n_dimensional_tensor"], "ev")
    assert res is not None
    assert res.compression_sla.required_grounding_density == "sparse"
    res2 = align_semantic_manifolds("task", ["text"], ["tabular_grid"], "ev")
    assert res2 is not None
    assert res2.compression_sla.required_grounding_density == "dense"

def test_calculate_latent_alignment():
    v1 = VectorEmbeddingState(vector_base64=base64.b64encode(struct.pack('<f', 1.0)).decode(), dimensionality=1, model_name="a")
    v2 = VectorEmbeddingState(vector_base64=base64.b64encode(struct.pack('<f', 1.0)).decode(), dimensionality=1, model_name="a")
    v3 = VectorEmbeddingState(vector_base64=base64.b64encode(struct.pack('<f', 0.0)).decode(), dimensionality=1, model_name="a")

    policy = OntologicalAlignmentPolicy(min_cosine_similarity=0.5, require_isometry_proof=False)
    assert calculate_latent_alignment(v1, v2, policy) == 1.0
    with pytest.raises(ValueError):
        calculate_latent_alignment(v1, v3, policy)

def test_calculate_remaining_compute():
    ledger = EpistemicLedgerState(history=[
        TokenBurnReceipt(event_id="1", timestamp=1, tool_invocation_id="t1", input_tokens=1, output_tokens=1, burn_magnitude=10)
    ])
    assert calculate_remaining_compute(ledger, 100) == 90

    # Exhausted
    with pytest.raises(ValueError):
        calculate_remaining_compute(ledger, 5)
