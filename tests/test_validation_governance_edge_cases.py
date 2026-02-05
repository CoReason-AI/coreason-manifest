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
    Manifest,
    ManifestMetadata,
    ToolDefinition,
    ToolRiskLevel,
    Workflow,
    check_compliance_v2,
)


@pytest.fixture
def base_workflow() -> Workflow:
    return Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")})


def test_auth_mandate_explicit_false(base_workflow: Workflow) -> None:
    """Case 1: Manifest with CRITICAL tool but requires_auth=False explicitly."""
    tool = ToolDefinition(id="nuke", name="Nuke", uri="https://nuke.com", risk_level=ToolRiskLevel.CRITICAL)
    config = GovernanceConfig(require_auth_for_critical_tools=True)

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Explicit Insecure", requires_auth=False),
        definitions={"nuke": tool},
        workflow=base_workflow,
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].rule == "auth_mandate_missing"


def test_auth_mandate_none_default(base_workflow: Workflow) -> None:
    """Case 2: Manifest with CRITICAL tool and requires_auth=None (default)."""
    tool = ToolDefinition(id="nuke", name="Nuke", uri="https://nuke.com", risk_level=ToolRiskLevel.CRITICAL)
    config = GovernanceConfig(require_auth_for_critical_tools=True)

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Default Insecure"),
        definitions={"nuke": tool},
        workflow=base_workflow,
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].rule == "auth_mandate_missing"


def test_auth_mandate_mixed_tools(base_workflow: Workflow) -> None:
    """Case 3: Manifest with multiple tools, mixed risk levels.
    Ensures presence of ONE critical tool triggers the mandate.
    """
    tools = {
        "safe_tool": ToolDefinition(id="safe", name="Safe", uri="https://safe.com", risk_level=ToolRiskLevel.SAFE),
        "std_tool": ToolDefinition(id="std", name="Std", uri="https://std.com", risk_level=ToolRiskLevel.STANDARD),
        "crit_tool": ToolDefinition(id="crit", name="Crit", uri="https://crit.com", risk_level=ToolRiskLevel.CRITICAL),
    }
    config = GovernanceConfig(require_auth_for_critical_tools=True)

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Mixed Risk Agent"),
        definitions=tools,
        workflow=base_workflow,
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].rule == "auth_mandate_missing"


def test_auth_mandate_config_disabled(base_workflow: Workflow) -> None:
    """Case 4: GovernanceConfig with require_auth_for_critical_tools=False.
    Manifest has critical tools but no auth. Should PASS.
    """
    tool = ToolDefinition(id="nuke", name="Nuke", uri="https://nuke.com", risk_level=ToolRiskLevel.CRITICAL)
    config = GovernanceConfig(require_auth_for_critical_tools=False)

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Config Disabled Agent"),
        definitions={"nuke": tool},
        workflow=base_workflow,
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is True
    assert len(report.violations) == 0


def test_auth_mandate_dynamic_extra_field(base_workflow: Workflow) -> None:
    """Case 5: Manifest with requires_auth set via model_extra.
    (Simulating loading from YAML where field isn't in schema but allowed).
    """
    tool = ToolDefinition(id="nuke", name="Nuke", uri="https://nuke.com", risk_level=ToolRiskLevel.CRITICAL)
    config = GovernanceConfig(require_auth_for_critical_tools=True)

    # Creating metadata with extra field directly via constructor if allowed,
    # or by forcing it into model_extra.
    # ManifestMetadata has extra='allow'.
    metadata = ManifestMetadata(name="Dynamic Secure", requires_auth=True)

    manifest = Manifest(
        kind="Agent",
        metadata=metadata,
        definitions={"nuke": tool},
        workflow=base_workflow,
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is True
