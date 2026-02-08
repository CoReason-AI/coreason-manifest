# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.compliance import (
    AuditContentMode,
    AuditLevel,
    ComplianceConfig,
    IntegrityConfig,
    IntegrityLevel,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
)


def test_zero_copy_configuration() -> None:
    """Test Case 1: Zero-Copy Configuration."""
    config = ComplianceConfig(
        integrity=IntegrityConfig(
            input_mode=AuditContentMode.FULL_PAYLOAD,
            output_mode=AuditContentMode.REFERENCE_ONLY,
        )
    )

    assert config.integrity.input_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.output_mode == AuditContentMode.REFERENCE_ONLY
    assert config.integrity.hash_algorithm == "sha256"  # Default check


def test_high_integrity_configuration() -> None:
    """Test Case 2: High Integrity Configuration."""
    config = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT,
        integrity=IntegrityConfig(
            integrity_level=IntegrityLevel.BLOCKCHAIN_ANCHOR
        )
    )

    assert config.audit_level == AuditLevel.GXP_COMPLIANT
    assert config.integrity.integrity_level == IntegrityLevel.BLOCKCHAIN_ANCHOR


def test_defaults() -> None:
    """Test Case 3: Defaults."""
    config = ComplianceConfig()

    # Assert defaults
    assert config.integrity.input_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.output_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.integrity_level == IntegrityLevel.NONE
    assert config.integrity.hash_algorithm == "sha256"


def test_serialization() -> None:
    """Test Case 4: Serialization."""
    integrity_config = IntegrityConfig(
        input_mode=AuditContentMode.REDACTED,
        integrity_level=IntegrityLevel.DIGITAL_SIGNATURE,
    )

    compliance_config = ComplianceConfig(
        integrity=integrity_config
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Veritas Harvest Test"),
        interface=RecipeInterface(),
        compliance=compliance_config,
        topology=GraphTopology(
            nodes=[AgentNode(id="A", agent_ref="ref-a")],
            edges=[],
            entry_point="A",
        ),
    )

    # Dump to JSON
    json_output = recipe.model_dump(mode="json")

    # Verify nested structure
    assert "compliance" in json_output
    assert "integrity" in json_output["compliance"]
    integrity = json_output["compliance"]["integrity"]

    assert integrity["input_mode"] == "redacted"
    assert integrity["integrity_level"] == "signature"
    assert integrity["hash_algorithm"] == "sha256"  # Default preserved
