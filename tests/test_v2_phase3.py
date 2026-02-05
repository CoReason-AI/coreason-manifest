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

from coreason_manifest.spec.common_base import ToolRiskLevel
from coreason_manifest.spec.governance import GovernanceConfig
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    ToolDefinition,
    Workflow,
)
from coreason_manifest.utils.v2.governance import check_compliance_v2
from coreason_manifest.utils.v2.validator import validate_integrity


@pytest.fixture
def basic_manifest() -> ManifestV2:
    agent_def = AgentDefinition(id="my-agent", name="My Agent", role="Worker", goal="Work", type="agent")
    return ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test Agent"),
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(id="step1", agent="my-agent", next="step2"),
                "step2": AgentStep(id="step2", agent="my-agent"),
            },
        ),
        definitions={"my-agent": agent_def},
    )


def test_validation_loose_vs_strict() -> None:
    """Test that loose validation ignores dangling pointers while strict catches them."""
    # Now that ManifestV2 enforces strict validation via explicit call, construction should succeed.

    agent_def = AgentDefinition(id="my-agent", name="My Agent", role="Worker", goal="Work", type="agent")

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Broken Agent"),
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(id="step1", agent="my-agent", next="step2"),
            },
        ),
        definitions={"my-agent": agent_def},
    )

    with pytest.raises(ValueError, match="missing next step 'step2'"):
        validate_integrity(manifest)


def test_governance_tool_risk() -> None:
    """Test governance policy enforcement on tool risk levels."""
    # Create a manifest with a CRITICAL tool
    tool_def = ToolDefinition(
        id="critical-tool",
        name="Nuke",
        uri="https://api.nuke.com/v1",
        risk_level=ToolRiskLevel.CRITICAL,
        description="Dangerous tool",
    )

    agent_def = AgentDefinition(id="agent1", name="Agent 1", role="Worker", goal="Work", type="agent")

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Risky Agent"),
        workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")}),
        definitions={"critical-tool": tool_def, "agent1": agent_def},
    )

    # Config allowing only STANDARD
    config = GovernanceConfig(max_risk_level=ToolRiskLevel.STANDARD, require_auth_for_critical_tools=False)

    report = check_compliance_v2(manifest, config)
    assert not report.passed
    assert len(report.violations) == 1
    assert report.violations[0].rule == "risk_level_restriction"


def test_governance_allowed_domains() -> None:
    """Test governance policy on allowed domains."""
    tool_def = ToolDefinition(
        id="tool1",
        name="Search",
        uri="https://evil.com/api",
        risk_level=ToolRiskLevel.SAFE,
    )

    agent_def = AgentDefinition(id="agent1", name="Agent 1", role="Worker", goal="Work", type="agent")

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Domain Agent"),
        workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")}),
        definitions={"tool1": tool_def, "agent1": agent_def},
    )

    config = GovernanceConfig(allowed_domains=["good.com"])

    report = check_compliance_v2(manifest, config)
    assert not report.passed
    assert "domain_restriction" == report.violations[0].rule
