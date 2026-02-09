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

from coreason_manifest.spec.v2.compliance import (
    AuditContentMode,
    AuditLevel,
    ComplianceConfig,
    IntegrityConfig,
    IntegrityLevel,
    RetentionPolicy,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
)


def test_zero_copy_configuration() -> None:
    """
    Test Case 1: Zero-Copy Configuration
    Goal: Verify that a high-volume output agent can be configured to not clutter the logs.
    """
    config = ComplianceConfig(
        audit_level=AuditLevel.FULL,
        retention=RetentionPolicy.THIRTY_DAYS,
        integrity=IntegrityConfig(
            input_mode=AuditContentMode.FULL_PAYLOAD, output_mode=AuditContentMode.REFERENCE_ONLY
        ),
    )

    assert config.integrity.input_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.output_mode == AuditContentMode.REFERENCE_ONLY


def test_high_integrity_configuration() -> None:
    """
    Test Case 2: High Integrity Configuration
    Goal: Verify the schema supports strict GxP requirements.
    """
    config = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT,
        integrity=IntegrityConfig(integrity_level=IntegrityLevel.BLOCKCHAIN_ANCHOR),
    )

    assert config.integrity.integrity_level == IntegrityLevel.BLOCKCHAIN_ANCHOR
    assert config.audit_level == AuditLevel.GXP_COMPLIANT


def test_compliance_defaults() -> None:
    """
    Test Case 3: Defaults
    Assert: integrity.input_mode defaults to FULL_PAYLOAD.
    Assert: integrity.integrity_level defaults to NONE.
    """
    config = ComplianceConfig()

    assert config.integrity.input_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.integrity_level == IntegrityLevel.NONE
    assert config.integrity.output_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity.hash_algorithm == "sha256"


def test_serialization() -> None:
    """
    Test Case 4: Serialization
    Goal: Ensure the nested integrity JSON structure is generated correctly.
    """
    metadata = ManifestMetadata(name="Veritas Test", description="Testing harvesting", version="1.0.0")

    compliance = ComplianceConfig(
        audit_level=AuditLevel.BASIC,
        integrity=IntegrityConfig(
            input_mode=AuditContentMode.REDACTED,
            output_mode=AuditContentMode.OFF,
            integrity_level=IntegrityLevel.CHECKSUM,
        ),
    )

    recipe = RecipeDefinition(
        metadata=metadata,
        interface=RecipeInterface(),
        compliance=compliance,
        topology=GraphTopology(nodes=[AgentNode(id="A", agent_ref="agent-a")], edges=[], entry_point="A"),
    )

    json_output = recipe.model_dump(mode="json")

    # Check structure
    assert "compliance" in json_output
    assert "integrity" in json_output["compliance"]

    integrity_data = json_output["compliance"]["integrity"]
    assert integrity_data["input_mode"] == "redacted"
    assert integrity_data["output_mode"] == "off"
    assert integrity_data["integrity_level"] == "checksum"

    # Round trip
    loaded_recipe = RecipeDefinition.model_validate(json_output)
    assert loaded_recipe.compliance is not None
    assert loaded_recipe.compliance.integrity.input_mode == AuditContentMode.REDACTED
    assert loaded_recipe.compliance.integrity.output_mode == AuditContentMode.OFF
    assert loaded_recipe.compliance.integrity.integrity_level == IntegrityLevel.CHECKSUM


def test_edge_case_invalid_enum() -> None:
    """
    Edge Case: Invalid enum values should raise ValidationError.
    """
    with pytest.raises(ValidationError) as excinfo:
        IntegrityConfig(input_mode="INVALID_MODE")

    assert "Input should be 'full_payload', 'redacted', 'reference_only' or 'off'" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        IntegrityConfig(integrity_level="SuperSecureBlockChain")

    assert "Input should be 'none', 'checksum', 'signature' or 'anchor'" in str(excinfo.value)


def test_complex_integrity_combination() -> None:
    """
    Complex Case: Mixed settings (e.g., REFERENCE_ONLY input, FULL_PAYLOAD output, ANCHOR integrity).
    """
    config = IntegrityConfig(
        input_mode=AuditContentMode.REFERENCE_ONLY,
        output_mode=AuditContentMode.FULL_PAYLOAD,
        integrity_level=IntegrityLevel.BLOCKCHAIN_ANCHOR,
        hash_algorithm="sha512",
    )

    assert config.input_mode == AuditContentMode.REFERENCE_ONLY
    assert config.output_mode == AuditContentMode.FULL_PAYLOAD
    assert config.integrity_level == IntegrityLevel.BLOCKCHAIN_ANCHOR
    assert config.hash_algorithm == "sha512"


def test_immutability() -> None:
    """
    Edge Case: Verify immutability of frozen config.
    """
    config = IntegrityConfig()
    with pytest.raises(ValidationError) as excinfo:
        config.input_mode = AuditContentMode.OFF  # type: ignore

    assert "Instance is frozen" in str(excinfo.value)


def test_full_recipe_integration_complex() -> None:
    """
    Complex Case: Full recipe with multiple nodes and detailed integrity config.
    """
    compliance = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT,
        integrity=IntegrityConfig(
            input_mode=AuditContentMode.REDACTED,
            output_mode=AuditContentMode.REFERENCE_ONLY,
            integrity_level=IntegrityLevel.DIGITAL_SIGNATURE,
        ),
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Recipe", version="2.0.0"),
        interface=RecipeInterface(),
        compliance=compliance,
        topology=GraphTopology(
            nodes=[
                AgentNode(id="Start", agent_ref="agent-1"),
                AgentNode(id="End", agent_ref="agent-2"),
            ],
            edges=[{"source": "Start", "target": "End"}],
            entry_point="Start",
        ),
    )

    # Serialize
    json_data = recipe.model_dump(mode="json")

    # Deserialize
    new_recipe = RecipeDefinition.model_validate(json_data)

    assert new_recipe.compliance is not None
    assert new_recipe.compliance.integrity.integrity_level == IntegrityLevel.DIGITAL_SIGNATURE
    assert new_recipe.compliance.integrity.input_mode == AuditContentMode.REDACTED
