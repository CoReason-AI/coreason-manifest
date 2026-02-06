# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest import (
    AgentStep,
    GovernanceConfig,
    Manifest,
    ManifestMetadata,
    ToolDefinition,
    ToolRiskLevel,
    Workflow,
)
from coreason_manifest.utils.v2.governance import check_compliance_v2


def test_complex_large_manifest_many_tools() -> None:
    """Case 7: Large manifest with many tools (stress test logic)."""
    tools = {}
    # Generate 50 safe tools
    for i in range(50):
        tools[f"safe_{i}"] = ToolDefinition(
            id=f"safe_{i}", name=f"Safe {i}", uri=f"https://safe{i}.com", risk_level=ToolRiskLevel.SAFE
        )

    # Generate 1 critical tool hidden in the middle
    tools["hidden_critical"] = ToolDefinition(
        id="hidden_critical", name="Critical", uri="https://crit.com", risk_level=ToolRiskLevel.CRITICAL
    )

    # Generate 49 more standard tools
    for i in range(49):
        tools[f"std_{i}"] = ToolDefinition(
            id=f"std_{i}", name=f"Std {i}", uri=f"https://std{i}.com", risk_level=ToolRiskLevel.STANDARD
        )

    config = GovernanceConfig(require_auth_for_critical_tools=True)
    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Large Manifest"),
        definitions=tools,
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].rule == "auth_mandate_missing"


def test_complex_compliant_large_manifest() -> None:
    """Case 8: Large compliant manifest."""
    tools = {}
    tools["hidden_critical"] = ToolDefinition(
        id="hidden_critical", name="Critical", uri="https://crit.com", risk_level=ToolRiskLevel.CRITICAL
    )

    config = GovernanceConfig(require_auth_for_critical_tools=True)
    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Large Compliant", requires_auth=True),
        definitions=tools,
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )

    report = check_compliance_v2(manifest, config)
    assert report.passed is True
