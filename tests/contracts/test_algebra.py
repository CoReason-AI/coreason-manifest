# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import base64
import struct
from copy import deepcopy
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coreason_manifest.spec.ontology import (
    DAGTopologyManifest,
    DynamicRoutingManifest,
    EpistemicLedgerState,
    ExecutionNodeReceipt,
    OntologicalAlignmentPolicy,
    StateDifferentialManifest,
    StateMutationIntent,
    TamperFaultEvent,
    TokenBurnReceipt,
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


def test_align_semantic_manifolds_dense() -> None:
    res = align_semantic_manifolds("task1", ["text"], ["text", "raster_image"], "ev1")
    assert res is not None
    assert res.compression_sla.required_grounding_density == "dense"


def test_compute_topology_hash() -> None:
    topology = DAGTopologyManifest(
        nodes={}, edges=[], max_depth=10, max_fan_out=10, allow_cycles=False, architectural_intent="test"
    )
    hash_val = compute_topology_hash(topology)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64


class MockStrictProfile(BaseModel):
    name: str = Field(min_length=5)
    age: int


def test_generate_correction_prompt_translation() -> None:
    try:
        MockStrictProfile(name="Bob", age="not_an_int")
    except ValidationError as e:
        prompt = generate_correction_prompt(error=e, target_node_id="did:web:node-1", fault_id="fault-001")
        assert prompt.fault_id == "fault-001"
        assert prompt.target_node_id == "did:web:node-1"
        assert "/name" in prompt.failing_pointers
        assert "/age" in prompt.failing_pointers
        assert "CRITICAL CONTRACT BREACH" in prompt.remediation_prompt


def test_get_ontology_schema() -> None:
    schema = get_ontology_schema()
    assert isinstance(schema, dict)
    assert "$defs" in schema
    assert "WorkflowManifest" in schema["$defs"]


def test_validate_payload_success() -> None:
    payload = b'{"op": "add", "path": "/foo", "value": "bar"}'
    model = validate_payload("state_differential", payload)
    assert model.op == "add"  # type: ignore[attr-defined]
    assert model.path == "/foo"  # type: ignore[attr-defined]
    assert model.value == "bar"  # type: ignore[attr-defined]


def test_validate_payload_invalid_step() -> None:
    payload = b'{"op": "add", "path": "/foo", "value": "bar"}'
    with pytest.raises(ValueError, match="FATAL: Unknown step"):
        validate_payload("nonexistent_step", payload)


def test_validate_payload_invalid_json() -> None:
    payload = b'{"op": "add", "path": "/foo", "value": "bar"'  # missing closing brace
    with pytest.raises(ValidationError):
        validate_payload("state_differential", payload)


def test_project_manifest_to_mermaid() -> None:
    manifest_data = {
        "manifest_id": "manifest-test-01",
        "artifact_profile": {
            "artifact_event_id": "root-artifact",
            "detected_modalities": ["text"],
            "token_density": 100,
        },
        "active_subgraphs": {"text": ["did:web:agent-1"]},
        "bypassed_steps": [],
        "branch_budgets_magnitude": {"did:web:agent-1": 1000},
    }
    manifest = TypeAdapter(DynamicRoutingManifest).validate_python(manifest_data)
    mermaid_string = project_manifest_to_mermaid(manifest)

    assert "graph TD" in mermaid_string
    assert "did:web:agent-1" in mermaid_string
    assert "manifest-test-01" in mermaid_string


def test_project_manifest_to_markdown() -> None:
    envelope_data = {
        "manifest_version": "1.0.0",
        "genesis_provenance": {
            "extracted_by": "did:web:agent-1",
            "source_event_id": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        },
        "governance": {
            "mandatory_license_rule": {
                "rule_id": "PPL_3_0_COMPLIANCE",
                "severity": "critical",
                "description": "Ensure Prosperity Public License 3.0 Compliance.",
                "forbidden_intents": [],
            },
            "max_budget_magnitude": 1000,
            "max_global_tokens": 100000,
            "global_timeout_seconds": 3600,
        },
        "topology": {
            "type": "dag",
            "max_depth": 10,
            "max_fan_out": 10,
            "lifecycle_phase": "live",
            "nodes": {"did:web:agent-1": {"type": "system", "description": "Extractor"}},
            "edges": [],
            "allow_cycles": False,
        },
    }
    manifest = TypeAdapter(WorkflowManifest).validate_python(envelope_data)
    markdown_string = project_manifest_to_markdown(manifest)

    assert "# CoReason Agent Card" in markdown_string
    assert "did:web:agent-1" in markdown_string


def test_calculate_latent_alignment_mismatch_rejection() -> None:
    v1 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 0.0)).decode("utf-8"),
        dimensionality=2,
        model_name="model-a",
    )
    v2 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 0.0, 1.0)).decode("utf-8"),
        dimensionality=2,
        model_name="model-b",
    )
    v3 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<3f", 1.0, 0.0, 0.0)).decode("utf-8"),
        dimensionality=3,
        model_name="model-a",
    )

    policy = OntologicalAlignmentPolicy(min_cosine_similarity=0.0, require_isometry_proof=False)

    with pytest.raises(ValueError, match=r"Topological Contradiction: Vector geometries are incommensurable\."):
        calculate_latent_alignment(v1, v2, policy)

    with pytest.raises(ValueError, match=r"Topological Contradiction: Vector geometries are incommensurable\."):
        calculate_latent_alignment(v1, v3, policy)


