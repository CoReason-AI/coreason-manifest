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
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
)


def test_complex_gxp_configuration() -> None:
    """Complex Case: GxP with strict integrity and audit levels."""
    integrity = IntegrityConfig(
        input_mode=AuditContentMode.FULL_PAYLOAD,
        output_mode=AuditContentMode.REFERENCE_ONLY,
        integrity_level=IntegrityLevel.BLOCKCHAIN_ANCHOR,
        hash_algorithm="sha512",  # Custom strong hash
    )
    compliance = ComplianceConfig(
        audit_level=AuditLevel.GXP_COMPLIANT, integrity=integrity, generate_aibom=True, require_signature=True
    )
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="GxP Recipe"),
        interface=RecipeInterface(),
        compliance=compliance,
        topology=GraphTopology(
            nodes=[AgentNode(id="A", agent_ref="ref-a")],
            edges=[],
            entry_point="A",
        ),
    )

    assert recipe.compliance is not None
    assert recipe.compliance.integrity.integrity_level == IntegrityLevel.BLOCKCHAIN_ANCHOR
    assert recipe.compliance.integrity.hash_algorithm == "sha512"
    assert recipe.compliance.audit_level == AuditLevel.GXP_COMPLIANT
    assert recipe.compliance.require_signature is True


def test_integrity_with_policy_limits() -> None:
    """Complex Case: Integrity combined with Policy constraints."""
    # Ensure no schema conflict between strict integrity and execution policy
    policy = PolicyConfig(max_retries=3, timeout_seconds=600, execution_mode="sequential", budget_cap_usd=50.0)
    integrity = IntegrityConfig(integrity_level=IntegrityLevel.DIGITAL_SIGNATURE)
    compliance = ComplianceConfig(integrity=integrity)

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Policy + Integrity"),
        interface=RecipeInterface(),
        policy=policy,
        compliance=compliance,
        topology=GraphTopology(
            nodes=[AgentNode(id="A", agent_ref="ref-a")],
            edges=[],
            entry_point="A",
        ),
    )

    assert recipe.policy is not None
    assert recipe.compliance is not None
    assert recipe.policy.budget_cap_usd == 50.0
    assert recipe.compliance.integrity.integrity_level == IntegrityLevel.DIGITAL_SIGNATURE


def test_nested_serialization_deserialization() -> None:
    """Complex Case: Deep nested structure roundtrip."""
    original_recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Deep Nesting"),
        interface=RecipeInterface(),
        compliance=ComplianceConfig(
            integrity=IntegrityConfig(input_mode=AuditContentMode.REDACTED, integrity_level=IntegrityLevel.CHECKSUM)
        ),
        topology=GraphTopology(
            nodes=[AgentNode(id="A", agent_ref="ref-a")],
            edges=[],
            entry_point="A",
        ),
    )

    json_str = original_recipe.model_dump_json()
    loaded_recipe = RecipeDefinition.model_validate_json(json_str)

    assert loaded_recipe.compliance is not None
    assert loaded_recipe.compliance.integrity.input_mode == AuditContentMode.REDACTED
    assert loaded_recipe.compliance.integrity.integrity_level == IntegrityLevel.CHECKSUM
    # Default
    assert loaded_recipe.compliance.integrity.output_mode == AuditContentMode.FULL_PAYLOAD
