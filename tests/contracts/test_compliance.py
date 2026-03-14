# Copyright (c) 2026 CoReason, Inc.
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

from coreason_manifest.spec.ontology import ComplianceRatingScheme, ExternalPayloadManifest


def test_compliance_rating_scheme_boundary_enforcement() -> None:
    # A grade payload should successfully instantiate
    crs_a = ComplianceRatingScheme(
        c2pa_metadata_present=True,
        licensing_constraints=["MIT", "Apache"],
        opt_out_mechanisms=["robots.txt"],
        final_grade="A"
    )
    assert crs_a.final_grade == "A"
    assert crs_a.licensing_constraints == ["Apache", "MIT"]  # sorted

    # C grade payload should successfully instantiate
    crs_c = ComplianceRatingScheme(
        c2pa_metadata_present=False,
        licensing_constraints=["CC-BY"],
        opt_out_mechanisms=[],
        final_grade="C"
    )
    assert crs_c.final_grade == "C"

    # F grade payload should throw ValueError / ValidationError
    with pytest.raises(ValidationError, match="CRITICAL COMPLIANCE VIOLATION"):
        ComplianceRatingScheme(
            c2pa_metadata_present=False,
            licensing_constraints=[],
            opt_out_mechanisms=[],
            final_grade="F"
        )


def test_external_payload_manifest_rejects_f_grade() -> None:
    # Test through the external payload manifest boundary
    with pytest.raises(ValidationError, match="CRITICAL COMPLIANCE VIOLATION"):
        ExternalPayloadManifest(
            payload_id="external_dataset_001",
            compliance_rating=ComplianceRatingScheme(
                c2pa_metadata_present=False,
                licensing_constraints=["none"],
                opt_out_mechanisms=["none"],
                final_grade="F"
            ),
            raw_content_hash="d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"
        )
