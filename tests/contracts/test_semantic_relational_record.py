from typing import Any, cast

import pytest

from coreason_manifest.spec.ontology import (
    JsonPrimitiveState,
    SemanticRelationalRecordState,
    TemporalBoundsProfile,
    UpperOntologyClassProfile,
)


def test_semantic_relational_record_payload_bounds() -> None:
    # Create a dictionary with more than 10,000 nodes to trigger JSON Bomb protection
    large_dict: dict[str, Any] = {"level_1": [{"node": i} for i in range(15000)]}

    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit"):
        SemanticRelationalRecordState(
            event_cid="test-event-cid-1",
            timestamp=123456789.0,
            record_cid="test-record-cid",
            ontology_class=UpperOntologyClassProfile.CONTINUANT,
            payload_injection_zone=cast("dict[str, JsonPrimitiveState]", large_dict),
        )


def test_semantic_relational_record_occurrent_temporality() -> None:
    # Test valid occurrent with temporal bounds
    tb = TemporalBoundsProfile(valid_from=123.0)
    record = SemanticRelationalRecordState(
        event_cid="test-event-cid-2",
        timestamp=123456789.0,
        record_cid="test-record-cid",
        ontology_class=UpperOntologyClassProfile.OCCURRENT,
        temporal_bounds=tb,
        payload_injection_zone={"key": "value"},
    )
    assert record.ontology_class == UpperOntologyClassProfile.OCCURRENT

    # Test occurrent without temporal bounds
    with pytest.raises(
        ValueError,
        match=r"Ontological Paradox: An OCCURRENT must mathematically possess a temporal_bounds coordinate\.",
    ):
        SemanticRelationalRecordState(
            event_cid="test-event-cid-3",
            timestamp=123456789.0,
            record_cid="test-record-cid",
            ontology_class=UpperOntologyClassProfile.OCCURRENT,
            payload_injection_zone={"key": "value"},
        )


def test_semantic_relational_record_continuant_no_temporality() -> None:
    record = SemanticRelationalRecordState(
        event_cid="test-event-cid-4",
        timestamp=123456789.0,
        record_cid="test-record-cid",
        ontology_class=UpperOntologyClassProfile.CONTINUANT,
        payload_injection_zone={"key": "value"},
    )
    assert record.ontology_class == UpperOntologyClassProfile.CONTINUANT
