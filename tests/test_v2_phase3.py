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

from coreason_manifest.definitions.agent import ToolRequirement, ToolRiskLevel
from coreason_manifest.governance import GovernanceConfig
from coreason_manifest.v2.compiler import compile_dependencies, compile_to_topology
from coreason_manifest.v2.governance import check_compliance_v2
from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    ManifestMetadata,
    ManifestV2,
    ToolDefinition,
    Workflow,
)
from coreason_manifest.v2.validator import validate_loose, validate_strict


@pytest.fixture
def basic_manifest() -> ManifestV2:
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
        definitions={"my-agent": "some-definition"},  # Mock definition for strict check
    )


def test_validation_loose_vs_strict() -> None:
    """Test that loose validation ignores dangling pointers while strict catches them."""
    # Create a broken manifest (step1 points to missing step2)
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Broken Agent"),
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(id="step1", agent="my-agent", next="step2"),
            },
        ),
        definitions={"my-agent": "def"},
    )

    # Loose validation should be clean (or just warnings)
    warnings = validate_loose(manifest)
    # validate_loose checks strict structural things like ID match, not pointers.
    # So it should be empty here.
    assert len(warnings) == 0

    # Strict validation should fail
    errors = validate_strict(manifest)
    assert len(errors) > 0
    assert any("step2" in e for e in errors)


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

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Risky Agent"),
        workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")}),
        definitions={"critical-tool": tool_def, "agent1": "def"},
    )

    # Config allowing only STANDARD
    config = GovernanceConfig(max_risk_level=ToolRiskLevel.STANDARD)

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

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Domain Agent"),
        workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")}),
        definitions={"tool1": tool_def, "agent1": "def"},
    )

    config = GovernanceConfig(allowed_domains=["good.com"])

    report = check_compliance_v2(manifest, config)
    assert not report.passed
    assert "domain_restriction" == report.violations[0].rule


def test_compiler_dependencies() -> None:
    """Test extracting dependencies from V2 manifest."""
    tool_def = ToolDefinition(
        id="tool1",
        name="Calculator",
        uri="https://calc.com/api",
        risk_level=ToolRiskLevel.SAFE,
    )

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Calc Agent"),
        workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1")}),
        definitions={"tool1": tool_def, "agent1": "def"},
    )

    deps = compile_dependencies(manifest)
    assert len(deps.tools) == 1
    tool = deps.tools[0]

    # Assert type to satisfy Mypy that it's not InlineToolDefinition
    assert isinstance(tool, ToolRequirement)

    assert str(tool.uri) == "https://calc.com/api"
    assert tool.risk_level == ToolRiskLevel.SAFE
    assert tool.hash == "0" * 64
    assert tool.scopes == []


def test_compiler_strict_validation_integration() -> None:
    """Test that compile_to_topology calls strict validation."""
    # Broken manifest
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Broken Agent"),
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(id="step1", agent="my-agent", next="missing_step"),
            },
        ),
        definitions={"my-agent": "def"},
    )

    with pytest.raises(ValueError, match="Manifest validation failed"):
        compile_to_topology(manifest)
