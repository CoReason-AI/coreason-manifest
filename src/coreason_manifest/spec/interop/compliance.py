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
        "replace_node",
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
