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

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel, ToolRiskLevel


class GovernanceConfig(CoReasonBaseModel):
    """Configuration for governance rules.

    Attributes:
        allowed_domains: List of allowed domains for tool URIs.
        max_risk_level: Maximum allowed risk level for tools.
        require_auth_for_critical_tools: Whether authentication is required for agents using CRITICAL tools.
        allow_inline_tools: Whether to allow inline tool definitions (which lack risk scoring).
        allow_custom_logic: Whether to allow LogicNodes and conditional Edges with custom code.
        strict_url_validation: Enforce strict, normalized URL validation.
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
    allow_inline_tools: bool = Field(
        True, description="Whether to allow inline tool definitions (which lack risk scoring)."
    )
    allow_custom_logic: bool = Field(
        False, description="Whether to allow LogicNodes and conditional Edges with custom code."
    )
    strict_url_validation: bool = Field(True, description="Enforce strict, normalized URL validation.")


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
    component_id: Optional[str] = Field(None, description="Name of the tool or component causing the issue.")


class ComplianceReport(CoReasonBaseModel):
    """Report of compliance checks.

    Attributes:
        passed: Whether the agent passed all checks.
        violations: List of violations found.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    passed: bool = Field(..., description="Whether the agent passed all checks.")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="List of violations found.")
