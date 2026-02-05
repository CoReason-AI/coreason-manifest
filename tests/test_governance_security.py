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
    ToolDefinition,
    ToolRiskLevel,
    Workflow,
    check_compliance,
)


def test_security_subdomain_hijack_attempt() -> None:
    """Test subdomain bypass attempts (e.g. evilgood.com)."""
    config = GovernanceConfig(allowed_domains=["good.com"])

    # "evilgood.com" ends with "good.com" but is NOT a subdomain.
    tool = ToolDefinition(id="t1", name="T", uri="https://evilgood.com/api", risk_level=ToolRiskLevel.SAFE)

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Test"},
        definitions={"t1": tool},
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)
    assert not report.compliant
    assert report.violations[0].rule == "domain_restriction"


def test_security_user_info_bypass() -> None:
    """Test authority confusion using user info (e.g. good.com@evil.com)."""
    config = GovernanceConfig(allowed_domains=["good.com"])

    # URL: https://good.com@evil.com/api
    # Browser treats 'evil.com' as host, 'good.com' as user.
    # python urlparse should correctly identify hostname as 'evil.com'.

    tool = ToolDefinition(id="t1", name="T", uri="https://good.com@evil.com/api", risk_level=ToolRiskLevel.SAFE)

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Test"},
        definitions={"t1": tool},
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)
    assert not report.compliant
    assert "evil.com" in report.violations[0].message


def test_security_dot_boundary_confusion() -> None:
    """Test dot boundary confusion (e.g. .com vs com)."""
    # If allowed is "com", does "evil.com" pass? (Technically yes if we allow TLDs)
    # But if allowed is "co.uk", does "evil.co.uk" pass? Yes.
    # Does "evilco.uk" pass? No.

    config = GovernanceConfig(allowed_domains=["co.uk"])

    tool_good = ToolDefinition(id="t1", name="T", uri="https://google.co.uk", risk_level=ToolRiskLevel.SAFE)
    tool_bad = ToolDefinition(id="t2", name="T", uri="https://evilco.uk", risk_level=ToolRiskLevel.SAFE)

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Test"},
        definitions={"t1": tool_good, "t2": tool_bad},
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)
    assert not report.compliant

    violation_ids = [v.component_id for v in report.violations]
    assert "t1" not in violation_ids
    assert "t2" in violation_ids


def test_security_normalization_bypass() -> None:
    """Test bypass via case and trailing dots variations."""
    config = GovernanceConfig(allowed_domains=["good.com"])

    uris = [
        "https://GOOD.COM",  # Case
        "https://good.com.",  # Trailing dot
        "https://GOOD.COM.",  # Both
        "https://api.good.com.",  # Subdomain + Trailing dot
    ]

    defs = {
        f"t{i}": ToolDefinition(id=f"t{i}", name=f"T{i}", uri=u, risk_level=ToolRiskLevel.SAFE)
        for i, u in enumerate(uris)
    }

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Test"},
        definitions=defs,
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)
    assert report.compliant  # All should pass due to normalization


def test_security_multiple_trailing_dots() -> None:
    """Test handling of multiple trailing dots (e.g. good.com..)."""
    # RFCs generally say only one trailing dot is root. Two might be invalid or handled differently.
    # Python urlparse behavior: 'good.com..' -> hostname='good.com..'
    # Our normalization strips ONE dot. 'good.com.' remains.
    # 'good.com.' != 'good.com'.
    # So this SHOULD fail if strict.

    config = GovernanceConfig(allowed_domains=["good.com"])

    tool = ToolDefinition(id="t1", name="T", uri="https://good.com..", risk_level=ToolRiskLevel.SAFE)

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Test"},
        definitions={"t1": tool},
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)

    # Expect failure because we only strip one dot.
    assert not report.compliant


def test_security_punycode() -> None:
    """Test punycode handling (e.g. xn--... vs unicode)."""
    # If policy allows 'xn--fake-123.com', does 'fake.com' pass? No.
    # Does 'xn--fake-123.com' (in unicode) pass?
    # We rely on urlparse. urlparse usually keeps unicode as is or converts?
    # Python 3 urlparse keeps unicode.

    # Allowed: münchen.de (unicode)
    config = GovernanceConfig(allowed_domains=["münchen.de"])

    # Tool: xn--mnchen-3ya.de (punycode for münchen.de)
    tool_puny = ToolDefinition(id="t1", name="T", uri="https://xn--mnchen-3ya.de", risk_level=ToolRiskLevel.SAFE)
    # Tool: münchen.de (unicode)
    tool_uni = ToolDefinition(id="t2", name="T", uri="https://münchen.de", risk_level=ToolRiskLevel.SAFE)

    manifest = Manifest(
        kind="Agent",
        metadata={"name": "Test"},
        definitions={"t1": tool_puny, "t2": tool_uni},
        workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="a")}),
    )

    report = check_compliance(manifest, config)

    # Implementation now normalizes to IDNA (punycode).
    # Both should pass.
    # t1: xn--... matches normalized xn--...
    # t2: münchen.de (Pydantic converts to xn--...) matches normalized xn--...

    assert report.compliant
    assert len(report.violations) == 0
