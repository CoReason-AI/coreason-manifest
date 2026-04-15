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
from pydantic import HttpUrl

from coreason_manifest.spec.ontology import HTTPTransportProfile, SSETransportProfile


@pytest.mark.parametrize(
    "url",
    [
        "https://1.1.1.1/",
        "http://1.1.1.1/",
    ],
)
def test_http_transport_profile_valid(url: str) -> None:
    profile = HTTPTransportProfile(uri=HttpUrl(url))
    assert str(profile.uri) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://1.1.1.1/",
        "http://1.1.1.1/",
    ],
)
def test_sse_transport_profile_valid(url: str) -> None:
    profile = SSETransportProfile(uri=HttpUrl(url))
    assert str(profile.uri) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://1.1.1.1/sparql",
        "http://1.1.1.1/sparql",
    ],
)
def test_sparql_query_intent_valid(url: str) -> None:
    from coreason_manifest.spec.ontology import SPARQLQueryIntent

    intent = SPARQLQueryIntent(
        target_endpoint=HttpUrl(url),
        query_string="SELECT * WHERE { ?s ?p ?o }",
    )
    assert str(intent.target_endpoint) == url


def test_sparql_query_result_receipt() -> None:
    from coreason_manifest.spec.ontology import SPARQLQueryResultReceipt

    receipt = SPARQLQueryResultReceipt(
        event_cid="event-123",
        timestamp=1620000000.0,
        query_intent_cid="intent-123",
        returned_bindings={"bindings": {"type": "array", "items": []}},
        execution_time_ms=150,
    )
    assert receipt.execution_time_ms == 150


def test_rdf_serialization_intent_shacl_governance() -> None:
    from pydantic import AnyUrl

    from coreason_manifest.spec.ontology import RDFSerializationIntent, SHACLValidationSLA

    # Missing SHACL should fail for strictly typed target_formats (xml, json-ld)
    with pytest.raises(ValueError, match="mathematically requires a SHACLValidationSLA"):
        RDFSerializationIntent(
            export_cid="export-1",
            target_graph_cid="graph-1",
            target_format="xml",
            base_uri_namespace=AnyUrl("http://example.com"),
        )

    with pytest.raises(ValueError, match="mathematically requires a SHACLValidationSLA"):
        RDFSerializationIntent(
            export_cid="export-1",
            target_graph_cid="graph-1",
            target_format="json-ld",
            base_uri_namespace=AnyUrl("http://example.com"),
        )

    # Should pass when correctly supplied
    intent = RDFSerializationIntent(
        export_cid="export-1",
        target_graph_cid="graph-1",
        target_format="json-ld",
        base_uri_namespace=AnyUrl("http://example.com"),
        shacl_governance=SHACLValidationSLA(
            shacl_shape_graph_uri=AnyUrl("http://example.com/shape.ttl"), violation_action="DROP_GRAPH"
        ),
    )
    assert intent.shacl_governance is not None
