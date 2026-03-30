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
from typing import Any
from unittest.mock import Mock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BypassReceipt,
    DAGTopologyManifest,
    DynamicRoutingManifest,
    GlobalSemanticProfile,
    OntologicalAlignmentPolicy,
    StateDifferentialManifest,
    StateMutationIntent,
    VectorEmbeddingState,
    WorkflowManifest,
)
from coreason_manifest.utils.algebra import (
    align_semantic_manifolds,
    apply_state_differential,
    calculate_latent_alignment,
    calculate_remaining_compute,
    compute_topology_hash,
    generate_correction_prompt,
    get_ontology_schema,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    validate_payload,
    verify_ast_safety,
    verify_merkle_proof,
)


@given(
    st.builds(
        DynamicRoutingManifest,
        manifest_id=st.just("m1"),
        branch_budgets_magnitude=st.just({"did:node:b111111": 10}),
        active_subgraphs=st.just({}),
        bypassed_steps=st.lists(
            st.builds(
                BypassReceipt,
                bypassed_node_id=st.just("did:node:bypass1"),
                cryptographic_null_hash=st.just("a" * 64),
                artifact_event_id=st.just("event-1"),
            ),
            min_size=1,
        ),
        artifact_profile=st.builds(
            GlobalSemanticProfile,
            artifact_event_id=st.just("event-1"),
            detected_modalities=st.just(["text"]),
            token_density=st.integers(min_value=0, max_value=100),
        ),
    )
)
def test_project_mermaid_bypassed(manifest: DynamicRoutingManifest) -> None:
    result = project_manifest_to_mermaid(manifest)
    assert "subgraph Quarantined_Bypass" in result
    for b in manifest.bypassed_steps:
        assert b.bypassed_node_id.replace(":", "_").replace("-", "_").replace(".", "_") in result


@given(
    intent=st.text(min_size=1, max_size=50),
    justification=st.text(min_size=1, max_size=50),
    lineage=st.just("b" * 64),
    sig=st.just("sig" * 10),
    merkle=st.just("c" * 64),
)
def test_project_markdown_optional_fields(intent: str, justification: str, lineage: str, sig: str, merkle: str) -> None:
    node = Mock()
    node.type = "system"
    node.description = "desc"
    node.architectural_intent = intent
    node.justification = justification
    node.agent_attestation = Mock(training_lineage_hash=lineage, developer_signature=sig, capability_merkle_root=merkle)

    topology = Mock()
    topology.nodes = {"n1": node}
    topology.architectural_intent = intent
    topology.justification = justification

    manifest = Mock()
    manifest.manifest_version = "1.0.0"
    manifest.tenant_id = "t1"
    manifest.session_id = "s1"
    manifest.topology = topology

    result = project_manifest_to_markdown(manifest)
    assert intent in result
    assert justification in result
    assert lineage in result


def test_generate_correction_prompt_missing_and_invalid() -> None:
    # Trigger a missing error
    try:
        WorkflowManifest(manifest_version="1.0.0")  # type: ignore[call-arg]
    except ValidationError as e:
        prompt = generate_correction_prompt(e, "did:node:faulty1", "fault1")
        assert any("completely missing" in r.diagnostic_message for r in prompt.violation_receipts)

    # Trigger an invalid error
    try:
        WorkflowManifest(
            manifest_version="invalid",
            tenant_id="t1",
            session_id="s1",
            genesis_provenance={"author_identity": "did:node:n1"},  # type: ignore[arg-type]
            topology=DAGTopologyManifest(type="dag", nodes={}, edges=[], max_depth=1, max_fan_out=1),
        )
    except ValidationError as e:
        prompt = generate_correction_prompt(e, "did:node:faulty1", "fault1")
        assert any("String should match pattern" in r.diagnostic_message for r in prompt.violation_receipts)


@given(source=st.lists(st.sampled_from(["text", "raster_image", "vector_graphics"]), min_size=2, unique=True))
def test_align_semantic_manifolds_subset(source: list[str]) -> None:
    # Pass subset to target
    target = source[:1]
    res = align_semantic_manifolds("task1", source, target, "event1")  # type: ignore[arg-type]
    assert res is None


