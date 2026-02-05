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
    ManifestMetadata,
    SwitchStep,
    ToolDefinition,
    ToolRiskLevel,
    Workflow,
    check_compliance_v2,
)


def test_governance_auth_edge_cases() -> None:
    """Test edge cases for authentication mandate."""
    tool = ToolDefinition(id="crit", name="Crit", uri="https://crit.com", risk_level=ToolRiskLevel.CRITICAL)
    config = GovernanceConfig(require_auth_for_critical_tools=True)

    # 1. requires_auth explicitly False
    manifest_false = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="FalseAuth", requires_auth=False),
        definitions={"crit": tool},
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )
    report = check_compliance_v2(manifest_false, config)
    assert report.passed is False
    assert report.violations[0].rule == "auth_mandate_missing"

    # 2. requires_auth via model_extra (valid)
    # We construct metadata manually to inject extra fields if needed,
    # but ManifestMetadata has extra="allow", so we can pass it in constructor if defined that way.
    # However, ManifestMetadata definition in provided context showed:
    # class ManifestMetadata(CoReasonBaseModel):
    #     model_config = ConfigDict(extra="allow", ...)
    #     name: str

    # Passing arbitrary kwarg to constructor:
    meta_extra = ManifestMetadata(name="ExtraAuth", requires_auth=True)
    # Wait, if `requires_auth` is NOT in the schema (it wasn't in the definitions file I read earlier,
    # only `name` and `design_metadata`), then passing it to constructor puts it in extra.

    manifest_extra = Manifest(
        kind="Agent",
        metadata=meta_extra,
        definitions={"crit": tool},
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )

    report_extra = check_compliance_v2(manifest_extra, config)
    assert report_extra.passed is True


def test_governance_domain_normalization_edge_cases() -> None:
    """Test strict vs loose domain validation."""
    # Tool has trailing dot (FQDN style)
    tool = ToolDefinition(id="t1", name="T1", uri="https://example.com./api", risk_level=ToolRiskLevel.SAFE)

    # 1. Strict Validation: Should normalize 'example.com.' -> 'example.com' and match
    config_strict = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=True)
    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        definitions={"t1": tool},
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )
    report_strict = check_compliance_v2(manifest, config_strict)
    assert report_strict.passed is True

    # 2. Loose Validation: 'example.com.' != 'example.com'
    config_loose = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=False)
    report_loose = check_compliance_v2(manifest, config_loose)
    assert report_loose.passed is False
    assert report_loose.violations[0].rule == "domain_restriction"

    # 3. Case Insensitivity in Loose Mode
    # urlparse lowercases hostname, so 'HTTPS://EXAMPLE.COM' -> 'example.com'
    # If allowed_domains has 'Example.com', loose mode set check is {'Example.com'}.
    # 'example.com' in {'Example.com'} -> False.
    tool_upper = ToolDefinition(id="t2", name="T2", uri="https://EXAMPLE.COM/api", risk_level=ToolRiskLevel.SAFE)
    config_loose_case = GovernanceConfig(allowed_domains=["Example.com"], strict_url_validation=False)

    manifest_upper = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="TestUpper"),
        definitions={"t2": tool_upper},
        workflow=Workflow(start="A", steps={"A": AgentStep(id="A", agent="bond")}),
    )
    report_loose_case = check_compliance_v2(manifest_upper, config_loose_case)
    # This is arguably a "gotcha" of loose validation, but asserting current behavior
    assert report_loose_case.passed is False

    # 4. Strict Validation handles case
    config_strict_case = GovernanceConfig(allowed_domains=["Example.com"], strict_url_validation=True)
    report_strict_case = check_compliance_v2(manifest_upper, config_strict_case)
    assert report_strict_case.passed is True


def test_governance_custom_logic_complex() -> None:
    """Test complex custom logic detection in SwitchSteps."""
    config = GovernanceConfig(allow_custom_logic=False)

    # Case 1: Import in switch case
    step_import = SwitchStep(id="s1", cases={"import os; os.system('ls')": "step2"}, default="step3")
    manifest_import = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="BadSwitch"),
        workflow=Workflow(start="s1", steps={"s1": step_import}),
    )
    report = check_compliance_v2(manifest_import, config)
    assert report.passed is False
    assert any("import " in v.message for v in report.violations)

    # Case 2: Dunder in switch case
    step_dunder = SwitchStep(id="s2", cases={"val.__class__": "step2"}, default="step3")
    manifest_dunder = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="BadSwitch2"),
        workflow=Workflow(start="s2", steps={"s2": step_dunder}),
    )
    report_dunder = check_compliance_v2(manifest_dunder, config)
    assert report_dunder.passed is False
    assert any("contains complex condition" in v.message for v in report_dunder.violations)


def test_governance_mixed_complex_scenario() -> None:
    """
    Complex scenario:
    - Critical Tool (Auth OK)
    - Safe Tool (Domain OK)
    - LogicStep (Blocked)
    """
    crit_tool = ToolDefinition(id="crit", name="Crit", uri="https://crit.com", risk_level=ToolRiskLevel.CRITICAL)
    safe_tool = ToolDefinition(id="safe", name="Safe", uri="https://safe.com", risk_level=ToolRiskLevel.SAFE)

    logic_step = LogicStep(id="logic", code="x = 1")
    agent_step = AgentStep(id="agent", agent="bond")

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Mixed", requires_auth=True),
        definitions={"crit": crit_tool, "safe": safe_tool},
        workflow=Workflow(start="logic", steps={"logic": logic_step, "agent": agent_step}),
    )

    config = GovernanceConfig(
        require_auth_for_critical_tools=True, allowed_domains=["crit.com", "safe.com"], allow_custom_logic=False
    )

    report = check_compliance_v2(manifest, config)

    # Should fail ONLY due to logic step
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].rule == "custom_logic_restriction"
    assert report.violations[0].component_id == "logic"
