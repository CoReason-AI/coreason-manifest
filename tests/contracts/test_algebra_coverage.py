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
    calculate_latent_alignment,
    calculate_remaining_compute,
    compute_topology_hash,
    get_ontology_schema,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    synthesize_remediation_intent,
    transmute_state_differential,
    verify_ast_safety,
    verify_manifold_bounds,
    verify_merkle_proof,
)


@given(
    st.builds(
        DynamicRoutingManifest,
        manifest_cid=st.just("m1"),
        branch_budgets_magnitude=st.just({"did:node:b111111": 10}),
        active_subgraphs=st.just({}),
        bypassed_steps=st.lists(
            st.builds(
                BypassReceipt,
                bypassed_node_cid=st.just("did:node:bypass1"),
                cryptographic_null_hash=st.just("a" * 64),
                artifact_event_cid=st.just("event-1"),
            ),
            min_size=1,
        ),
        artifact_profile=st.builds(
            GlobalSemanticProfile,
            artifact_event_cid=st.just("event-1"),
            detected_modalities=st.just(["text"]),
            token_density=st.integers(min_value=0, max_value=100),
        ),
    )
)
def test_project_mermaid_bypassed(manifest: DynamicRoutingManifest) -> None:
    result = project_manifest_to_mermaid(manifest)
    assert "subgraph Quarantined_Bypass" in result
    for b in manifest.bypassed_steps:
        assert b.bypassed_node_cid.replace(":", "_").replace("-", "_").replace(".", "_") in result


@given(
    intent=st.text(min_size=1, max_size=50),
    justification=st.text(min_size=1, max_size=50),
    lineage=st.just("b" * 64),
    sig=st.just("sig" * 10),
    merkle=st.just("c" * 64),
)
def test_project_markdown_optional_fields(intent: str, justification: str, lineage: str, sig: str, merkle: str) -> None:
    node = Mock()
    node.topology_class = "system"
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
    manifest.tenant_cid = "t1"
    manifest.session_cid = "s1"
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
        prompt = synthesize_remediation_intent(e, "did:node:faulty1", "fault1")
        assert any("completely missing" in r.diagnostic_message for r in prompt.violation_receipts)

    # Trigger an invalid error
    try:
        WorkflowManifest(
            manifest_version="invalid",
            tenant_cid="t1",
            session_cid="s1",
            genesis_provenance={"author_identity": "did:node:n1"},  # type: ignore[arg-type]
            topology=DAGTopologyManifest(topology_class="dag", nodes={}, edges=[], max_depth=1, max_fan_out=1),
        )
    except ValidationError as e:
        prompt = synthesize_remediation_intent(e, "did:node:faulty1", "fault1")
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
@settings(max_examples=100)
def test_calculate_latent_alignment_success(v1: list[float]) -> None:
    b1 = struct.pack(f"<{len(v1)}f", *v1)
    b64 = base64.b64encode(b1).decode("ascii")

    vec1 = VectorEmbeddingState(foundation_matrix_name="m1", dimensionality=len(v1), vector_base64=b64)
    vec2 = VectorEmbeddingState(foundation_matrix_name="m1", dimensionality=len(v1), vector_base64=b64)
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
        diff_cid="d111111", author_node_cid="n111111", lamport_timestamp=1, vector_clock={"n111111": 1}, patches=ops
    )
    with contextlib.suppress(ValueError):
        transmute_state_differential(state, manifest)


def test_apply_state_differential_test_fail() -> None:
    state = {"foo": "baz"}
    manifest = StateDifferentialManifest(
        diff_cid="d111111",
        author_node_cid="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="test", path="/foo", value="bar")],
    )
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(state, manifest)


def test_apply_state_differential_copy() -> None:
    state = {"foo": {"bar": "baz"}}
    manifest = StateDifferentialManifest(
        diff_cid="d111111",
        author_node_cid="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(**{"op": "copy", "from": "/foo/bar", "path": "/foo/qux"})],  # type: ignore[arg-type]
    )
    res = transmute_state_differential(state, manifest)
    assert res["foo"]["qux"] == "baz"
    assert res["foo"]["bar"] == "baz"


