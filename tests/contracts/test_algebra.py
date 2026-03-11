import pytest
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coreason_manifest.spec.ontology import (
    DAGTopologyManifest,
    DynamicRoutingManifest,
    WorkflowManifest,
)
from coreason_manifest.utils.algebra import (
    align_semantic_manifolds,
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
