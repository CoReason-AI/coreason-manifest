from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorCatalog(StrEnum):
    """
    Strict catalog of error codes for machine-remediable compliance reports.
    """

    # Security / Governance
    ERR_SEC_PATH_ESCAPE_001 = "ERR_SEC_PATH_ESCAPE_001"
    ERR_SEC_DOMAIN_BLOCKED_002 = "ERR_SEC_DOMAIN_BLOCKED_002"
    ERR_SEC_UNGUARDED_CRITICAL_003 = "ERR_SEC_UNGUARDED_CRITICAL_003"

    # Topology
    ERR_TOPOLOGY_ORPHAN_001 = "ERR_TOPOLOGY_ORPHAN_001"
    ERR_TOPOLOGY_CYCLE_002 = "ERR_TOPOLOGY_CYCLE_002"
    ERR_TOPOLOGY_UNREACHABLE_RISK_003 = "ERR_TOPOLOGY_UNREACHABLE_RISK_003"

    # Capability / Resource
    ERR_CAP_MISSING_TOOL_001 = "ERR_CAP_MISSING_TOOL_001"
    ERR_CAP_UNDEFINED_PROFILE_002 = "ERR_CAP_UNDEFINED_PROFILE_002"


class RemediationAction(BaseModel):
    """
    Standard remediation payload using JSON Patch (RFC 6902).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal[
        "add_guard_node",
        "whitelist_domain",
        "prune_node",
        "update_field",
        "semantic_repair",
        "prune_topology",
    ]
    target_node_id: str | None = None
    format: Literal["json_patch", "merge_patch"] = "json_patch"
    patch_data: list[dict[str, Any]] | dict[str, Any]
    description: str


class ComplianceReport(BaseModel):
    """
    A strong-typed compliance violation report.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: ErrorCatalog
    severity: Literal["violation", "warning", "info"]
    message: str
    node_id: str | None = None
    remediation: RemediationAction | None = None
    details: dict[str, Any] = Field(default_factory=dict)


def legacy_error_adapter(report: ComplianceReport, consumer_version: str = "v0.24.0") -> str:
    """
    Adapts a modern ComplianceReport into a legacy error string format.

    Legacy Format Example: "Security Error: Reference '{ref}' escapes the root directory."
    """
    if consumer_version >= "v0.25.0":
        # Return strict JSON representation for modern clients
        return report.model_dump_json()

    # Legacy mapping
    if report.code == ErrorCatalog.ERR_SEC_DOMAIN_BLOCKED_002:
        domain = report.details.get("domain", "unknown")
        tool_name = report.details.get("tool_name", "unknown")
        return f"Tool '{tool_name}' uses blocked domain: {domain}"

    if report.code == ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003:
        reason = report.details.get("reason", "unknown")
        return (
            f"Policy Violation: Node '{report.node_id}' requires high-risk features "
            f"({reason}) but is not guarded by a HumanNode."
        )

    if report.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003:
        reason = report.details.get("reason", "unknown")
        return (
            f"Topology Violation: Node '{report.node_id}' is unreachable (utility island) "
            f"but requires high-risk capabilities: {reason}."
        )

    # Fallback for unknown codes or generic errors
    return f"{report.severity.title()}: {report.message} (Code: {report.code})"
