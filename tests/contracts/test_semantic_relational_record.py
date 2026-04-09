from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    SemanticRelationalRecordState,
    TemporalBoundsProfile,
    UpperOntologyClassProfile,
)


@given(st.integers(min_value=15000, max_value=20000))
def test_semantic_relational_record_payload_bounds(node_count: int) -> None:
    # We create a dictionary to trigger JSON Bomb protection
    # The threshold is dynamically set at 10,000 for the default hardware limit.
    large_dict: dict[str, Any] = {"level_1": [{"node": i} for i in range(node_count)]}

    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit"):
        SemanticRelationalRecordState(
            event_cid="test-event-cid-1",
            record_cid="test-record-cid-1",
            timestamp=123456789.0,
            ontology_class=UpperOntologyClassProfile.CONTINUANT,
            payload_injection_zone=large_dict,
        )


@given(st.floats(min_value=0.0, max_value=1000000000.0))
def test_semantic_relational_record_occurrent_temporality(valid_from: float) -> None:
    # Test valid occurrent with temporal bounds
    tb = TemporalBoundsProfile(valid_from=valid_from)
    record = SemanticRelationalRecordState(
        event_cid="test-event-cid-2",
        record_cid="test-record-cid-2",
        timestamp=123456789.0,
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
            record_cid="test-record-cid-3",
            timestamp=123456789.0,
            ontology_class=UpperOntologyClassProfile.OCCURRENT,
            payload_injection_zone={"key": "value"},
        )


@given(st.floats(min_value=0.0, max_value=1000000000.0))
def test_semantic_relational_record_continuant_no_temporality(timestamp: float) -> None:
    record = SemanticRelationalRecordState(
        event_cid="test-event-cid-4",
        record_cid="test-record-cid-4",
        timestamp=timestamp,
        ontology_class=UpperOntologyClassProfile.CONTINUANT,
        payload_injection_zone={"key": "value"},
    )
    assert record.ontology_class == UpperOntologyClassProfile.CONTINUANT
