from datetime import datetime

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData


def test_manifest_metadata_provenance_valid() -> None:
    """Test valid provenance fields."""
    provenance = ProvenanceData(
        type="ai",
        confidence_score=0.95,
        rationale="AI generated reasoning",
        original_intent="User want a workflow",
        generated_by="coreason-strategist-v1",
    )
    metadata = ManifestMetadata(
        name="Test Workflow",
        version="1.0.0",
        provenance=provenance,
    )
    assert metadata.name == "Test Workflow"
    assert metadata.version == "1.0.0"
    assert metadata.provenance is not None
    assert metadata.provenance.confidence_score == 0.95
    assert metadata.provenance.rationale == "AI generated reasoning"
    assert metadata.provenance.original_intent == "User want a workflow"
    assert metadata.provenance.generated_by == "coreason-strategist-v1"


def test_provenance_confidence_score_validation() -> None:
    """Test confidence_score validation in ProvenanceData."""
    # Test valid score
    p1 = ProvenanceData(type="ai", confidence_score=0.0)
    assert p1.confidence_score == 0.0

    p2 = ProvenanceData(type="ai", confidence_score=1.0)
    assert p2.confidence_score == 1.0

    # Test invalid score > 1.0
    with pytest.raises(ValidationError) as excinfo:
        ProvenanceData(type="ai", confidence_score=1.5)
    assert "less than or equal to 1" in str(excinfo.value)

    # Test invalid score < 0.0
    with pytest.raises(ValidationError) as excinfo:
        ProvenanceData(type="ai", confidence_score=-0.1)
    assert "greater than or equal to 0" in str(excinfo.value)


def test_provenance_type_validation() -> None:
    """Test type field validation."""
    # Valid types
    assert ProvenanceData(type="ai").type == "ai"
    assert ProvenanceData(type="human").type == "human"
    assert ProvenanceData(type="hybrid").type == "hybrid"

    # Invalid type
    with pytest.raises(ValidationError) as excinfo:
        ProvenanceData(type="alien")
    assert "Input should be 'ai', 'human' or 'hybrid'" in str(excinfo.value)


def test_manifest_metadata_extra_fields() -> None:
    """Test that extra fields are still allowed on ManifestMetadata."""
    metadata = ManifestMetadata(name="Test Extra", unknown_field="some value")
    assert metadata.name == "Test Extra"

    # Check via model_dump
    dump = metadata.model_dump()
    assert dump["unknown_field"] == "some value"


def test_provenance_extra_forbid() -> None:
    """Test that ProvenanceData forbids extra fields."""
    with pytest.raises(ValidationError) as excinfo:
        ProvenanceData(type="ai", extra_field="forbidden")  # type: ignore[call-arg]
    assert "Extra inputs are not permitted" in str(excinfo.value)


def test_provenance_serialization() -> None:
    """Test full serialization roundtrip."""
    provenance = ProvenanceData(
        type="hybrid",
        generated_date=datetime(2025, 1, 1, 12, 0, 0),
        methodology="human-review",
    )
    metadata = ManifestMetadata(name="Roundtrip", provenance=provenance)

    json_str = metadata.model_dump_json()
    m2 = ManifestMetadata.model_validate_json(json_str)

    assert m2.provenance is not None
    assert m2.provenance.type == "hybrid"
    assert m2.provenance.generated_date == datetime(2025, 1, 1, 12, 0, 0)
    assert m2.provenance.methodology == "human-review"
