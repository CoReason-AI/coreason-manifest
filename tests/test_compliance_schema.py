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

from coreason_manifest.spec.v2.compliance import AuditLevel, ComplianceConfig, RetentionPolicy
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
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
    assert AuditLevel.NONE.value == "none"
    assert AuditLevel.BASIC.value == "basic"
    assert AuditLevel.FULL.value == "full"
    assert AuditLevel.GXP_COMPLIANT.value == "gxp"

    assert RetentionPolicy.EPHEMERAL.value == "ephemeral"
    assert RetentionPolicy.THIRTY_DAYS.value == "30_days"
    assert RetentionPolicy.ONE_YEAR.value == "1_year"
    assert RetentionPolicy.SEVEN_YEARS.value == "7_years"


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


def test_compliance_edge_cases_invalid_enum() -> None:
    """Test validation failure for invalid enum values."""
    with pytest.raises(ValidationError) as excinfo:
        ComplianceConfig.model_validate({"audit_level": "INVALID_LEVEL"})

    assert "Input should be 'none', 'basic', 'full' or 'gxp'" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        ComplianceConfig.model_validate({"retention": "100_years"})

    assert "Input should be 'ephemeral', '30_days', '1_year' or '7_years'" in str(excinfo.value)


def test_compliance_edge_cases_type_mismatch() -> None:
    """Test validation failure for type mismatch in boolean flags."""
    # Pydantic attempts coercion, so passing a string "true" works.
    # But passing a dict or list should fail.

    with pytest.raises(ValidationError) as excinfo:
        ComplianceConfig.model_validate({"generate_aibom": {"nested": "dict"}})

    assert "Input should be a valid boolean" in str(excinfo.value)


def test_complex_compliance_scenario() -> None:
    """Test a complex scenario mimicking a GxP Clinical Trial workflow."""

    # 1. Define strict compliance
    clinical_compliance = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT,
        retention=RetentionPolicy.SEVEN_YEARS,
        generate_aibom=True,
        generate_pdf_report=True,
        require_signature=True,
        mask_pii=False,  # Explicitly keeping PII for clinical records
    )

    # 2. Define recipe with this compliance
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(
            name="Clinical Trial Analysis",
            description="Analyzes patient data for adverse events.",
            version="1.0.0",
        ),
        interface=RecipeInterface(
            inputs={"patient_id": {"type": "string"}}, outputs={"risk_score": {"type": "number"}}
        ),
        compliance=clinical_compliance,
        topology=GraphTopology(
            nodes=[
                AgentNode(id="ingest", agent_ref="ingestion-bot"),
                AgentNode(id="analyze", agent_ref="clinical-reasoner"),
            ],
            edges=[{"source": "ingest", "target": "analyze"}],
            entry_point="ingest",
        ),
    )

    # 3. Serialize
    json_output = recipe.model_dump_json()

    # 4. Deserialize
    loaded_recipe = RecipeDefinition.model_validate_json(json_output)

    # 5. Verify integrity
    assert loaded_recipe.compliance is not None
    assert loaded_recipe.compliance.audit_level == AuditLevel.GXP_COMPLIANT
    assert loaded_recipe.compliance.mask_pii is False
    assert loaded_recipe.compliance.generate_aibom is True
    assert loaded_recipe.metadata.name == "Clinical Trial Analysis"


def test_compliance_field_alias() -> None:
    """Test that populate_by_name works (though we use snake_case)."""
    # Just verifying that passing arguments by name works as expected in constructor
    config = ComplianceConfig(audit_level=AuditLevel.NONE)
    assert config.audit_level == AuditLevel.NONE

    # Verify dict instantiation
    config_from_dict = ComplianceConfig.model_validate({"audit_level": "none"})
    assert config_from_dict.audit_level == AuditLevel.NONE


def test_compliance_extra_forbid() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError) as excinfo:
        ComplianceConfig(
            audit_level=AuditLevel.BASIC,
            extra_field="should_fail",  # type: ignore[call-arg]
        )
    assert "Extra inputs are not permitted" in str(excinfo.value)