@given(
    initial=st.integers(min_value=0, max_value=100000),
    burns=st.lists(st.integers(min_value=0, max_value=1000), max_size=50),
)
@settings(max_examples=100)
def test_calculate_remaining_compute_fuzzing(initial: int, burns: list[int]) -> None:
    """Mathematically prove the compute escrow exhaustion boundary."""
    receipts: list[Any] = [
        TokenBurnReceipt(
            event_id=f"burn-{i}",
            timestamp=float(i),
            tool_invocation_id=f"tool-{i}",
            input_tokens=1,
            output_tokens=1,
            burn_magnitude=b,
        )
        for i, b in enumerate(burns)
    ]
    ledger = EpistemicLedgerState(history=receipts)
    total_burn = sum(burns)

    if total_burn > initial:
        with pytest.raises(ValueError, match="Mathematical Boundary Breached"):
            calculate_remaining_compute(ledger, initial_escrow_magnitude=initial)
    else:
        assert calculate_remaining_compute(ledger, initial_escrow_magnitude=initial) == initial - total_burn


def test_calculate_latent_alignment_cosine_math() -> None:
    v1 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 1.0, 0.0)).decode("utf-8"),
        dimensionality=2,
        model_name="model-a",
    )
    v2 = VectorEmbeddingState(
        vector_base64=base64.b64encode(struct.pack("<2f", 0.0, 1.0)).decode("utf-8"),
        dimensionality=2,
        model_name="model-a",
    )

    policy = OntologicalAlignmentPolicy(min_cosine_similarity=0.0, require_isometry_proof=False)

    res = calculate_latent_alignment(v1, v2, policy)
    assert res == 0.0

    policy_strict = OntologicalAlignmentPolicy(min_cosine_similarity=0.9, require_isometry_proof=False)
    with pytest.raises(ValueError, match=r"TamperFaultEvent: Latent alignment failed\."):
        calculate_latent_alignment(v1, v2, policy_strict)


@pytest.mark.parametrize("payload", ["{'x': 1, 'y': 2 + 2}", "1 + 2 * 3", "a[0]"])
def test_verify_ast_safety_valid(payload: str) -> None:
    assert verify_ast_safety(payload) is True


