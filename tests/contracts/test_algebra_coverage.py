# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import base64
import contextlib
import struct
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    TemporalGraphCRDTManifest,
    TemporalEdgeInvalidationIntent,
    BypassReceipt,
    DAGTopologyManifest,
    DynamicRoutingManifest,
    GlobalSemanticProfile,
    OntologicalAlignmentPolicy,
    StateMutationIntent,
    VectorEmbeddingState,
    WorkflowManifest,
)
from coreason_manifest.utils.algebra import (
    align_semantic_manifolds,
    calculate_latent_alignment,
    calculate_remaining_compute,
    compute_topology_hash,
    get_ontology_schema,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    synthesize_remediation_intent,
    transmute_temporal_crdt,
    verify_ast_safety,
    verify_manifold_bounds,
    verify_merkle_proof,
)









def test_project_mermaid_active_subgraph() -> None:
    manifest = Mock()
    manifest.manifest_cid = "m1"
    manifest.artifact_profile.detected_modalities = ["text"]
    manifest.active_subgraphs = {"text": ["did:node:1"]}
    manifest.bypassed_steps = []
    res = project_manifest_to_mermaid(manifest)
    assert "did_node_1" in res


def test_get_ontology_schema() -> None:
    schema = get_ontology_schema()
    assert isinstance(schema, dict)

    # ⚡ Bolt: Verify caching behavior and deepcopy return
    schema2 = get_ontology_schema()
    assert schema == schema2
    assert schema is not schema2


def test_validate_payload() -> None:
    with pytest.raises(ValueError, match="Unknown step"):
        verify_manifold_bounds("Unknown", b"")

    # Try valid step with empty payload to trigger ValidationError
    with pytest.raises(ValidationError):
        verify_manifold_bounds("state_differential", b"{}")


def test_align_semantic_manifolds_dims() -> None:
    assert (
        align_semantic_manifolds(
            "task1", ["text", "raster_image", "vector_graphics", "audio_waveform", "unknown"], ["text"], "event1"
        )
        is None
    )








def test_compute_topology_hash() -> None:
    top = DAGTopologyManifest(topology_class="dag", nodes={}, edges=[], max_depth=1, max_fan_out=1)
    h = compute_topology_hash(top)
    assert len(h) == 64


def test_verify_merkle_proof() -> None:
    assert verify_merkle_proof([])

    n1 = Mock(node_hash=None, parent_hashes=[], request_cid="r1")
    assert not verify_merkle_proof([n1])

    n2 = Mock(node_hash="h1", parent_hashes=[], request_cid="r2")
    n2.generate_node_hash.return_value = "h1"
    assert verify_merkle_proof([n2])

    n3 = Mock(node_hash="h3", parent_hashes=[], request_cid="r3")
    n3.generate_node_hash.return_value = "invalid"
    with pytest.raises(Exception, match="Node hash mismatch"):
        verify_merkle_proof([n3])

    n4 = Mock(node_hash="h4", parent_hashes=["missing_parent"], request_cid="r4")
    n4.generate_node_hash.return_value = "h4"
    with pytest.raises(Exception, match="Missing parent hash"):
        verify_merkle_proof([n4])


def test_verify_ast_safety() -> None:
    assert verify_ast_safety("1 + 1")
    with pytest.raises(ValueError, match="Kinetic execution bleed"):
        verify_ast_safety("__import__('os')")
    with pytest.raises(ValueError, match="Forbidden AST node: Pow"):
        verify_ast_safety("2 ** 100")
    with pytest.raises(ValueError, match="not valid syntax"):
        verify_ast_safety("invalid syntax +")



def test_align_semantic_manifolds_transmutation() -> None:
    res1 = align_semantic_manifolds("t1", [], ["raster_image"], "e1")
    assert res1 is not None
    assert res1.compression_sla.required_grounding_density == "dense"

    res2 = align_semantic_manifolds("t1", [], ["text"], "e1")
    assert res2 is not None
    assert res2.compression_sla.required_grounding_density == "sparse"


def test_calculate_remaining_compute() -> None:
    ledger = Mock(history=[])
    assert calculate_remaining_compute(ledger, 10) == 10

    tbr1 = Mock(topology_class="token_burn", burn_magnitude=5)
    ledger.history.append(tbr1)
    assert calculate_remaining_compute(ledger, 10) == 5

    tbr2 = Mock(topology_class="token_burn", burn_magnitude=10)
    ledger.history.append(tbr2)
    with pytest.raises(ValueError, match="Mathematical Boundary Breached"):
        calculate_remaining_compute(ledger, 10)


def test_calculate_latent_alignment_errors() -> None:
    pol = OntologicalAlignmentPolicy(min_cosine_similarity=0.0, require_isometry_proof=False)

    v1 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 2.0)).decode(),
        dimensionality=2,
        foundation_matrix_name="m1",
    )
    v2 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<3f", 1.0, 2.0, 3.0)).decode(),
        dimensionality=3,
        foundation_matrix_name="m1",
    )
    with pytest.raises(ValueError, match="Topological Contradiction"):
        calculate_latent_alignment(v1, v2, pol)

    v3 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 2.0)).decode(),
        dimensionality=3,
        foundation_matrix_name="m1",
    )
    v4 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 2.0)).decode(),
        dimensionality=3,
        foundation_matrix_name="m1",
    )
    with pytest.raises(ValueError, match="Byte length does not match"):
        calculate_latent_alignment(v3, v4, pol)


