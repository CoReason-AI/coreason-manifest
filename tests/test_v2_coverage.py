# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common_base import ToolRiskLevel
from coreason_manifest.spec.governance import GovernanceConfig
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    LogicStep,
    ManifestMetadata,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
    Workflow,
)
from coreason_manifest.utils.v2.governance import _risk_score, check_compliance_v2
from coreason_manifest.utils.v2.validator import validate_integrity, validate_loose

# --- Governance Tests ---


def test_risk_score_all_levels() -> None:
    """Test _risk_score with all known levels."""
    assert _risk_score(ToolRiskLevel.SAFE) == 0
    assert _risk_score(ToolRiskLevel.STANDARD) == 1
    assert _risk_score(ToolRiskLevel.CRITICAL) == 2

    # Unknown
    mock_level = MagicMock()
    mock_level.value = "unknown"
    assert _risk_score(mock_level) == 3


def test_governance_uri_no_hostname() -> None:
    """Test tool URI without hostname using model_construct to bypass Pydantic validation."""
    # Create invalid tool using model_construct
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="/local/path",  # type: ignore[arg-type] # Invalid for AnyUrl but injected here
        risk_level=ToolRiskLevel.SAFE,
    )

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={"s1": LogicStep(id="s1", code="pass")}),
        definitions={"t1": tool},
    )
    config = GovernanceConfig(allowed_domains=["example.com"])

    # This should now hit the "if not hostname:" block
    report = check_compliance_v2(manifest, config)
    assert not report.passed
    assert any("no hostname" in v.message for v in report.violations)


def test_governance_uri_trailing_dot() -> None:
    """Test tool URI with trailing dot in hostname."""
    # This targets line 90: if hostname.endswith("."): hostname = hostname[:-1]
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="https://example.com./api",  # type: ignore[arg-type]
        risk_level=ToolRiskLevel.SAFE,
    )
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={"s1": LogicStep(id="s1", code="pass")}),
        definitions={"t1": tool},
    )
    config = GovernanceConfig(allowed_domains=["example.com"], allow_custom_logic=True)

    # strict_url_validation=True by default.
    # hostname "example.com." should become "example.com" and pass.
    report = check_compliance_v2(manifest, config)
    assert report.passed


def test_governance_uri_parsing_error() -> None:
    """Test tool URI that causes parsing error."""
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="http://valid-but-will-be-mocked.com",  # type: ignore[arg-type]
        risk_level=ToolRiskLevel.SAFE,
    )
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={"s1": LogicStep(id="s1", code="pass")}),
        definitions={"t1": tool},
    )
    config = GovernanceConfig(allowed_domains=["example.com"])

    # Mock urlparse to raise exception
    with patch("coreason_manifest.utils.v2.governance.urlparse", side_effect=ValueError("Boom")):
        report = check_compliance_v2(manifest, config)

    assert not report.passed
    assert any("Failed to parse tool URI" in v.message for v in report.violations)


def test_governance_loose_url_validation() -> None:
    """Test governance with strict_url_validation=False."""
    tool = ToolDefinition.model_construct(
        id="t1",
        name="T",
        uri="https://EXAMPLE.COM/api",  # type: ignore[arg-type]
        risk_level=ToolRiskLevel.SAFE,
    )
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(start="s1", steps={"s1": LogicStep(id="s1", code="pass")}),
        definitions={"t1": tool},
    )

    # Case mismatch with strict=False (assuming library lowercases hostname anyway, this test might just pass through)
    # But we want to ensure the code path `else: allowed_set = set(...)` is hit.
    config = GovernanceConfig(allowed_domains=["example.com"], strict_url_validation=False, allow_custom_logic=True)
    report = check_compliance_v2(manifest, config)
    # If parsing normalizes EXAMPLE.COM -> example.com, and allowed is example.com, it passes.
    assert report.passed

    # To test failure in loose mode:
    # allowed="Other.com", uri="other.com". strict=False.
    # hostname="other.com". allowed_set={"Other.com"}.
    # "other.com" in {"Other.com"} -> False.
    config_fail = GovernanceConfig(
        allowed_domains=["Example.com"], strict_url_validation=False, allow_custom_logic=True
    )
    report_fail = check_compliance_v2(manifest, config_fail)
    assert not report_fail.passed


