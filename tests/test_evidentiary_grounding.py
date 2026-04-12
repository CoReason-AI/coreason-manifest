# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest

from coreason_manifest.spec.ontology import EvidentiaryCitationState


def test_evidentiary_citation_state_ssrf_quarantine() -> None:
    # Test that instantiating EvidentiaryCitationState with a Bogon IP raises a validation error
    from pydantic import HttpUrl, TypeAdapter

    url_adapter = TypeAdapter(HttpUrl)
    with pytest.raises(ValueError, match="SSRF restricted IP detected"):
        EvidentiaryCitationState(
            citation_cid="test_cid_123",
            source_url=url_adapter.validate_python("http://127.0.0.1"),
            extracted_snippet="Some test snippet.",
            nli_entailment_score=0.9,
        )


def test_evidentiary_citation_state_valid() -> None:
    from pydantic import HttpUrl, TypeAdapter

    url_adapter = TypeAdapter(HttpUrl)
    state = EvidentiaryCitationState(
        citation_cid="test_cid_123",
        source_url=url_adapter.validate_python("http://example.com"),
        extracted_snippet="Some test snippet.",
        nli_entailment_score=0.9,
    )
    assert state.source_url == url_adapter.validate_python("http://example.com")


def test_dempster_shafer_belief_vector_sorting() -> None:
    from pydantic import HttpUrl, TypeAdapter

    from coreason_manifest.spec.ontology import DempsterShaferBeliefVector

    url_adapter = TypeAdapter(HttpUrl)
    c1 = EvidentiaryCitationState(
        citation_cid="b_cid",
        source_url=url_adapter.validate_python("http://example.com"),
        extracted_snippet="Some test snippet.",
        nli_entailment_score=0.9,
    )
    c2 = EvidentiaryCitationState(
        citation_cid="a_cid",
        source_url=url_adapter.validate_python("http://example.com"),
        extracted_snippet="Some test snippet.",
        nli_entailment_score=0.8,
    )
    vector = DempsterShaferBeliefVector(
        lexical_confidence=0.5,
        semantic_distance=0.5,
        structural_graph_confidence=0.5,
        epistemic_conflict_mass=0.5,
        supporting_citations=[c1, c2],
    )
    assert vector.supporting_citations[0].citation_cid == "a_cid"
    assert vector.supporting_citations[1].citation_cid == "b_cid"


def test_epistemic_starvation_event_sorting() -> None:
    from pydantic import HttpUrl, TypeAdapter

    from coreason_manifest.spec.ontology import EpistemicStarvationEvent

    url_adapter = TypeAdapter(HttpUrl)
    c1 = EvidentiaryCitationState(
        citation_cid="b_cid",
        source_url=url_adapter.validate_python("http://example.com"),
        extracted_snippet="Some test snippet.",
        nli_entailment_score=0.9,
    )
    c2 = EvidentiaryCitationState(
        citation_cid="a_cid",
        source_url=url_adapter.validate_python("http://example.com"),
        extracted_snippet="Some test snippet.",
        nli_entailment_score=0.8,
    )
    event = EpistemicStarvationEvent(
        event_cid="test_event_123",
        timestamp=0.0,
        starved_edge_cid="test_edge_123",
        failed_citations=[c1, c2],
        diagnostic_reason="Exhausted retries",
    )
    assert event.failed_citations[0].citation_cid == "a_cid"
    assert event.failed_citations[1].citation_cid == "b_cid"
