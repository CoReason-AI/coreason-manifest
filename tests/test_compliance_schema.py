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
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    AuditLevel,
    ComplianceConfig,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
    RetentionPolicy,
)


def test_compliance_defaults() -> None:
    """Test default values for ComplianceConfig."""
    config = ComplianceConfig()

    assert config.audit_level == AuditLevel.BASIC
    assert config.retention == RetentionPolicy.THIRTY_DAYS
    assert config.generate_aibom is False
    assert config.generate_pdf_report is False
    assert config.require_signature is False
    assert config.mask_pii is True


def test_compliance_custom_values() -> None:
    """Test setting custom values for ComplianceConfig."""
    config = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT,
        retention=RetentionPolicy.SEVEN_YEARS,
        generate_aibom=True,
        require_signature=True,
        mask_pii=False,
    )

    assert config.audit_level == AuditLevel.GXP_COMPLIANT
    assert config.retention == RetentionPolicy.SEVEN_YEARS
    assert config.generate_aibom is True
    assert config.require_signature is True
    assert config.mask_pii is False


def test_compliance_enums() -> None:
    """Verify enum values match the spec."""
    assert AuditLevel.NONE == "none"
    assert AuditLevel.BASIC == "basic"
    assert AuditLevel.FULL == "full"
    assert AuditLevel.GXP_COMPLIANT == "gxp"

    assert RetentionPolicy.EPHEMERAL == "ephemeral"
    assert RetentionPolicy.THIRTY_DAYS == "30_days"
    assert RetentionPolicy.ONE_YEAR == "1_year"
    assert RetentionPolicy.SEVEN_YEARS == "7_years"


def test_recipe_with_compliance() -> None:
    """Test full recipe definition with compliance config."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Compliance Test"),
        interface=RecipeInterface(),
        compliance=ComplianceConfig(
            audit_level=AuditLevel.FULL,
            retention=RetentionPolicy.ONE_YEAR,
        ),
        topology=GraphTopology(
            nodes=[AgentNode(id="A", agent_ref="ref-a")],
            edges=[],
            entry_point="A",
        ),
    )

    assert recipe.compliance is not None
    assert recipe.compliance.audit_level == AuditLevel.FULL
    assert recipe.compliance.retention == RetentionPolicy.ONE_YEAR


def test_recipe_without_compliance() -> None:
    """Test recipe definition without compliance config (optional)."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="No Compliance Test"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[AgentNode(id="A", agent_ref="ref-a")],
            edges=[],
            entry_point="A",
        ),
    )

    assert recipe.compliance is None


def test_compliance_roundtrip() -> None:
    """Test JSON serialization/deserialization."""
    original = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT,
        generate_pdf_report=True,
    )

    json_str = original.model_dump_json()
    loaded = ComplianceConfig.model_validate_json(json_str)

    assert loaded == original
    assert loaded.audit_level == AuditLevel.GXP_COMPLIANT
    assert loaded.generate_pdf_report is True