@pytest.mark.parametrize(
    "payload",
    ["import os; os.system('ls')", "__import__('os').system('ls')", "exec('print(1)')", "__builtins__['eval']('1')"],
)
def test_verify_ast_safety_kinetic_bleed(payload: str) -> None:
    with pytest.raises((SyntaxError, ValueError)):
        verify_ast_safety(payload)


def test_apply_state_differential() -> None:
    base_state = {"user": {"name": "Alice", "tags": ["admin"]}}

    patch1 = StateMutationIntent(op="add", path="/user/age", value=30)
    patch2 = StateMutationIntent(op="replace", path="/user/name", value="Bob")
    patch3 = StateMutationIntent(op="remove", path="/user/tags/0")

    manifest = StateDifferentialManifest(
        diff_id="did:web:patch-1",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[patch1, patch2, patch3],
    )

    new_state = apply_state_differential(base_state, manifest)

    assert new_state == {"user": {"name": "Bob", "age": 30, "tags": []}}
    assert base_state == {"user": {"name": "Alice", "tags": ["admin"]}}


# Strategy to generate valid JSON primitives
json_primitive = st.recursive(
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.integers()
    | st.text(max_size=100),
    lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=50), children, max_size=5),
    max_leaves=10,
)


@st.composite
def random_mutations(draw: Any) -> StateDifferentialManifest:
    ops = draw(st.lists(st.sampled_from(["add", "remove", "replace", "copy", "move", "test"]), min_size=1, max_size=10))

    patches = []
    for op in ops:
        path = "/" + "/".join(draw(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)))
        kwargs = {"op": op, "path": path}
        if op in ("add", "replace", "test"):
            kwargs["value"] = draw(json_primitive)
        elif op in ("copy", "move"):
            kwargs["from"] = "/" + "/".join(draw(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)))

        import contextlib

        with contextlib.suppress(ValidationError):
            patches.append(StateMutationIntent(**kwargs))

    return StateDifferentialManifest(
        diff_id="random_diff",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=patches,
    )


@given(json_primitive, random_mutations())
def test_apply_state_differential_property(
    initial_state: dict[str, Any] | list[Any] | str | int | float | bool | None, manifest: StateDifferentialManifest
) -> None:
    """Property test to ensure apply_state_differential never crashes unexpectedly."""
    original_state = deepcopy(initial_state)

    try:
        _ = apply_state_differential(initial_state, manifest)  # type: ignore

        # If it succeeds, initial state should remain unchanged
        assert initial_state == original_state

    except ValueError:
        # ValueErrors (e.g., path not found, invalid operation) are expected for random invalid patches
        pass


def test_verify_merkle_proof_valid() -> None:
    receipt1 = ExecutionNodeReceipt(
        request_id="req1", inputs={"in": 1}, outputs={"out": 1}, parent_hashes=[], node_hash="dummy1"
    )
    # Use object.__setattr__ to bypass frozen=True
    object.__setattr__(receipt1, "node_hash", receipt1.generate_node_hash())

    receipt2 = ExecutionNodeReceipt(
        request_id="req2",
        inputs={"in": 2},
        outputs={"out": 2},
        parent_hashes=[receipt1.node_hash],  # type: ignore[list-item]
        node_hash="dummy2",
    )
    object.__setattr__(receipt2, "node_hash", receipt2.generate_node_hash())

    trace = [receipt2, receipt1]  # out of order but valid
    assert verify_merkle_proof(trace) is True


def test_verify_merkle_proof_invalid_hash() -> None:
    receipt1 = ExecutionNodeReceipt(
        request_id="req1", inputs={"in": 1}, outputs={"out": 1}, parent_hashes=[], node_hash="dummy1"
    )
    object.__setattr__(receipt1, "node_hash", "invalid_hash")
    with pytest.raises(TamperFaultEvent, match="Node hash mismatch"):
        verify_merkle_proof([receipt1])


