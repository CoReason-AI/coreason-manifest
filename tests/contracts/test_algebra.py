import base64
import struct

import pytest
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coreason_manifest.spec.ontology import (
    DAGTopologyManifest,
    DynamicRoutingManifest,
    EpistemicLedgerState,
    OntologicalAlignmentPolicy,
    TokenBurnReceipt,
    VectorEmbeddingState,
    WorkflowManifest,
)
from coreason_manifest.utils.algebra import (
    align_semantic_manifolds,
    calculate_latent_alignment,
    calculate_remaining_compute,
    compute_topology_hash,
    generate_correction_prompt,
    get_ontology_schema,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    validate_payload,
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


class MockStrictSchema(BaseModel):
    name: str = Field(min_length=5)
    age: int


def test_generate_correction_prompt_translation() -> None:
    try:
        MockStrictSchema(name="Bob", age="not_an_int")
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


def test_calculate_remaining_compute_valid() -> None:
    receipt1 = TokenBurnReceipt(
        event_id="burn-1",
        timestamp=100.0,
        tool_invocation_id="tool-1",
        input_tokens=5,
        output_tokens=5,
        burn_magnitude=10,
    )
    receipt2 = TokenBurnReceipt(
        event_id="burn-2",
        timestamp=101.0,
        tool_invocation_id="tool-2",
        input_tokens=10,
        output_tokens=10,
        burn_magnitude=20,
    )
    ledger = EpistemicLedgerState(history=[receipt1, receipt2])
    remaining = calculate_remaining_compute(ledger, initial_escrow_magnitude=50)
    assert remaining == 20


def test_calculate_remaining_compute_exhaustion() -> None:
    receipt1 = TokenBurnReceipt(
        event_id="burn-1",
        timestamp=100.0,
        tool_invocation_id="tool-1",
        input_tokens=5,
        output_tokens=5,
        burn_magnitude=10,
    )
    receipt2 = TokenBurnReceipt(
        event_id="burn-2",
        timestamp=101.0,
        tool_invocation_id="tool-2",
        input_tokens=10,
        output_tokens=10,
        burn_magnitude=20,
    )
    ledger = EpistemicLedgerState(history=[receipt1, receipt2])
    with pytest.raises(ValueError, match="Mathematical Boundary Breached"):
        calculate_remaining_compute(ledger, initial_escrow_magnitude=25)


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
