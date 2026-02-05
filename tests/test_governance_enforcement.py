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


def test_block_custom_logic() -> None:
    """Test that LogicStep is blocked when allow_custom_logic is False."""
    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Logic Agent"},
        workflow=Workflow(
            start="logic1",
            steps={"logic1": LogicStep(id="logic1", code="print('hello')")},
        ),
    )

    config = GovernanceConfig(allow_custom_logic=False)
    report = check_compliance(manifest, config)

    assert report.compliant is False
    assert len(report.violations) == 1
    violation = report.violations[0]
    assert violation.rule == "no_custom_logic"
    assert violation.component_id == "logic1"


def test_domain_whitelist_strict() -> None:
    """Test strict domain validation."""
    config = GovernanceConfig(
        allowed_domains=["good.com"],
        strict_url_validation=True,
    )

    # Tool A: good.com (Should Pass)
    tool_a = ToolDefinition(
        id="tool_a",
        name="Tool A",
        uri="https://api.good.com",
        risk_level=ToolRiskLevel.SAFE,
    )
    # Tool B: evil.com (Should Fail)
    tool_b = ToolDefinition(
        id="tool_b",
        name="Tool B",
        uri="https://evil.com/api",
        risk_level=ToolRiskLevel.SAFE,
    )
    # Tool C: good.com. (Trailing dot - Should Pass if normalized)
    tool_c = ToolDefinition(
        id="tool_c",
        name="Tool C",
        uri="https://good.com.",
        risk_level=ToolRiskLevel.SAFE,
    )

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Domain Agent"},
        definitions={
            "tool_a": tool_a,
            "tool_b": tool_b,
            "tool_c": tool_c,
        },
        workflow=Workflow(
            start="step1",
            steps={"step1": AgentStep(id="step1", agent="some_agent")},
        ),
    )

    report = check_compliance(manifest, config)

    assert report.compliant is False
    # Expect 1 violation for tool_b
    assert len(report.violations) == 1
    violation = report.violations[0]
    assert violation.component_id == "tool_b"
    assert violation.rule == "domain_restriction"


def test_risk_level_hierarchy() -> None:
    """Test risk level enforcement."""
    config = GovernanceConfig(max_risk_level=ToolRiskLevel.SAFE)

    # Tool with CRITICAL risk -> Violation
    critical_tool = ToolDefinition(
        id="critical",
        name="Critical Tool",
        uri="https://safe.com",  # Assume domain is safe or ignored for this test? No, domain check runs too.
        # If allowed_domains is empty list (default), domain check is skipped?
        # GovernanceConfig default: allowed_domains=[] (empty list).
        # My implementation: if config.allowed_domains: ...
        # So empty list means NO domain restriction.
        risk_level=ToolRiskLevel.CRITICAL,
    )

    # Tool with SAFE risk -> Pass
    safe_tool = ToolDefinition(
        id="safe",
        name="Safe Tool",
        uri="https://safe.com",
        risk_level=ToolRiskLevel.SAFE,
    )

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Risk Agent"},
        definitions={
            "critical": critical_tool,
            "safe": safe_tool,
        },
        workflow=Workflow(
            start="step1",
            steps={"step1": AgentStep(id="step1", agent="some_agent")},
        ),
    )

    report = check_compliance(manifest, config)

    assert report.compliant is False
    assert len(report.violations) == 1
    violation = report.violations[0]
    assert violation.component_id == "critical"
    assert violation.rule == "risk_level"


def test_clean_report() -> None:
    """Test a fully compliant agent."""
    config = GovernanceConfig(
        allowed_domains=["good.com"],
        max_risk_level=ToolRiskLevel.STANDARD,
        allow_custom_logic=False,
    )

    tool = ToolDefinition(
        id="tool1",
        name="Good Tool",
        uri="https://api.good.com",
        risk_level=ToolRiskLevel.SAFE,
    )

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Clean Agent"},
        definitions={"tool1": tool},
        workflow=Workflow(
            start="step1",
            steps={"step1": AgentStep(id="step1", agent="some_agent")},
        ),
    )

    report = check_compliance(manifest, config)

    assert report.compliant is True
    assert len(report.violations) == 0
    assert report.checked_at is not None