def test_verify_merkle_proof_missing_parent() -> None:
    receipt1 = ExecutionNodeReceipt(
        request_id="req1",
        inputs={"in": 1},
        outputs={"out": 1},
        parent_hashes=["non_existent_parent"],
        node_hash="dummy1",
    )
    object.__setattr__(receipt1, "node_hash", receipt1.generate_node_hash())
    with pytest.raises(TamperFaultEvent, match="Missing parent hash"):
        verify_merkle_proof([receipt1])


def test_verify_merkle_proof_none_hash() -> None:
    receipt1 = ExecutionNodeReceipt(
        request_id="req1", inputs={"in": 1}, outputs={"out": 1}, parent_hashes=[], node_hash="valid"
    )
    object.__setattr__(receipt1, "node_hash", None)
    assert verify_merkle_proof([receipt1]) is False


# --- Atomic Edge Cases for State Differential (RFC 6902) ---


@pytest.mark.parametrize(
    ("patch_kwargs", "match_str"),
    [
        ({"op": "add", "path": "/arr/10", "value": 4}, "Invalid index: 10"),
        ({"op": "add", "path": "/arr/0/key", "value": 4}, "Cannot add to path"),
        ({"op": "remove", "path": "/arr/-"}, "Cannot remove from end of array"),
        (
            {"op": "replace", "path": "/arr/-", "value": 9},
            "Cannot replace at path /arr/-: Cannot extract from end of array",
        ),
        ({"op": "add", "path": "invalid", "value": 1}, "Invalid JSON pointer: invalid"),
        ({"op": "add", "path": "", "value": 1}, "Invalid path or root operation not supported"),
        ({"op": "add", "path": "/arr~20", "value": 1}, "Invalid JSON pointer: /arr~20"),
        ({"op": "test", "path": "", "value": {"different": "value"}}, "Patch test operation failed"),
        ({"op": "test", "path": "/arr/0", "value": 99}, "Patch test operation failed"),
        ({"op": "copy", "path": "/nested/new_key", "from": "/arr/10"}, "Invalid from_path operation"),
        ({"op": "copy", "path": "/nested/new_key", "from": "/nested/key/invalid"}, "Invalid from_path"),
    ],
)
def test_apply_state_differential_atomic_failures(patch_kwargs: dict[str, Any], match_str: str) -> None:
    """Mathematically prove invalid RFC 6902 patch geometries strictly trip the topological bounds."""
    base_state = {"arr": [1, 2, 3], "nested": {"key": "value"}}
    patch = StateMutationIntent(**patch_kwargs)
    manifest = StateDifferentialManifest(
        diff_id="did:web:patch-fail",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[patch],
    )
    with pytest.raises(ValueError, match=match_str):
        apply_state_differential(base_state, manifest)


@pytest.mark.parametrize(
    ("patch_kwargs", "expected_state"),
    [
        ({"op": "add", "path": "/arr/-", "value": 4}, {"arr": [1, 2, 3, 4], "nested": {"key": "value"}}),
        (
            {"op": "copy", "path": "/arr/1", "from": "/nested/key"},
            {"arr": [1, "value", 2, 3], "nested": {"key": "value"}},
        ),
        ({"op": "move", "path": "/arr/1", "from": "/nested/key"}, {"arr": [1, "value", 2, 3], "nested": {}}),
        (
            {"op": "test", "path": "", "value": {"arr": [1, 2, 3], "nested": {"key": "value"}}},
            {"arr": [1, 2, 3], "nested": {"key": "value"}},
        ),
        ({"op": "move", "path": "/arr/-", "from": "/arr/0"}, {"arr": [2, 3, 1], "nested": {"key": "value"}}),
    ],
)
def test_apply_state_differential_atomic_success(patch_kwargs: dict[str, Any], expected_state: dict[str, Any]) -> None:
    """Mathematically prove valid RFC 6902 array operations map accurately across dimensions."""
    base_state = {"arr": [1, 2, 3], "nested": {"key": "value"}}
    patch = StateMutationIntent(**patch_kwargs)
    manifest = StateDifferentialManifest(
        diff_id="did:web:patch-success",
        author_node_id="did:web:node-1",
        lamport_timestamp=1,
        vector_clock={"did:web:node-1": 1},
        patches=[patch],
    )
    new_state = apply_state_differential(base_state, manifest)
    assert new_state == expected_state