@given(
    v1=st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=10
    )
)
def test_calculate_latent_alignment_success(v1: list[float]) -> None:
    b1 = struct.pack(f"<{len(v1)}f", *v1)
    b64 = base64.b64encode(b1).decode("ascii")

    vec1 = VectorEmbeddingState(model_name="m1", dimensionality=len(v1), vector_base64=b64)
    vec2 = VectorEmbeddingState(model_name="m1", dimensionality=len(v1), vector_base64=b64)
    policy = OntologicalAlignmentPolicy(min_cosine_similarity=0.9, require_isometry_proof=False)

    if any(x != 0.0 for x in v1):  # Avoid zero vectors
        try:
            res = calculate_latent_alignment(vec1, vec2, policy)
        except ValueError as e:
            if "Latent alignment failed" not in str(e):
                raise
        else:
            assert res >= 0.9


@given(
    ops=st.lists(
        st.builds(StateMutationIntent, op=st.sampled_from(["test", "add"]), path=st.just("/foo"), value=st.just("bar"))
    )
)
def test_apply_state_differential_hyp_add(ops: list[StateMutationIntent]) -> None:
    state: dict[str, Any] = {}
    manifest = StateDifferentialManifest(
        diff_id="d111111", author_node_id="n111111", lamport_timestamp=1, vector_clock={"n111111": 1}, patches=ops
    )
    with contextlib.suppress(ValueError):
        apply_state_differential(state, manifest)


def test_apply_state_differential_test_fail() -> None:
    state = {"foo": "baz"}
    manifest = StateDifferentialManifest(
        diff_id="d111111",
        author_node_id="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="test", path="/foo", value="bar")],
    )
    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential(state, manifest)


def test_apply_state_differential_copy() -> None:
    state = {"foo": {"bar": "baz"}}
    manifest = StateDifferentialManifest(
        diff_id="d111111",
        author_node_id="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(**{"op": "copy", "from": "/foo/bar", "path": "/foo/qux"})],  # type: ignore[arg-type]
    )
    res = apply_state_differential(state, manifest)
    assert res["foo"]["qux"] == "baz"
    assert res["foo"]["bar"] == "baz"


def test_apply_state_differential_move() -> None:
    state = {"foo": {"bar": "baz"}}
    manifest = StateDifferentialManifest(
        diff_id="d111111",
        author_node_id="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(**{"op": "move", "from": "/foo/bar", "path": "/foo/qux"})],  # type: ignore[arg-type]
    )
    res = apply_state_differential(state, manifest)
    assert res["foo"]["qux"] == "baz"
    assert "bar" not in res["foo"]


def test_apply_state_differential_replace_list() -> None:
    state = {"foo": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="d111111",
        author_node_id="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="replace", path="/foo/1", value=99)],
    )
    res = apply_state_differential(state, manifest)
    assert res["foo"][1] == 99


def test_apply_state_differential_remove_list() -> None:
    state = {"foo": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_id="d111111",
        author_node_id="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="remove", path="/foo/1")],
    )
    res = apply_state_differential(state, manifest)
    assert res["foo"] == [1, 3]


def test_apply_state_differential_add_list_dash() -> None:
    state = {"foo": [1, 2]}
    manifest = StateDifferentialManifest(
        diff_id="d111111",
        author_node_id="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="add", path="/foo/-", value=3)],
    )
    res = apply_state_differential(state, manifest)
    assert res["foo"] == [1, 2, 3]


def test_project_mermaid_active_subgraph() -> None:
    manifest = Mock()
    manifest.manifest_id = "m1"
    manifest.artifact_profile.detected_modalities = ["text"]
    manifest.active_subgraphs = {"text": ["did:node:1"]}
    manifest.bypassed_steps = []
    res = project_manifest_to_mermaid(manifest)
    assert "did_node_1" in res


def test_get_ontology_schema() -> None:
    schema = get_ontology_schema()
    assert isinstance(schema, dict)


