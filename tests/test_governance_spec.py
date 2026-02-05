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
from pydantic import ValidationError

from coreason_manifest import (
    ComplianceReport,
    ComplianceViolation,
    GovernanceConfig,
    ToolRiskLevel,
)


def test_governance_config_serialization() -> None:
    """Test that GovernanceConfig serializes correctly."""
    config = GovernanceConfig(
        allowed_domains=["example.com"],
        max_risk_level=ToolRiskLevel.STANDARD,
    )

    data = config.dump()
    assert data["allowed_domains"] == ["example.com"]
    assert data["max_risk_level"] == "standard"
    assert data["allow_custom_logic"] is False  # Default

    # Check JSON string serialization
    json_str = config.to_json()
    assert '"max_risk_level":"standard"' in json_str


def test_compliance_report_serialization() -> None:
    """Test that ComplianceReport and ComplianceViolation serialize correctly."""
    violation = ComplianceViolation(
        rule="no_critical_tools", message="Critical tools are forbidden.", component_id="tool-1", severity="error"
    )

    report = ComplianceReport(compliant=False, violations=[violation])

    data = report.dump()
    assert data["compliant"] is False
    assert len(data["violations"]) == 1
    v_data = data["violations"][0]
    assert v_data["rule"] == "no_critical_tools"
    assert v_data["severity"] == "error"


def test_governance_config_strictness() -> None:
    """Test that GovernanceConfig forbids extra fields."""
    with pytest.raises(ValidationError) as exc:
        GovernanceConfig(extra_field="invalid")  # type: ignore[call-arg]

    assert "Extra inputs are not permitted" in str(exc.value)


def test_compliance_violation_strictness() -> None:
    """Test that ComplianceViolation forbids extra fields."""
    with pytest.raises(ValidationError) as exc:
        ComplianceViolation(
            rule="rule",
            message="msg",
            invalid_field="x",  # type: ignore[call-arg]
        )
    assert "Extra inputs are not permitted" in str(exc.value)