@pytest.mark.parametrize("payload", ["1 + 1"])
def test_verify_ast_safety_extra_valid(payload: str) -> None:
    assert verify_ast_safety(payload)


@pytest.mark.parametrize(
    ("payload", "match_str"),
    [
        ("a = 1", r"Payload is not valid syntax."),
        ("import os", r"Payload is not valid syntax."),
        ("1 +", r"Payload is not valid syntax."),
    ],
)
def test_verify_ast_safety_extra_invalid(payload: str, match_str: str) -> None:
    with pytest.raises(ValueError, match=match_str):
        verify_ast_safety(payload)


def test_verify_merkle_proof() -> None:
    node1 = ExecutionNodeReceipt(request_id="1", inputs=1, outputs=2)
    node1_hash = node1.generate_node_hash()

    node2 = ExecutionNodeReceipt(
        request_id="2", root_request_id="1", parent_request_id="1", inputs=2, outputs=3, parent_hashes=[node1_hash]
    )

    assert verify_merkle_proof([node1, node2])


@pytest.mark.parametrize(
    ("patch_intent", "expected_state"),
    [
        (StateMutationIntent(op="add", path="/a/0", value=0), {"a": [0, 1, 2], "b": [1, 2, 3]}),
        (StateMutationIntent(op="remove", path="/b/1"), {"a": [1, 2], "b": [1, 3]}),
        (StateMutationIntent(op="replace", path="/a/0", value=99), {"a": [99, 2], "b": [1, 2, 3]}),
        (StateMutationIntent(op="move", path="/a/0", **{"from": "/b/0"}), {"a": [1, 1, 2], "b": [2, 3]}),
        (StateMutationIntent(op="copy", path="/a/-", **{"from": "/b/0"}), {"a": [1, 2, 1], "b": [1, 2, 3]}),
    ],
)
def test_apply_state_differential_atomic_array_operations(
    patch_intent: StateMutationIntent, expected_state: dict[str, Any]
) -> None:
    manifest = StateDifferentialManifest(
        diff_id="d1", author_node_id="did:example:1", lamport_timestamp=1, vector_clock={}, patches=[patch_intent]
    )
    current_state = {"a": [1, 2], "b": [1, 2, 3]}
    new_state = apply_state_differential(current_state, manifest)
    assert new_state == expected_state


@pytest.mark.parametrize(
    ("patch_intent", "current_state", "match_str"),
    [
        (StateMutationIntent(op="test", path="/a", value=2), {"a": 1}, r"Patch test operation failed"),
        (StateMutationIntent(op="add", path="a", value=2), {"a": 1}, r"Invalid JSON pointer"),
        (StateMutationIntent(op="add", path="/a/b", value=2), {"a": 1}, r"Cannot add to path"),
        (StateMutationIntent(op="remove", path="/b"), {"a": 1}, r"Cannot remove from path"),
        (StateMutationIntent(op="replace", path="/a/-", value=2), {"a": [1]}, r"Cannot replace at path"),
        (
            StateMutationIntent(op="move", path="/a", **{"from": "/b/-"}),
            {"b": [1]},
            r"Cannot extract from end of array",
        ),
    ],
)
def test_apply_state_differential_atomic_errors(
    patch_intent: StateMutationIntent, current_state: dict[str, Any], match_str: str
) -> None:
    manifest = StateDifferentialManifest(
        diff_id="d1", author_node_id="did:example:1", lamport_timestamp=1, vector_clock={}, patches=[patch_intent]
    )
    with pytest.raises(ValueError, match=match_str):
        apply_state_differential(current_state, manifest)
