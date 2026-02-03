# Copyright (c) 2025 CoReason, Inc.

import pytest
from unittest.mock import MagicMock, patch

from coreason_manifest.definitions.agent import ToolRiskLevel
from coreason_manifest.governance import GovernanceConfig
from coreason_manifest.v2.governance import check_compliance_v2, _risk_score
from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    LogicStep,
    ManifestMetadata,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
    Workflow,
)
from coreason_manifest.v2.validator import validate_loose, validate_strict


# --- Governance Tests ---

def test_risk_score_all_levels():
    """Test _risk_score with all known levels."""
    assert _risk_score(ToolRiskLevel.SAFE) == 0
    assert _risk_score(ToolRiskLevel.STANDARD) == 1
    assert _risk_score(ToolRiskLevel.CRITICAL) == 2

    # Unknown
    mock_level = MagicMock()
    mock_level.value = "unknown"
    assert _risk_score(mock_level) == 3


def test_governance_uri_no_hostname():
    """Test tool URI without hostname using model_construct to bypass Pydantic validation."""
    # Create invalid tool using model_construct
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="/local/path", # Invalid for AnyUrl but injected here
        risk_level=ToolRiskLevel.SAFE
    )

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={}),
        definitions={"t1": tool}
    )
    config = GovernanceConfig(allowed_domains=["example.com"])

    # This should now hit the "if not hostname:" block
    report = check_compliance_v2(manifest, config)
    assert not report.passed
    assert any("no hostname" in v.message for v in report.violations)


def test_governance_uri_trailing_dot():
    """Test tool URI with trailing dot in hostname."""
    # This targets line 90: if hostname.endswith("."): hostname = hostname[:-1]
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="https://example.com./api",
        risk_level=ToolRiskLevel.SAFE
    )
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={}),
        definitions={"t1": tool}
    )
    config = GovernanceConfig(allowed_domains=["example.com"])

    # strict_url_validation=True by default.
    # hostname "example.com." should become "example.com" and pass.
    report = check_compliance_v2(manifest, config)
    assert report.passed


def test_governance_uri_parsing_error():
    """Test tool URI that causes parsing error."""
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="http://valid-but-will-be-mocked.com",
        risk_level=ToolRiskLevel.SAFE
    )
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={}),
        definitions={"t1": tool}
    )
    config = GovernanceConfig(allowed_domains=["example.com"])

    # Mock urlparse to raise exception
    with patch("coreason_manifest.v2.governance.urlparse", side_effect=ValueError("Boom")):
        report = check_compliance_v2(manifest, config)

    assert not report.passed
    assert any("Failed to parse tool URI" in v.message for v in report.violations)


def test_governance_loose_url_validation():
    """Test governance with strict_url_validation=False."""
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="https://EXAMPLE.COM/api",
        risk_level=ToolRiskLevel.SAFE
    )
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={}),
        definitions={"t1": tool}
    )

    # Case mismatch with strict=False (assuming library lowercases hostname anyway, this test might just pass through)
    # But we want to ensure the code path `else: allowed_set = set(...)` is hit.
    config = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=False)
    report = check_compliance_v2(manifest, config)
    # If parsing normalizes EXAMPLE.COM -> example.com, and allowed is example.com, it passes.
    assert report.passed

    # To test failure in loose mode:
    # allowed="Other.com", uri="other.com". strict=False.
    # hostname="other.com". allowed_set={"Other.com"}.
    # "other.com" in {"Other.com"} -> False.
    config_fail = GovernanceConfig(allowed_domains=["Example.com"], strict_url_validation=False)
    report_fail = check_compliance_v2(manifest, config_fail)
    assert not report_fail.passed


def test_governance_custom_logic_violations():
    """Test LogicStep and complex SwitchStep violations."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "s1": LogicStep(id="s1", code="print('bad')"),
                "s2": SwitchStep(id="s2", cases={"__import__('os')": "s1"}),
            }
        ),
    )
    config = GovernanceConfig(allow_custom_logic=False)
    report = check_compliance_v2(manifest, config)
    assert not report.passed
    rules = [v.rule for v in report.violations]
    assert rules.count("custom_logic_restriction") >= 2


# --- Validator Tests ---

def test_validator_loose_id_mismatch():
    """Test loose validation catches ID mismatch."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "key1": AgentStep(id="id1", agent="a") # Mismatch
            }
        )
    )
    warnings = validate_loose(manifest)
    assert any("does not match" in w for w in warnings)


def test_validator_loose_invalid_switch_condition():
    """Test loose validation catches empty switch condition."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "s1": SwitchStep(id="s1", cases={"": "s2"}) # Empty condition
            }
        )
    )
    warnings = validate_loose(manifest)
    assert any("invalid condition" in w for w in warnings)


def test_validator_strict_missing_start():
    """Test strict validation missing start step."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="missing_start",
            steps={"s1": AgentStep(id="s1", agent="a")}
        ),
        definitions={"a": {}}
    )
    errors = validate_strict(manifest)
    assert any("start step 'missing_start' not found" in e for e in errors)


def test_validator_strict_switch_broken_targets():
    """Test strict validation broken switch targets."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "s1": SwitchStep(
                    id="s1",
                    cases={"cond": "missing_case_target"},
                    default="missing_default_target"
                )
            }
        )
    )
    errors = validate_strict(manifest)
    assert any("case 'cond' points to non-existent" in e for e in errors)
    assert any("default points to non-existent" in e for e in errors)


def test_validator_strict_missing_agent_definition():
    """Test strict validation missing agent definition."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "s1": AgentStep(id="s1", agent="missing_agent")
            }
        ),
        definitions={}
    )
    errors = validate_strict(manifest)
    assert any("Agent 'missing_agent' referenced in step 's1' not found" in e for e in errors)
