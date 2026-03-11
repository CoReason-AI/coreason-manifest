import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.spec.ontology import DynamicRoutingManifest, WorkflowManifest
from coreason_manifest.utils.algebra import (
    get_ontology_schema,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
    validate_payload,
)


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
