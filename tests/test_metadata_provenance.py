# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata


def test_manifest_metadata_provenance_valid() -> None:
    """Test valid provenance fields."""
    metadata = ManifestMetadata(
        name="Test Workflow",
        confidence_score=0.95,
        generation_rationale="AI generated reasoning",
        original_user_intent="User want a workflow",
        generated_by="coreason-strategist-v1",
    )
    assert metadata.name == "Test Workflow"
    assert metadata.confidence_score == 0.95
    assert metadata.generation_rationale == "AI generated reasoning"
    assert metadata.original_user_intent == "User want a workflow"
    assert metadata.generated_by == "coreason-strategist-v1"


def test_manifest_metadata_confidence_score_validation() -> None:
    """Test confidence_score validation."""
    # Test valid score
    m1 = ManifestMetadata(name="Valid", confidence_score=0.0)
    assert m1.confidence_score == 0.0

    m2 = ManifestMetadata(name="Valid", confidence_score=1.0)
    assert m2.confidence_score == 1.0

    # Test invalid score > 1.0
    with pytest.raises(ValidationError) as excinfo:
        ManifestMetadata(name="Invalid", confidence_score=1.5)
    # Pydantic v2 message may say '1' or '1.0'
    assert "less than or equal to 1" in str(excinfo.value)

    # Test invalid score < 0.0
    with pytest.raises(ValidationError) as excinfo:
        ManifestMetadata(name="Invalid", confidence_score=-0.1)
    # Pydantic v2 message may say '0' or '0.0'
    assert "greater than or equal to 0" in str(excinfo.value)


def test_manifest_metadata_extra_fields() -> None:
    """Test that extra fields are still allowed."""
    # Pydantic V2 with extra='allow' stores in model_extra
    # Access via attribute depends on __getattr__ implementation in base class
    # but we can definitely check via dictionary access or model_dump
    metadata = ManifestMetadata(name="Test Extra", unknown_field="some value")
    assert metadata.name == "Test Extra"

    # Check via model_dump
    dump = metadata.model_dump()
    assert dump["unknown_field"] == "some value"

    # Check via direct attribute access (if supported by Pydantic V2 ConfigDict)
    # Based on local test, it seems supported
    assert getattr(metadata, "unknown_field", None) == "some value"


def test_manifest_metadata_edge_cases() -> None:
    """Test edge cases for provenance fields."""
    # Empty strings
    m = ManifestMetadata(name="Empty Strings", generation_rationale="", original_user_intent="", generated_by="")
    assert m.generation_rationale == ""
    assert m.original_user_intent == ""
    assert m.generated_by == ""

    # None values
    m_none = ManifestMetadata(
        name="None Values",
        confidence_score=None,
        generation_rationale=None,
        original_user_intent=None,
        generated_by=None,
    )
    assert m_none.confidence_score is None

    # Precision for float
    m_prec = ManifestMetadata(name="Precision", confidence_score=0.999999999)
    assert m_prec.confidence_score == 0.999999999

    # Minimal epsilon above 0
    m_min = ManifestMetadata(name="Min", confidence_score=0.000000001)
    assert m_min.confidence_score == 0.000000001


def test_manifest_metadata_complex_roundtrip() -> None:
    """Test full serialization roundtrip."""
    data = {
        "name": "Complex Case",
        "confidence_score": 0.88,
        "generation_rationale": "Complex rationale with \n newlines and symbols !@#$",
        "original_user_intent": "Make it so.",
        "generated_by": "the-architect",
        "extra_data": 123,
    }

    # Create from dict
    m = ManifestMetadata(**data)

    # Verify
    assert m.confidence_score == 0.88
    assert m.generation_rationale == data["generation_rationale"]

    # Serialize
    json_str = m.model_dump_json()

    # Deserialize
    m2 = ManifestMetadata.model_validate_json(json_str)

    # Verify equality
    assert m2.name == m.name
    assert m2.confidence_score == m.confidence_score
    assert m2.generated_by == m.generated_by
    # Extra fields should be preserved in roundtrip
    assert getattr(m2, "extra_data", None) == 123


def test_manifest_metadata_type_coercion_failure() -> None:
    """Test strict typing where applicable."""
    # Pydantic will try to coerce strings to floats
    m = ManifestMetadata(name="Coercion", confidence_score="0.5")
    assert m.confidence_score == 0.5

    # Fail on invalid string for float
    with pytest.raises(ValidationError):
        ManifestMetadata(name="Fail", confidence_score="not-a-float")
