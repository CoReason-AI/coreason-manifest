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

from typing import List, Optional
from urllib.parse import urlparse

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.agent import (
    AgentDefinition,
    InlineToolDefinition,
    ToolRequirement,
    ToolRiskLevel,
)
from coreason_manifest.definitions.base import CoReasonBaseModel


class GovernanceConfig(CoReasonBaseModel):
    """Configuration for governance rules.

    Attributes:
        allowed_domains: List of allowed domains for tool URIs.
        max_risk_level: Maximum allowed risk level for tools.
        require_auth_for_critical_tools: Whether authentication is required for agents using CRITICAL tools.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed_domains: Optional[List[str]] = Field(
        None, description="If provided, all Tool URIs must match one of these domains."
    )
    max_risk_level: Optional[ToolRiskLevel] = Field(
        None, description="If provided, no tool can exceed this risk level."
    )
    require_auth_for_critical_tools: bool = Field(
        True,
        description="If an agent uses a CRITICAL tool, agent.metadata.requires_auth must be True.",
    )


class ComplianceViolation(CoReasonBaseModel):
    """Details of a compliance violation.

    Attributes:
        rule: Name of the rule broken.
        message: Human readable details.
        component_id: Name of the tool or component causing the issue.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule: str = Field(..., description="Name of the rule broken, e.g., 'domain_restriction'.")
    message: str = Field(..., description="Human readable details.")
    component_id: Optional[str] = Field(
        None, description="Name of the tool or component causing the issue."
    )


class ComplianceReport(CoReasonBaseModel):
    """Report of compliance checks.

    Attributes:
        passed: Whether the agent passed all checks.
        violations: List of violations found.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    passed: bool = Field(..., description="Whether the agent passed all checks.")
    violations: List[ComplianceViolation] = Field(
        default_factory=list, description="List of violations found."
    )


def _risk_score(level: ToolRiskLevel) -> int:
    """Convert risk level to integer score for comparison.

    Args:
        level: The risk level.

    Returns:
        Integer score (0=SAFE, 1=STANDARD, 2=CRITICAL).
    """
    if level == ToolRiskLevel.SAFE:
        return 0
    if level == ToolRiskLevel.STANDARD:
        return 1
    if level == ToolRiskLevel.CRITICAL:
        return 2
    return 0  # pragma: no cover


def check_compliance(agent: AgentDefinition, config: GovernanceConfig) -> ComplianceReport:
    """Validate an AgentDefinition against a GovernanceConfig.

    Args:
        agent: The AgentDefinition to validate.
        config: The GovernanceConfig rules.

    Returns:
        A ComplianceReport detailing pass/fail status and violations.
    """
    violations: List[ComplianceViolation] = []

    # Check Tools
    has_critical_tool = False

    for tool in agent.dependencies.tools:
        if isinstance(tool, InlineToolDefinition):
            # Inline tools don't have URI or risk level in current schema
            continue

        if isinstance(tool, ToolRequirement):
            # Domain Check
            if config.allowed_domains is not None:
                try:
                    parsed_uri = urlparse(str(tool.uri))
                    hostname = parsed_uri.hostname
                    if hostname not in config.allowed_domains:
                        violations.append(
                            ComplianceViolation(
                                rule="domain_restriction",
                                message=(
                                    f"Tool URI '{tool.uri}' (host: {hostname}) is not in allowed domains: "
                                    f"{config.allowed_domains}"
                                ),
                                component_id=str(tool.uri),
                            )
                        )
                except Exception as e:
                    violations.append(
                        ComplianceViolation(
                            rule="domain_restriction",
                            message=f"Failed to parse tool URI '{tool.uri}': {e}",
                            component_id=str(tool.uri),
                        )
                    )

            # Risk Level Check
            if config.max_risk_level:
                tool_score = _risk_score(tool.risk_level)
                max_score = _risk_score(config.max_risk_level)
                if tool_score > max_score:
                    violations.append(
                        ComplianceViolation(
                            rule="risk_level_restriction",
                            message=(
                                f"Tool risk level '{tool.risk_level.value}' exceeds allowed maximum "
                                f"'{config.max_risk_level.value}'."
                            ),
                            component_id=str(tool.uri),
                        )
                    )

            # Track Critical Tools for Auth Check
            if tool.risk_level == ToolRiskLevel.CRITICAL:
                has_critical_tool = True

    # Auth Check
    if config.require_auth_for_critical_tools and has_critical_tool:
        if not agent.metadata.requires_auth:
            violations.append(
                ComplianceViolation(
                    rule="auth_requirement",
                    message="Agent uses CRITICAL tools but 'requires_auth' is False.",
                    component_id="agent.metadata",
                )
            )

    return ComplianceReport(passed=len(violations) == 0, violations=violations)
