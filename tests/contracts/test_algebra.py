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
    OntologicalAlignmentPolicy,
    StateDifferentialManifest,
    StateMutationIntent,
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

# Generate a list of StateMutationIntent


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