def test_validate_payload() -> None:
    with pytest.raises(ValueError, match="Unknown step"):
        validate_payload("Unknown", b"")

    # Try valid step with empty payload to trigger ValidationError
    with pytest.raises(ValidationError):
        validate_payload("state_differential", b"{}")


def test_align_semantic_manifolds_dims() -> None:
    assert (
        align_semantic_manifolds(
            "task1", ["text", "raster_image", "vector_graphics", "audio_waveform", "unknown"], ["text"], "event1"
        )
        is None
    )


def test_apply_state_differential_test_pass() -> None:
    state = {"foo": "bar"}
    manifest = StateDifferentialManifest(
        diff_id="d111",
        author_node_id="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(op="test", path="/foo", value="bar")],
    )
    res = apply_state_differential(state, manifest)
    assert res == state


def test_apply_state_differential_invalid_root() -> None:
    manifest = StateDifferentialManifest(
        diff_id="d111",
        author_node_id="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(op="add", path="invalid", value="bar")],
    )
    with pytest.raises(ValueError, match="Invalid JSON pointer"):
        apply_state_differential({}, manifest)


def test_apply_state_differential_invalid_from_path() -> None:
    manifest = StateDifferentialManifest(
        diff_id="d111",
        author_node_id="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(**{"op": "copy", "path": "/foo", "from": "invalid"})],  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="Invalid from_path"):
        apply_state_differential({"foo": 1}, manifest)


def test_apply_state_differential_out_of_bounds() -> None:
    manifest = StateDifferentialManifest(
        diff_id="d111",
        author_node_id="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(op="add", path="/foo/99", value="bar")],
    )
    with pytest.raises(ValueError, match="Invalid index"):
        apply_state_differential({"foo": []}, manifest)


def test_apply_state_differential_exceptions() -> None:
    def manifest_base(patches: list[Any]) -> StateDifferentialManifest:
        return StateDifferentialManifest(
            diff_id="d1", author_node_id="n1", lamport_timestamp=1, vector_clock={"n1": 1}, patches=patches
        )

    with pytest.raises(ValueError, match="root operation not supported"):
        apply_state_differential({}, manifest_base([StateMutationIntent(op="add", path="", value=1)]))

    with pytest.raises(ValueError, match="Cannot add to path"):
        apply_state_differential({"a": "b"}, manifest_base([StateMutationIntent(op="add", path="/a/b", value=1)]))

    with pytest.raises(ValueError, match="Invalid JSON pointer"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/~foo", value=1)]))

    with pytest.raises(ValueError, match="Invalid path"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/foo/bar", value=1)]))

    p = StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/foo/bar"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Invalid from_path"):
        apply_state_differential({"a": [], "b": 1}, manifest_base([p]))

    with pytest.raises(ValueError, match="Invalid path"):
        apply_state_differential({"a": {}}, manifest_base([StateMutationIntent(op="add", path="/a/b/c", value=1)]))

    with pytest.raises(ValueError, match="Cannot extract"):
        apply_state_differential(
            {"a": []},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/-"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Invalid from_path operation: Invalid index"):
        apply_state_differential(
            {"a": []},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/99"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Invalid from_path operation: Invalid index"):
        apply_state_differential(
            {"a": []},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/foo"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Cannot remove from path"):
        apply_state_differential({"a": {}}, manifest_base([StateMutationIntent(op="remove", path="/a/foo")]))

    with pytest.raises(ValueError, match="Cannot remove from end"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="remove", path="/a/-")]))

    with pytest.raises(ValueError, match="Invalid index"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="remove", path="/a/99")]))

    with pytest.raises(ValueError, match="Invalid index"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="remove", path="/a/foo")]))

    with pytest.raises(ValueError, match="Invalid index"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/99", value=1)]))

    with pytest.raises(ValueError, match="Cannot add to path"):
        apply_state_differential(1, manifest_base([StateMutationIntent(op="add", path="/a", value=1)]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Invalid path"):
        apply_state_differential(
            {"a": {"b": 1}}, manifest_base([StateMutationIntent(op="add", path="/a/b/c/d", value=1)])
        )

    # Hit 369: valid list navigation
    apply_state_differential({"a": [{"b": 1}]}, manifest_base([StateMutationIntent(op="test", path="/a/0/b", value=1)]))

    # Hit 371: invalid list navigation
    with pytest.raises(ValueError, match="Invalid path"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/foo/b", value=1)]))

    # Hit 391: valid from_path list navigation
    p_valid = StateMutationIntent(**{"op": "copy", "path": "/c", "from": "/a/0/b"})  # type: ignore[arg-type]
    apply_state_differential({"a": [{"b": 1}], "c": 0}, manifest_base([p_valid]))

    # Hit 386: from_path missing parent dict key
    p_invalid_key = StateMutationIntent(**{"op": "copy", "path": "/c", "from": "/a/foo/bar"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Invalid from_path operation: Invalid from_path"):
        apply_state_differential({"a": {}}, manifest_base([p_invalid_key]))

    p_invalid = StateMutationIntent(**{"op": "copy", "path": "/c", "from": "/a/b/c/d"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Invalid from_path operation"):
        apply_state_differential({"a": {"b": 1}}, manifest_base([p_invalid]))


def test_apply_state_differential_copy_ops() -> None:
    def manifest_base(patches: list[Any]) -> StateDifferentialManifest:
        return StateDifferentialManifest(
            diff_id="d2", author_node_id="n1", lamport_timestamp=1, vector_clock={"n1": 1}, patches=patches
        )

    # Test deep copy op inside object
    res = apply_state_differential(
        {"a": {"b": 1}},
        manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/c", "from": "/a/b"})]),  # type: ignore[arg-type]
    )
    assert res["a"]["c"] == 1

    # Test move op inside list
    res = apply_state_differential(
        {"a": [1, 2]},
        manifest_base([StateMutationIntent(**{"op": "move", "path": "/a/-", "from": "/a/0"})]),  # type: ignore[arg-type]
    )
    assert res["a"] == [2, 1]

    # Test replace op inside dict
    res = apply_state_differential(
        {"a": {"b": 1}}, manifest_base([StateMutationIntent(op="replace", path="/a/b", value=2)])
    )
    assert res["a"]["b"] == 2

    # Test overlapping from_path for copy/move
    with pytest.raises(ValueError, match="proper prefix"):
        apply_state_differential(
            {"a": {"b": 1}},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/b/c", "from": "/a/b"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="from_path is mathematically required"):
        apply_state_differential({"a": 1}, manifest_base([StateMutationIntent(op="copy", path="/b")]))

    with pytest.raises(ValueError, match="Cannot replace at path /a/-: Cannot extract from end of array"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="replace", path="/a/-", value=1)]))

    with pytest.raises(ValueError, match="Cannot replace at path"):
        apply_state_differential({"a": []}, manifest_base([StateMutationIntent(op="replace", path="/a/foo", value=1)]))

    # cover 494-511 copy/move array logic
    # copy append to list (-)
    apply_state_differential(
        {"a": [1]},
        manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/-", "from": "/a/0"})]),  # type: ignore[arg-type]
    )

    # copy insert to list (0)
    apply_state_differential(
        {"a": [1]},
        manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/0", "from": "/a/0"})]),  # type: ignore[arg-type]
    )

    # copy insert to list invalid index
    with pytest.raises(ValueError, match="Invalid index"):
        apply_state_differential(
            {"a": [1]},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/foo", "from": "/a/0"})]),  # type: ignore[arg-type]
        )

    # move insert to same list (from_idx < last_part)
    apply_state_differential(
        {"a": [1, 2, 3]},
        manifest_base([StateMutationIntent(**{"op": "move", "path": "/a/2", "from": "/a/0"})]),  # type: ignore[arg-type]
    )

    # move insert to same list (from_idx >= last_part)
    apply_state_differential(
        {"a": [1, 2, 3]},
        manifest_base([StateMutationIntent(**{"op": "move", "path": "/a/0", "from": "/a/2"})]),  # type: ignore[arg-type]
    )


def test_compute_topology_hash() -> None:
    top = DAGTopologyManifest(type="dag", nodes={}, edges=[], max_depth=1, max_fan_out=1)
    h = compute_topology_hash(top)
    assert len(h) == 64


def test_verify_merkle_proof() -> None:
    assert verify_merkle_proof([])

    n1 = Mock(node_hash=None, parent_hashes=[], request_id="r1")
    assert not verify_merkle_proof([n1])

    n2 = Mock(node_hash="h1", parent_hashes=[], request_id="r2")
    n2.generate_node_hash.return_value = "h1"
    assert verify_merkle_proof([n2])

    n3 = Mock(node_hash="h3", parent_hashes=[], request_id="r3")
    n3.generate_node_hash.return_value = "invalid"
    with pytest.raises(Exception, match="Node hash mismatch"):
        verify_merkle_proof([n3])

    n4 = Mock(node_hash="h4", parent_hashes=["missing_parent"], request_id="r4")
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


def test_apply_state_differential_test_op() -> None:
    def manifest_base(patches: list[Any]) -> StateDifferentialManifest:
        return StateDifferentialManifest(
            diff_id="d1", author_node_id="n1", lamport_timestamp=1, vector_clock={"n1": 1}, patches=patches
        )

    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential({"a": 1}, manifest_base([StateMutationIntent(op="test", path="", value={"a": 2})]))

    res = apply_state_differential({"a": 1}, manifest_base([StateMutationIntent(op="test", path="", value={"a": 1})]))
    assert res == {"a": 1}


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

    tbr1 = Mock(type="token_burn", burn_magnitude=5)
    ledger.history.append(tbr1)
    assert calculate_remaining_compute(ledger, 10) == 5

    tbr2 = Mock(type="token_burn", burn_magnitude=10)
    ledger.history.append(tbr2)
    with pytest.raises(ValueError, match="Mathematical Boundary Breached"):
        calculate_remaining_compute(ledger, 10)


def test_calculate_latent_alignment_errors() -> None:
    pol = OntologicalAlignmentPolicy(min_cosine_similarity=0.0, require_isometry_proof=False)

    v1 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 2.0)).decode(), dimensionality=2, model_name="m1"
    )
    v2 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<3f", 1.0, 2.0, 3.0)).decode(), dimensionality=3, model_name="m1"
    )
    with pytest.raises(ValueError, match="Topological Contradiction"):
        calculate_latent_alignment(v1, v2, pol)

    v3 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 2.0)).decode(), dimensionality=3, model_name="m1"
    )
    v4 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 2.0)).decode(), dimensionality=3, model_name="m1"
    )
    with pytest.raises(ValueError, match="Byte length does not match"):
        calculate_latent_alignment(v3, v4, pol)


@patch("coreason_manifest.utils.algebra.models_json_schema")
def test_get_ontology_schema_empty(mock_schema: Mock) -> None:
    from coreason_manifest.utils.algebra import _get_ontology_schema_cached

    _get_ontology_schema_cached.cache_clear()
    try:
        mock_schema.return_value = (None, {})
        assert get_ontology_schema() == {}
    finally:
        _get_ontology_schema_cached.cache_clear()


def test_calculate_latent_alignment_invalid_base64() -> None:
    pol = OntologicalAlignmentPolicy(min_cosine_similarity=-1.0, require_isometry_proof=False)
    # A string with valid chars but invalid length for base64: "a"
    v_invalid = VectorEmbeddingState.model_construct(vector_base64="a", dimensionality=3, model_name="model1")
    v_valid = VectorEmbeddingState.model_construct(
        vector_base64=base64.b64encode(struct.pack("<3f", 1.0, 0.0, 0.0)).decode(),
        dimensionality=3,
        model_name="model1",
    )

    with pytest.raises(ValueError, match=r"Topological Contradiction: Invalid base64 encoding\."):
        calculate_latent_alignment(v_invalid, v_valid, pol)
