# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    JsonPrimitiveState,
    SemanticRelationalVectorState,
    TemporalBoundsProfile,
    UpperOntologyClassProfile,
)


@given(st.integers(min_value=15000, max_value=20000))
def test_semantic_relational_vector_payload_bounds(node_count: int) -> None:
    # We create a dictionary to trigger JSON Bomb protection
    # The threshold is dynamically set at 10,000 for the default hardware limit.
    large_dict: dict[str, Any] = {"level_1": [{"node": i} for i in range(node_count)]}

    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit"):
        SemanticRelationalVectorState(
            event_cid="test-event-cid-1",
            timestamp=123456789.0,
            ontology_class=UpperOntologyClassProfile.CONTINUANT,
            payload_injection_zone=cast("dict[str, JsonPrimitiveState]", large_dict),
        )


@given(st.floats(min_value=0.0, max_value=1000000000.0))
def test_semantic_relational_vector_occurrent_temporality(valid_from: float) -> None:
    # Test valid occurrent with temporal bounds
    tb = TemporalBoundsProfile(valid_from=valid_from)
    record = SemanticRelationalVectorState(
        event_cid="test-event-cid-2",
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
        SemanticRelationalVectorState(
            event_cid="test-event-cid-3",
            timestamp=123456789.0,
            ontology_class=UpperOntologyClassProfile.OCCURRENT,
            payload_injection_zone={"key": "value"},
        )


@given(st.floats(min_value=0.0, max_value=1000000000.0))
def test_semantic_relational_vector_continuant_no_temporality(timestamp: float) -> None:
    record = SemanticRelationalVectorState(
        event_cid="test-event-cid-4",
        timestamp=timestamp,
        ontology_class=UpperOntologyClassProfile.CONTINUANT,
        payload_injection_zone={"key": "value"},
    )
    assert record.ontology_class == UpperOntologyClassProfile.CONTINUANT