def test_get_ontology_schema_empty() -> None:
    import coreason_manifest.utils.algebra as algebra

    # Temporarily clear the cache so the mock logic executes
    original_cache = algebra._CACHED_ONTOLOGY_SCHEMA
    algebra._CACHED_ONTOLOGY_SCHEMA = None

    try:
        # Temporarily clear models_to_export condition by mocking the return directly if empty
        with patch("coreason_manifest.utils.algebra.dir", return_value=[]):
            assert get_ontology_schema() == {}
    finally:
        # Restore the cache
        algebra._CACHED_ONTOLOGY_SCHEMA = original_cache


def test_calculate_latent_alignment_invalid_base64() -> None:
    pol = OntologicalAlignmentPolicy(min_cosine_similarity=-1.0, require_isometry_proof=False)
    # A string with valid chars but invalid length for base64: "a"
    v_invalid = VectorEmbeddingState.model_construct(
        vector_base64="a", dimensionality=3, foundation_matrix_name="model1"
    )
    v_valid = VectorEmbeddingState.model_construct(
        vector_base64=base64.b64encode(struct.pack("<3f", 1.0, 0.0, 0.0)).decode(),
        dimensionality=3,
        foundation_matrix_name="model1",
    )

    with pytest.raises(ValueError, match=r"Topological Contradiction: Invalid base64 encoding\."):
        calculate_latent_alignment(v_invalid, v_valid, pol)


def test_transmute_temporal_crdt_idempotence() -> None:
    state: dict[str, Any] = {"add_set": [], "terminate_set": []}
    cid_a = "did:coreason:agent1:" + "a" * 100
    cid_b = "did:coreason:agent1:" + "b" * 100
    manifest = TemporalGraphCRDTManifest(
        manifest_cid=cid_a,
        author_node_cid=cid_a,
        lamport_timestamp=1,
        vector_clock={cid_a: 1},
        add_set=[],
        terminate_set=[
            TemporalEdgeInvalidationIntent(
                target_edge_cid=cid_b,
                topology_class="temporal_invalidation",
                invalidation_timestamp=100.0,
                causal_justification_cid=cid_b
            )
        ]
    )
    state1 = transmute_temporal_crdt(state, manifest)
    state2 = transmute_temporal_crdt(state1, manifest)
    assert state1 == state2
    assert len(state1["terminate_set"]) == 1
    assert state1["terminate_set"][0] == cid_b

def test_transmute_temporal_crdt_commutativity() -> None:
    state: dict[str, Any] = {"add_set": [], "terminate_set": []}
    cid_a = "did:coreason:agent1:" + "a" * 100
    cid_b = "did:coreason:agent1:" + "b" * 100
    cid_c = "did:coreason:agent1:" + "c" * 100
    cid_d = "did:coreason:agent1:" + "d" * 100
    manifest_a = TemporalGraphCRDTManifest(
        manifest_cid=cid_a,
        author_node_cid=cid_a,
        lamport_timestamp=1,
        vector_clock={cid_a: 1},
        add_set=[],
        terminate_set=[
            TemporalEdgeInvalidationIntent(
                target_edge_cid=cid_c,
                topology_class="temporal_invalidation",
                invalidation_timestamp=100.0,
                causal_justification_cid=cid_c
            )
        ]
    )
    manifest_b = TemporalGraphCRDTManifest(
        manifest_cid=cid_b,
        author_node_cid=cid_b,
        lamport_timestamp=2,
        vector_clock={cid_b: 1},
        add_set=[],
        terminate_set=[
            TemporalEdgeInvalidationIntent(
                target_edge_cid=cid_d,
                topology_class="temporal_invalidation",
                invalidation_timestamp=200.0,
                causal_justification_cid=cid_d
            )
        ]
    )
    state_ab = transmute_temporal_crdt(transmute_temporal_crdt(state, manifest_a), manifest_b)
    state_ba = transmute_temporal_crdt(transmute_temporal_crdt(state, manifest_b), manifest_a)
    assert state_ab == state_ba
    assert len(state_ab["terminate_set"]) == 2
    assert set(state_ab["terminate_set"]) == {cid_c, cid_d}

def test_transmute_temporal_crdt_extraction() -> None:
    state: dict[str, Any] = {}
    cid_a = "did:coreason:agent1:" + "a" * 100
    cid_b = "did:coreason:agent1:" + "b" * 100
    manifest = TemporalGraphCRDTManifest(
        manifest_cid=cid_a,
        author_node_cid=cid_a,
        lamport_timestamp=1,
        vector_clock={cid_a: 1},
        add_set=[],
        terminate_set=[
            TemporalEdgeInvalidationIntent(
                target_edge_cid=cid_b,
                topology_class="temporal_invalidation",
                invalidation_timestamp=100.0,
                causal_justification_cid=cid_b
            )
        ]
    )
    res = transmute_temporal_crdt(state, manifest)
    assert len(res["terminate_set"]) == 1
    assert res["terminate_set"][0] == cid_b
