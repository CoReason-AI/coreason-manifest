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

from coreason_manifest.spec.ontology import (
    C2PAExportClaim,
    ComplianceRatingManifest,
    CRSGrade,
    EnvironmentContextManifest,
)


def test_compliance_rating_manifest_valid_a() -> None:
    manifest = ComplianceRatingManifest(
        claimed_grade=CRSGrade.A,
        c2pa_presence_score=0.9,
        opt_out_mechanisms_score=0.9,
        licensing_score=0.9,
    )
    assert manifest.claimed_grade == CRSGrade.A


def test_compliance_rating_manifest_rejects_f_g() -> None:
    with pytest.raises(ValueError, match="Compliance Violation"):
        ComplianceRatingManifest(
            claimed_grade=CRSGrade.F,
            c2pa_presence_score=0.1,
            opt_out_mechanisms_score=0.1,
            licensing_score=0.1,
        )
    with pytest.raises(ValueError, match="Compliance Violation"):
        ComplianceRatingManifest(
            claimed_grade=CRSGrade.G,
            c2pa_presence_score=0.1,
            opt_out_mechanisms_score=0.1,
            licensing_score=0.1,
        )


def test_compliance_rating_manifest_mathematical_firewall() -> None:
    # A claimed but computed is B (0.8)
    with pytest.raises(ValueError, match="Mathematical Contradiction"):
        ComplianceRatingManifest(
            claimed_grade=CRSGrade.A,
            c2pa_presence_score=0.8,
            opt_out_mechanisms_score=0.8,
            licensing_score=0.8,
        )


def test_compliance_rating_manifest_deterministic_hashing() -> None:
    manifest1 = ComplianceRatingManifest(
        claimed_grade=CRSGrade.A,
        c2pa_presence_score=0.9,
        opt_out_mechanisms_score=0.9,
        licensing_score=0.9,
    )
    manifest2 = ComplianceRatingManifest(
        licensing_score=0.9,
        opt_out_mechanisms_score=0.9,
        c2pa_presence_score=0.9,
        claimed_grade=CRSGrade.A,
    )
    assert hash(manifest1) == hash(manifest2)
    assert manifest1.model_dump_canonical() == manifest2.model_dump_canonical()


def test_environment_context_manifest_deterministic_hashing() -> None:
    env1 = EnvironmentContextManifest(
        gpu_architecture="A100",
        vram_allocated=1024,
        python_version="3.12.0",
        dependency_hashes={"b": "2", "a": "1"},
        cryptographic_nonces=["y", "x"],
    )
    env2 = EnvironmentContextManifest(
        vram_allocated=1024,
        python_version="3.12.0",
        dependency_hashes={"a": "1", "b": "2"},
        cryptographic_nonces=["x", "y"],
        gpu_architecture="A100",
    )
    assert env1.cryptographic_nonces == ["x", "y"]
    assert hash(env1) == hash(env2)
    assert env1.model_dump_canonical() == env2.model_dump_canonical()


def test_c2pa_export_claim_validation() -> None:
    with pytest.raises(ValidationError):
        C2PAExportClaim(watermark_receipt_hash="invalid_hash", c2pa_assertions=[], c2pa_ingredients=[])

    valid_claim = C2PAExportClaim(
        watermark_receipt_hash="a" * 64, c2pa_assertions=[{"type": "stds.c2pa.action", "data": {}}], c2pa_ingredients=[]
    )
    assert valid_claim.watermark_receipt_hash == "a" * 64
