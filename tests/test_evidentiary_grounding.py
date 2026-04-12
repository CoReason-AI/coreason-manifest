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
