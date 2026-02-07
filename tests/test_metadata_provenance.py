from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData


def test_manifest_metadata_provenance_ai() -> None:
    """Test AI-generated provenance."""
    metadata = ManifestMetadata(
        name="AI Workflow",
        version="1.0.0",
        provenance=ProvenanceData(
            type="ai",
            generated_by="coreason-strategist-v1",
            confidence_score=0.95,
            rationale="AI generated reasoning",
            original_intent="User want a workflow",
            generated_date=datetime(2023, 1, 1, tzinfo=UTC),
        ),
    )
    assert metadata.name == "AI Workflow"
    assert metadata.version == "1.0.0"
    assert metadata.provenance is not None
    assert metadata.provenance.type == "ai"
    assert metadata.provenance.generated_by == "coreason-strategist-v1"
    assert metadata.provenance.confidence_score == 0.95
    assert metadata.provenance.rationale == "AI generated reasoning"
    assert metadata.provenance.original_intent == "User want a workflow"
    assert metadata.provenance.generated_date == datetime(2023, 1, 1, tzinfo=UTC)


def test_manifest_metadata_provenance_human() -> None:
    """Test Human-authored provenance."""
    metadata = ManifestMetadata(
        name="Human Workflow",
        # version default check
        provenance=ProvenanceData(type="human", generated_by="Alice", methodology="Manual Design"),
    )
    assert metadata.name == "Human Workflow"
    assert metadata.version == "0.1.0"  # Default
    assert metadata.provenance is not None
    assert metadata.provenance.type == "human"
    assert metadata.provenance.generated_by == "Alice"
    assert metadata.provenance.methodology == "Manual Design"
    assert metadata.provenance.confidence_score is None


def test_manifest_metadata_confidence_score_validation() -> None:
    """Test confidence_score validation."""
    # Test valid score
    p = ProvenanceData(type="ai", generated_by="sys", confidence_score=0.0)
    assert p.confidence_score == 0.0

    p2 = ProvenanceData(type="ai", generated_by="sys", confidence_score=1.0)
    assert p2.confidence_score == 1.0

    # Test invalid score > 1.0
    with pytest.raises(ValidationError) as excinfo:
        ProvenanceData(type="ai", generated_by="sys", confidence_score=1.5)
    assert "less than or equal to 1" in str(excinfo.value)

    # Test invalid score < 0.0
    with pytest.raises(ValidationError) as excinfo:
        ProvenanceData(type="ai", generated_by="sys", confidence_score=-0.1)
    assert "greater than or equal to 0" in str(excinfo.value)


def test_manifest_metadata_extra_fields() -> None:
    """Test that extra fields are still allowed in Metadata and Provenance."""
    metadata = ManifestMetadata(
        name="Test Extra",
        unknown_field="some value",
        provenance=ProvenanceData(type="hybrid", generated_by="Team", extra_provenance="extra"),
    )
    # Check via model_dump
    dump = metadata.model_dump()
    assert dump["unknown_field"] == "some value"
    assert dump["provenance"]["extra_provenance"] == "extra"


def test_manifest_metadata_complex_roundtrip() -> None:
    """Test full serialization roundtrip."""
    data = {
        "name": "Complex Case",
        "version": "2.0.0",
        "provenance": {
            "type": "ai",
            "generated_by": "the-architect",
            "confidence_score": 0.88,
            "rationale": "Complex rationale",
            "original_intent": "Make it so.",
            "generated_date": "2023-10-27T10:00:00Z",
        },
    }

    # Create from dict
    m = ManifestMetadata(**data)

    # Verify
    assert m.provenance is not None
    assert m.provenance.confidence_score == 0.88

    # Serialize
    json_str = m.model_dump_json()

    # Deserialize
    m2 = ManifestMetadata.model_validate_json(json_str)

    # Verify equality
    assert m2.name == m.name
    assert m2.version == "2.0.0"
    assert m2.provenance is not None
    assert m2.provenance.generated_by == "the-architect"
    assert m2.provenance.generated_date is not None
    assert m2.provenance.generated_date.year == 2023
