# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Governance and Policy Enforcement module for Coreason Agents.

This module provides tools to validate an AgentDefinition against a set of organizational rules.
"""

from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel, ToolRiskLevel
from coreason_manifest.v2.spec.definitions import (
    LogicStep,
    ManifestV2,
    ToolDefinition,
)


class GovernanceConfig(CoReasonBaseModel):
    """Configuration for governance rules.

    Attributes:
        allowed_domains: List of allowed domains for tool URIs.
        allow_custom_logic: Whether to allow LogicNodes and conditional Edges with custom code.
        max_risk_level: Maximum allowed risk level for tools.
        strict_url_validation: Enforce strict, normalized URL validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed_domains: List[str] = Field(
        default_factory=list, description="If provided, all Tool URIs must match one of these domains."
    )
    allow_custom_logic: bool = Field(
        False, description="Whether to allow LogicNodes and conditional Edges with custom code."
    )
    max_risk_level: ToolRiskLevel = Field(
        ToolRiskLevel.SAFE, description="If provided, no tool can exceed this risk level."
    )
    strict_url_validation: bool = Field(True, description="Enforce strict, normalized URL validation.")


class ComplianceViolation(CoReasonBaseModel):
    """Details of a compliance violation.

    Attributes:
        rule: Name of the rule broken.
        message: Human readable details.
        component_id: Name of the tool or component causing the issue.
        severity: Severity level (e.g., 'error', 'warning').
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule: str = Field(..., description="Name of the rule broken, e.g., 'domain_restriction'.")
    message: str = Field(..., description="Human readable details.")
    component_id: Optional[str] = Field(None, description="Name of the tool or component causing the issue.")
    severity: str = Field("error", description="Severity level (e.g., 'error', 'warning').")


class ComplianceReport(CoReasonBaseModel):
    """Report of compliance checks.

    Attributes:
        compliant: Whether the agent passed all checks.
        violations: List of violations found.
        checked_at: Timestamp of the check.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    compliant: bool = Field(..., description="Whether the agent passed all checks.")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="List of violations found.")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the check."
    )


def _risk_score(level: ToolRiskLevel) -> int:
    """Convert risk level to integer score for comparison."""
    if level == ToolRiskLevel.SAFE:
        return 0
    if level == ToolRiskLevel.STANDARD:
        return 1
    if level == ToolRiskLevel.CRITICAL:
        return 2
    return 3  # Unknown is highest risk


def check_compliance(agent: ManifestV2, config: GovernanceConfig) -> ComplianceReport:
    """Check if the agent complies with the governance policy.

    Args:
        agent: The Agent Manifest (V2) to check.
        config: The Governance Configuration.

    Returns:
        A ComplianceReport indicating compliance status and listing violations.
    """
    violations: List[ComplianceViolation] = []

    # 1. Logic Check: Iterate agent.workflow.steps
    if not config.allow_custom_logic:
        for step_id, step in agent.workflow.steps.items():
            if isinstance(step, LogicStep):
                violations.append(
                    ComplianceViolation(
                        rule="no_custom_logic",
                        message=f"Step '{step_id}' is a LogicStep, which is not allowed by policy.",
                        component_id=step_id,
                    )
                )

    # 2. Tool Checks: Iterate agent.definitions
    # Note: 'agent.dependencies' in requirements maps to tools in 'agent.definitions'
    max_risk_score = _risk_score(config.max_risk_level)

    allowed_set = set()
    if config.allowed_domains:
        if config.strict_url_validation:
            allowed_set = {d.lower() for d in config.allowed_domains}
        else:
            allowed_set = set(config.allowed_domains)

    for _, definition in agent.definitions.items():
        if isinstance(definition, ToolDefinition):
            # Risk Level Check
            tool_risk_score = _risk_score(definition.risk_level)

            if tool_risk_score > max_risk_score:
                violations.append(
                    ComplianceViolation(
                        rule="risk_level",
                        message=(
                            f"Tool '{definition.name}' risk level '{definition.risk_level.value}' "
                            f"exceeds allowed maximum '{config.max_risk_level.value}'."
                        ),
                        component_id=definition.id,
                        severity="error",
                    )
                )

            # Domain Check
            if config.allowed_domains:
                try:
                    parsed_uri = urlparse(str(definition.uri))
                    hostname = parsed_uri.hostname

                    if not hostname:
                        violations.append(
                            ComplianceViolation(
                                rule="domain_restriction",
                                message=f"Tool '{definition.name}' URI '{definition.uri}' has no hostname.",
                                component_id=definition.id,
                                severity="error",
                            )
                        )
                    else:
                        # Normalize hostname
                        normalized_hostname = hostname.lower()
                        if normalized_hostname.endswith("."):
                            normalized_hostname = normalized_hostname[:-1]

                        # Check if hostname matches or is subdomain of any allowed domain.
                        # Strict matching: hostname == allowed OR hostname.endswith("." + allowed)
                        is_compliant_domain = False
                        for allowed_domain in allowed_set:
                            if normalized_hostname == allowed_domain or normalized_hostname.endswith(
                                "." + allowed_domain
                            ):
                                is_compliant_domain = True
                                break

                        if not is_compliant_domain:
                            violations.append(
                                ComplianceViolation(
                                    rule="domain_restriction",
                                    message=(
                                        f"Tool '{definition.name}' URI host '{hostname}' "
                                        f"is not in allowed domains: {config.allowed_domains}"
                                    ),
                                    component_id=definition.id,
                                    severity="error",
                                )
                            )

                except Exception as e:
                    violations.append(
                        ComplianceViolation(
                            rule="domain_restriction",
                            message=f"Failed to parse tool URI '{definition.uri}': {e}",
                            component_id=definition.id,
                            severity="error",
                        )
                    )

    return ComplianceReport(
        compliant=(len(violations) == 0),
        violations=violations,
        checked_at=datetime.now(timezone.utc),
    )
