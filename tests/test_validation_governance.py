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

from coreason_manifest import (
    AgentStep,
    GovernanceConfig,
    LogicStep,
    Manifest,
    ToolDefinition,
    ToolRiskLevel,
    Workflow,
    check_compliance_v2,
    validate_integrity,
    validate_loose,
)


def test_draft_mode_loose() -> None:
    """Test that we can create a broken manifest and get warnings."""
    # Create manifest with broken references (missing start step)
    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Broken Agent"},
        workflow=Workflow(
            start="step1",
            steps={},  # Missing step1
        ),
    )

    # Assert instantiation succeeded (no crash)
    assert manifest.metadata.name == "Broken Agent"

    # Assert validate_loose returns warnings
    warnings = validate_loose(manifest)
    assert len(warnings) > 0
    assert any("Start step 'step1' not found" in w for w in warnings)


def test_compiler_mode_strict() -> None:
    """Test that strict validation raises ValueError."""
    manifest = Manifest(kind="Agent", metadata={"name": "Broken Agent"}, workflow=Workflow(start="step1", steps={}))

    with pytest.raises(ValueError, match="Start step 'step1' not found"):
        validate_integrity(manifest)


def test_governance_risk() -> None:
    """Test governance policy enforcement on tool risk levels."""
    tool = ToolDefinition(id="nuke", name="Nuke", uri="https://nuke.com", risk_level=ToolRiskLevel.CRITICAL)
    # We create a manifest. It can be referentially broken (no agent def),
    # governance check should still work on tools present.
    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Risky Agent"},
        definitions={"nuke": tool},
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )

    config = GovernanceConfig(max_risk_level=ToolRiskLevel.STANDARD, require_auth_for_critical_tools=False)
    report = check_compliance_v2(manifest, config)

    assert report.compliant is False
    assert len(report.violations) == 1
    assert "risk level 'critical' exceeds" in report.violations[0].message


def test_governance_logic_block() -> None:
    """Test governance policy enforcement on custom logic."""
    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Logic Agent"},
        workflow=Workflow(start="logic1", steps={"logic1": LogicStep(id="logic1", code="print('hello')")}),
    )

    config = GovernanceConfig(allow_custom_logic=False)
    report = check_compliance_v2(manifest, config)

    assert report.compliant is False
    assert any("is a LogicStep, which is not allowed" in v.message for v in report.violations)