def test_apply_state_differential_move() -> None:
    state = {"foo": {"bar": "baz"}}
    manifest = StateDifferentialManifest(
        diff_cid="d111111",
        author_node_cid="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(**{"op": "move", "from": "/foo/bar", "path": "/foo/qux"})],  # type: ignore[arg-type]
    )
    res = transmute_state_differential(state, manifest)
    assert res["foo"]["qux"] == "baz"
    assert "bar" not in res["foo"]


def test_apply_state_differential_replace_list() -> None:
    state = {"foo": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_cid="d111111",
        author_node_cid="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="replace", path="/foo/1", value=99)],
    )
    res = transmute_state_differential(state, manifest)
    assert res["foo"][1] == 99


def test_apply_state_differential_remove_list() -> None:
    state = {"foo": [1, 2, 3]}
    manifest = StateDifferentialManifest(
        diff_cid="d111111",
        author_node_cid="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="remove", path="/foo/1")],
    )
    res = transmute_state_differential(state, manifest)
    assert res["foo"] == [1, 3]


def test_apply_state_differential_add_list_dash() -> None:
    state = {"foo": [1, 2]}
    manifest = StateDifferentialManifest(
        diff_cid="d111111",
        author_node_cid="n111111",
        lamport_timestamp=1,
        vector_clock={"n111111": 1},
        patches=[StateMutationIntent(op="add", path="/foo/-", value=3)],
    )
    res = transmute_state_differential(state, manifest)
    assert res["foo"] == [1, 2, 3]


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


def test_apply_state_differential_test_pass() -> None:
    state = {"foo": "bar"}
    manifest = StateDifferentialManifest(
        diff_cid="d111",
        author_node_cid="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(op="test", path="/foo", value="bar")],
    )
    res = transmute_state_differential(state, manifest)
    assert res == state


def test_apply_state_differential_invalid_root() -> None:
    manifest = StateDifferentialManifest(
        diff_cid="d111",
        author_node_cid="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(op="add", path="invalid", value="bar")],
    )
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({}, manifest)


def test_apply_state_differential_invalid_from_path() -> None:
    manifest = StateDifferentialManifest(
        diff_cid="d111",
        author_node_cid="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(**{"op": "copy", "path": "/foo", "from": "invalid"})],  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"foo": 1}, manifest)


def test_apply_state_differential_out_of_bounds() -> None:
    manifest = StateDifferentialManifest(
        diff_cid="d111",
        author_node_cid="n111",
        lamport_timestamp=1,
        vector_clock={"n111": 1},
        patches=[StateMutationIntent(op="add", path="/foo/99", value="bar")],
    )
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"foo": []}, manifest)


