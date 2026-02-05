# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Governance logic for V2 Manifests."""

from typing import List
from urllib.parse import urlparse

from coreason_manifest.common import ToolRiskLevel
from coreason_manifest.governance import (
    ComplianceReport,
    ComplianceViolation,
    GovernanceConfig,
)
from coreason_manifest.v2.spec.definitions import (
    LogicStep,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
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


def check_compliance_v2(manifest: ManifestV2, config: GovernanceConfig) -> ComplianceReport:
    """Enforce policy on V2 Manifest before compilation.

    Validates:
    - Tool risk levels against allowed maximums.
    - Tool URIs against allowed domains.
    - Presence of custom logic (LogicStep, complex SwitchStep) if restricted.

    Args:
        manifest: The V2 manifest to check.
        config: The governance policy configuration.

    Returns:
        A ComplianceReport detailing violations.
    """
    violations: List[ComplianceViolation] = []

    # 1. Check Tools in Definitions
    has_critical_tools = False

    for _, definition in manifest.definitions.items():
        if isinstance(definition, ToolDefinition):
            if definition.risk_level == ToolRiskLevel.CRITICAL:
                has_critical_tools = True

            # Check Risk Level
            if config.max_risk_level:
                tool_score = _risk_score(definition.risk_level)
                max_score = _risk_score(config.max_risk_level)
                if tool_score > max_score:
                    violations.append(
                        ComplianceViolation(
                            rule="risk_level_restriction",
                            message=(
                                f"Tool '{definition.name}' risk level '{definition.risk_level.value}' "
                                f"exceeds allowed maximum '{config.max_risk_level.value}'."
                            ),
                            component_id=definition.id,
                        )
                    )

            # Check Allowed Domains
            if config.allowed_domains is not None:
                try:
                    parsed_uri = urlparse(str(definition.uri))
                    hostname = parsed_uri.hostname

                    if not hostname:
                        violations.append(
                            ComplianceViolation(
                                rule="domain_restriction",
                                message=(f"Tool '{definition.name}' URI '{definition.uri}' has no hostname."),
                                component_id=definition.id,
                            )
                        )
                    else:
                        # Normalize hostname
                        hostname = hostname.lower()
                        if hostname.endswith("."):
                            hostname = hostname[:-1]

                        # Prepare allowed set
                        if config.strict_url_validation:
                            allowed_set = {d.lower() for d in config.allowed_domains if d}
                        else:
                            allowed_set = set(config.allowed_domains)

                        if hostname not in allowed_set:
                            violations.append(
                                ComplianceViolation(
                                    rule="domain_restriction",
                                    message=(
                                        f"Tool '{definition.name}' URI host '{hostname}' "
                                        f"is not in allowed domains: {config.allowed_domains}"
                                    ),
                                    component_id=definition.id,
                                )
                            )
                except Exception as e:
                    violations.append(
                        ComplianceViolation(
                            rule="domain_restriction",
                            message=f"Failed to parse tool URI '{definition.uri}': {e}",
                            component_id=definition.id,
                        )
                    )

    if config.require_auth_for_critical_tools and has_critical_tools:
        # Check if auth is required in metadata
        requires_auth = False
        # Try direct attribute access first (if it were defined in schema)
        if getattr(manifest.metadata, "requires_auth", False):
            requires_auth = True
        # Try model_extra for dynamic fields
        elif manifest.metadata.model_extra and manifest.metadata.model_extra.get("requires_auth"):
            requires_auth = True

        if not requires_auth:
            violations.append(
                ComplianceViolation(
                    rule="auth_mandate_missing",
                    message="Agent uses CRITICAL tools but does not enforce authentication (metadata.requires_auth=True).",
                    component_id="metadata",
                )
            )

    # 2. Check Workflow Steps for Custom Logic
    if not config.allow_custom_logic:
        for step_id, step in manifest.workflow.steps.items():
            if isinstance(step, LogicStep):
                violations.append(
                    ComplianceViolation(
                        rule="custom_logic_restriction",
                        message="LogicStep containing custom code is not allowed by policy.",
                        component_id=step_id,
                    )
                )
            elif isinstance(step, SwitchStep):
                # Flag complex conditions (function calls, imports, internals) as custom logic.
                for condition in step.cases.keys():
                    if "(" in condition or "import " in condition or "__" in condition:
                        violations.append(
                            ComplianceViolation(
                                rule="custom_logic_restriction",
                                message=(
                                    f"SwitchStep '{step_id}' contains complex condition '{condition}' "
                                    "which is flagged as custom logic."
                                ),
                                component_id=step_id,
                            )
                        )

    return ComplianceReport(passed=len(violations) == 0, violations=violations)