def test_governance_custom_logic_violations() -> None:
    """Test LogicStep and complex SwitchStep violations."""
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "s1": LogicStep(id="s1", code="print('bad')"),
                "s2": SwitchStep(id="s2", cases={"__import__('os')": "s1"}),
            },
        ),
    )
    config = GovernanceConfig(allow_custom_logic=False)
    report = check_compliance_v2(manifest, config)
    assert not report.passed
    rules = [v.rule for v in report.violations]
    assert rules.count("custom_logic_restriction") >= 2


# --- Validator Tests ---


def test_validator_loose_id_mismatch() -> None:
    """Test loose validation catches ID mismatch."""
    # Since ManifestV2 enforces strict integrity (agent ref), we need to bypass it or provide valid ref.
    # But validate_integrity does NOT check key/id mismatch.
    # However, validate_integrity checks if agent 'a' exists.

    agent_def = AgentDefinition(id="a", name="A", type="agent", role="R", goal="G")

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="key1",  # Point to the key
            steps={
                "key1": AgentStep(id="id1", agent="a")  # Mismatch
            },
        ),
        definitions={"a": agent_def},
    )
    warnings = validate_loose(manifest)
    assert any("does not match" in w for w in warnings)


def test_validator_loose_invalid_switch_condition() -> None:
    """Test loose validation catches empty switch condition."""
    # Need target 's2' to exist for strict validation
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        workflow=Workflow(
            start="s1",
            steps={
                "s1": SwitchStep(id="s1", cases={"": "s2"}),  # Empty condition
                "s2": LogicStep(id="s2", code="pass"),
            },
        ),
    )
    warnings = validate_loose(manifest)
    assert any("invalid condition" in w for w in warnings)


def test_validator_strict_missing_start() -> None:
    """Test strict validation missing start step."""
    agent_def = AgentDefinition(id="a", name="A", type="agent", role="R", goal="G")

    # Construct as draft first to bypass initial validation
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="Test"),
        status="published",
        workflow=Workflow(start="missing_start", steps={"s1": AgentStep(id="s1", agent="a")}),
        definitions={"a": agent_def},
    )

    # Now manually call validate_integrity or rely on Pydantic to catch it if instantiated with status=published
    # But wait, if I instantiate with status="published", it should raise ValidationError immediately!
    # The previous test used validate_integrity explicitly.
    # Now it's a model validator.
    # So constructing it should fail.

    with pytest.raises(ValidationError, match="Start step 'missing_start' not found"):
        ManifestV2(
            kind="Agent",
            metadata=ManifestMetadata(name="Test"),
            status="published",
            workflow=Workflow(start="missing_start", steps={"s1": AgentStep(id="s1", agent="a")}),
            definitions={"a": agent_def},
        )


def test_validator_strict_switch_broken_targets() -> None:
    """Test strict validation broken switch targets."""
    with pytest.raises(ValidationError, match="references missing step"):
        ManifestV2(
            kind="Agent",
            metadata=ManifestMetadata(name="Test"),
            status="published",
            workflow=Workflow(
                start="s1",
                steps={
                    "s1": SwitchStep(id="s1", cases={"cond": "missing_case_target"}, default="missing_default_target")
                },
            ),
        )


def test_validator_strict_missing_agent_definition() -> None:
    """Test strict validation missing agent definition."""
    with pytest.raises(ValidationError, match="references missing agent"):
        ManifestV2(
            kind="Agent",
            metadata=ManifestMetadata(name="Test"),
            status="published",
            workflow=Workflow(start="s1", steps={"s1": AgentStep(id="s1", agent="missing_agent")}),
            definitions={},
        )