def test_apply_state_differential_exceptions() -> None:
    def manifest_base(patches: list[Any]) -> StateDifferentialManifest:
        return StateDifferentialManifest(
            diff_cid="d1", author_node_cid="n1", lamport_timestamp=1, vector_clock={"n1": 1}, patches=patches
        )

    assert (
        cast("Any", transmute_state_differential({}, manifest_base([StateMutationIntent(op="add", path="", value=1)])))
        == 1
    )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": "b"}, manifest_base([StateMutationIntent(op="add", path="/a/b", value=1)]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/~foo", value=1)]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/foo/bar", value=1)])
        )

    p = StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/foo/bar"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": [], "b": 1}, manifest_base([p]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": {}}, manifest_base([StateMutationIntent(op="add", path="/a/b/c", value=1)]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/-"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/99"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/b", "from": "/a/foo"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": {}}, manifest_base([StateMutationIntent(op="remove", path="/a/foo")]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": []}, manifest_base([StateMutationIntent(op="remove", path="/a/-")]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": []}, manifest_base([StateMutationIntent(op="remove", path="/a/99")]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": []}, manifest_base([StateMutationIntent(op="remove", path="/a/foo")]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/99", value=1)]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(1, manifest_base([StateMutationIntent(op="add", path="/a", value=1)]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": {"b": 1}}, manifest_base([StateMutationIntent(op="add", path="/a/b/c/d", value=1)])
        )

    # Hit 369: valid list navigation
    transmute_state_differential(
        {"a": [{"b": 1}]}, manifest_base([StateMutationIntent(op="test", path="/a/0/b", value=1)])
    )

    # Hit 371: invalid list navigation
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []}, manifest_base([StateMutationIntent(op="add", path="/a/foo/b", value=1)])
        )

    # Hit 391: valid from_path list navigation
    p_valid = StateMutationIntent(**{"op": "copy", "path": "/c", "from": "/a/0/b"})  # type: ignore[arg-type]
    transmute_state_differential({"a": [{"b": 1}], "c": 0}, manifest_base([p_valid]))

    # Hit 386: from_path missing parent dict key
    p_invalid_key = StateMutationIntent(**{"op": "copy", "path": "/c", "from": "/a/foo/bar"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": {}}, manifest_base([p_invalid_key]))

    p_invalid = StateMutationIntent(**{"op": "copy", "path": "/c", "from": "/a/b/c/d"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": {"b": 1}}, manifest_base([p_invalid]))


def test_apply_state_differential_copy_ops() -> None:
    def manifest_base(patches: list[Any]) -> StateDifferentialManifest:
        return StateDifferentialManifest(
            diff_cid="d2", author_node_cid="n1", lamport_timestamp=1, vector_clock={"n1": 1}, patches=patches
        )

    # Test deep copy op inside object
    res = transmute_state_differential(
        {"a": {"b": 1}},
        manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/c", "from": "/a/b"})]),  # type: ignore[arg-type]
    )
    assert res["a"]["c"] == 1

    # Test move op inside list
    res = transmute_state_differential(
        {"a": [1, 2]},
        manifest_base([StateMutationIntent(**{"op": "move", "path": "/a/-", "from": "/a/0"})]),  # type: ignore[arg-type]
    )
    assert res["a"] == [2, 1]

    # Test replace op inside dict
    res = transmute_state_differential(
        {"a": {"b": 1}}, manifest_base([StateMutationIntent(op="replace", path="/a/b", value=2)])
    )
    assert res["a"]["b"] == 2

    # Test overlapping from_path for copy/move
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": {"b": 1}},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/b/c", "from": "/a/b"})]),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": 1}, manifest_base([StateMutationIntent(op="copy", path="/b")]))

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []}, manifest_base([StateMutationIntent(op="replace", path="/a/-", value=1)])
        )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": []}, manifest_base([StateMutationIntent(op="replace", path="/a/foo", value=1)])
        )

    # cover 494-511 copy/move array logic
    # copy append to list (-)
    transmute_state_differential(
        {"a": [1]},
        manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/-", "from": "/a/0"})]),  # type: ignore[arg-type]
    )

    # copy insert to list (0)
    transmute_state_differential(
        {"a": [1]},
        manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/0", "from": "/a/0"})]),  # type: ignore[arg-type]
    )

    # copy insert to list invalid index
    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential(
            {"a": [1]},
            manifest_base([StateMutationIntent(**{"op": "copy", "path": "/a/foo", "from": "/a/0"})]),  # type: ignore[arg-type]
        )

    # move insert to same list (from_idx < last_part)
    transmute_state_differential(
        {"a": [1, 2, 3]},
        manifest_base([StateMutationIntent(**{"op": "move", "path": "/a/2", "from": "/a/0"})]),  # type: ignore[arg-type]
    )

    # move insert to same list (from_idx >= last_part)
    transmute_state_differential(
        {"a": [1, 2, 3]},
        manifest_base([StateMutationIntent(**{"op": "move", "path": "/a/0", "from": "/a/2"})]),  # type: ignore[arg-type]
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


def test_apply_state_differential_test_op() -> None:
    def manifest_base(patches: list[Any]) -> StateDifferentialManifest:
        return StateDifferentialManifest(
            diff_cid="d1", author_node_cid="n1", lamport_timestamp=1, vector_clock={"n1": 1}, patches=patches
        )

    with pytest.raises(ValueError, match="Patch operation failed"):
        transmute_state_differential({"a": 1}, manifest_base([StateMutationIntent(op="test", path="", value={"a": 2})]))

    res = transmute_state_differential(
        {"a": 1}, manifest_base([StateMutationIntent(op="test", path="", value={"a": 1})])
    )
    assert res == {"a": 1}


def test_align_semantic_manifolds_transmutation() -> None:
    res1 = align_semantic_manifolds("t1", [], ["raster_image"], "e1")
    assert res1 is not None

    res2 = align_semantic_manifolds("t1", [], ["text"], "e1")
    assert res2 is not None


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


def test_epistemic_transmutation_schema_presence() -> None:
    import pytest
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import EpistemicTransmutationTask

    with pytest.raises(
        ValidationError,
        match=r"schema_governance is strictly required when target_modalities includes 'semantic_graph'.",
    ):
        EpistemicTransmutationTask(
            task_cid="t1", artifact_event_cid="a1", target_modalities=["semantic_graph"], schema_governance=None
        )


def test_transmutation_optical_sla_required() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import EpistemicTransmutationTask

    with pytest.raises(
        ValidationError,
        match=r"Epistemic Violation: Extracting 'raster_image' or 'tabular_grid' mathematically requires an OpticalParsingSLA.",
    ):
        EpistemicTransmutationTask(task_cid="t1", artifact_event_cid="a1", target_modalities=["raster_image"])


def test_edge_evidence_or_sla() -> None:

    import pytest
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import CausalDirectedEdgeState, SemanticEdgeState

    with pytest.raises(
        ValidationError,
        match=r"Causal edge must possess either empirical evidence \(belief_vector\) or an explicit grounding_sla.",
    ):
        CausalDirectedEdgeState(
            source_variable="A",
            target_variable="B",
            edge_class="direct_cause",
            predicate_curie="test:pred",
            belief_vector=None,
            grounding_sla=None,
        )

    with pytest.raises(
        ValidationError,
        match=r"Edge must possess either empirical evidence \(belief_vector\) or an explicit grounding_sla.",
    ):
        SemanticEdgeState(
            edge_cid="e1",
            subject_node_cid="n1",
            object_node_cid="n2",
            predicate_curie="test:pred",
            belief_vector=None,
            grounding_sla=None,
        )


def test_canonical_sorts() -> None:

    # DocumentKnowledgeGraphManifest
    from coreason_manifest.spec.ontology import (
        BeliefModulationReceipt,
        CausalDirectedEdgeState,
        CausalPropagationIntent,
        DerivationModeProfile,
        DocumentKnowledgeGraphManifest,
        EpistemicProvenanceReceipt,
        EvidentiaryGroundingSLA,
        SemanticNodeState,
    )

    prov = EpistemicProvenanceReceipt(
        extracted_by="did:coreason:abc:123",
        source_event_cid="e1",
        derivation_mode=DerivationModeProfile.DIRECT_TRANSLATION,
    )
    n1 = SemanticNodeState(node_cid="did:coreason:b", label="B", scope="session", text_chunk="B", provenance=prov)
    n2 = SemanticNodeState(node_cid="did:coreason:a", label="A", scope="session", text_chunk="A", provenance=prov)

    e1 = CausalDirectedEdgeState(
        source_variable="B",
        target_variable="C",
        edge_class="direct_cause",
        predicate_curie="t:p",
        grounding_sla=EvidentiaryGroundingSLA(minimum_nli_entailment_score=0.5),
    )
    e2 = CausalDirectedEdgeState(
        source_variable="A",
        target_variable="B",
        edge_class="direct_cause",
        predicate_curie="t:p",
        grounding_sla=EvidentiaryGroundingSLA(minimum_nli_entailment_score=0.5),
    )

    m = DocumentKnowledgeGraphManifest(
        graph_cid="g1", source_artifact_cid="a1", nodes=[n1, n2], causal_edges=[e1, e2], isomorphism_hash="a" * 64
    )
    assert m.nodes[0].node_cid == "did:coreason:a"
    assert m.causal_edges[0].source_variable == "A"

    # CausalPropagationIntent
    c = CausalPropagationIntent(
        target_graph_cid="g1",
        task_cid="t1",
        grounding_sla=EvidentiaryGroundingSLA(minimum_nli_entailment_score=0.5),
        unverified_edges=[e1, e2],
    )
    assert c.unverified_edges[0].source_variable == "A"

    # BeliefModulationReceipt
    b = BeliefModulationReceipt(
        receipt_cid="r1",
        event_cid="e1",
        timestamp=1.0,
        target_graph_cid="g1",
        grounded_edges={},
        severed_edge_cids=["z1", "a1"],
    )
    assert b.severed_edge_cids == ["a1", "z1"]


def test_tabular_matrix_profile_coverage() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import (
        DocumentLayoutRegionState,
        HierarchicalDOMManifest,
        MultimodalTokenAnchorState,
        TabularCellState,
        TabularMatrixProfile,
    )

    cell_ok = TabularCellState(cell_cid="c1", row_index=0, column_index=0, text_payload="hi")
    cell_bad = TabularCellState(cell_cid="c2", row_index=2, column_index=0, text_payload="hi")

    # Test valid matrix and sorting
    # bad is indexed 2, but total_rows=2, so it should fail physics
    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: Tabular cell geometry exceeds defined matrix dimensions."
    ):
        TabularMatrixProfile(matrix_cid="m1", total_rows=2, total_columns=2, cells=[cell_bad, cell_ok])

    m_ok = TabularMatrixProfile(matrix_cid="m1", total_rows=5, total_columns=5, cells=[cell_bad, cell_ok])
    assert m_ok.cells[0].cell_cid == "c1"

    anchor = MultimodalTokenAnchorState.model_construct()

    with pytest.raises(
        ValidationError,
        match=r"Topological Contradiction: tabular_matrix can only be populated if block_class is 'table'.",
    ):
        DocumentLayoutRegionState(block_cid="b1", block_class="paragraph", anchor=anchor, tabular_matrix=m_ok)

    r_ok = DocumentLayoutRegionState(block_cid="b1", block_class="table", anchor=anchor, tabular_matrix=m_ok)

    r_other = DocumentLayoutRegionState(block_cid="b2", block_class="paragraph", anchor=anchor)

    with pytest.raises(ValidationError, match=r"Topological Contradiction: root_block_cid not found in blocks."):
        HierarchicalDOMManifest(dom_cid="d1", root_block_cid="missing", blocks={"b1": r_ok})

    with pytest.raises(ValidationError, match=r"Ghost pointer: Containment edge references undefined block."):
        HierarchicalDOMManifest(
            dom_cid="d1", root_block_cid="b1", blocks={"b1": r_ok}, containment_edges=[("b1", "b2")]
        )

    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: Hierarchical DOM tree contains a spatial cycle."
    ):
        HierarchicalDOMManifest(
            dom_cid="d1",
            root_block_cid="b1",
            blocks={"b1": r_ok, "b2": r_other},
            containment_edges=[("b1", "b2"), ("b2", "b1")],
        )

    HierarchicalDOMManifest(
        dom_cid="d1", root_block_cid="b1", blocks={"b1": r_ok, "b2": r_other}, containment_edges=[("b1", "b2")]
    )
