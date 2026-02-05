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
    LogicStep,
    Manifest,
    ToolDefinition,
    ToolRiskLevel,
    Workflow,
    check_compliance,
)


def test_complex_multiple_violations() -> None:
    """Test a scenario with multiple overlapping violations."""
    config = GovernanceConfig(
        allowed_domains=["good.com"],
        max_risk_level=ToolRiskLevel.SAFE,
        allow_custom_logic=False,
    )

    # 1. Logic Step Violation
    steps = {
        "s1": LogicStep(id="s1", code="import os"),
        "s2": AgentStep(id="s2", agent="agent1"),
    }

    # 2. Risk Level Violation (Critical Tool)
    # 3. Domain Violation (Bad Domain)
    # 4. Domain Violation (Another Bad Domain)
    definitions = {
        "risky_tool": ToolDefinition(
            id="risky_tool", name="Risky", uri="https://good.com/api", risk_level=ToolRiskLevel.CRITICAL
        ),
        "evil_tool": ToolDefinition(
            id="evil_tool", name="Evil", uri="https://evil.com/api", risk_level=ToolRiskLevel.SAFE
        ),
        "safe_tool": ToolDefinition(
            id="safe_tool", name="Safe", uri="https://api.good.com", risk_level=ToolRiskLevel.SAFE
        ),
    }

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Complex Agent"},
        definitions=definitions,
        workflow=Workflow(start="s1", steps=steps),
    )

    report = check_compliance(manifest, config)

    assert not report.compliant

    # Analyze violations
    violation_rules = [v.rule for v in report.violations]
    violation_ids = [v.component_id for v in report.violations]

    assert "no_custom_logic" in violation_rules
    assert "s1" in violation_ids

    assert "risk_level" in violation_rules
    assert "risky_tool" in violation_ids

    assert "domain_restriction" in violation_rules
    assert "evil_tool" in violation_ids

    # safe_tool should NOT be in violations
    assert "safe_tool" not in violation_ids

    # Verify count (1 logic + 1 risk + 1 domain = 3)
    # Note: risky_tool has valid domain, so only 1 violation.
    # evil_tool has valid risk, so only 1 violation.
    assert len(report.violations) == 3


def test_complex_mixed_risk_and_domain() -> None:
    """Test a single tool failing BOTH risk and domain checks."""
    config = GovernanceConfig(
        allowed_domains=["good.com"],
        max_risk_level=ToolRiskLevel.SAFE,
    )

    # Tool fails both
    definitions = {
        "double_bad": ToolDefinition(
            id="double_bad",
            name="Double Bad",
            uri="https://evil.com/api",
            risk_level=ToolRiskLevel.CRITICAL
        )
    }

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Double Bad Agent"},
        definitions=definitions,
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)
    assert not report.compliant

    # Should have 2 violations for the same component
    tool_violations = [v for v in report.violations if v.component_id == "double_bad"]
    assert len(tool_violations) == 2
    rules = {v.rule for v in tool_violations}
    assert "risk_level" in rules
    assert "domain_restriction" in rules
