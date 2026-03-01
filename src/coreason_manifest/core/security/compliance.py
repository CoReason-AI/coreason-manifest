import ast
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode


class ErrorCatalog(StrEnum):
    """
    Strict catalog of error codes for machine-remediable compliance reports.
    """

    # Security / Governance
    ERR_SEC_PATH_ESCAPE_001 = "ERR_SEC_PATH_ESCAPE_001"
    ERR_SEC_DOMAIN_BLOCKED_002 = "ERR_SEC_DOMAIN_BLOCKED_002"
    ERR_SEC_UNGUARDED_CRITICAL_003 = "ERR_SEC_UNGUARDED_CRITICAL_003"
    ERR_SEC_KILL_SWITCH_VIOLATION = "ERR_SEC_KILL_SWITCH_VIOLATION"

    # Topology
    ERR_TOPOLOGY_ORPHAN_001 = "ERR_TOPOLOGY_ORPHAN_001"
    ERR_TOPOLOGY_CYCLE_002 = "ERR_TOPOLOGY_CYCLE_002"
    ERR_TOPOLOGY_UNREACHABLE_RISK_003 = "ERR_TOPOLOGY_UNREACHABLE_RISK_003"
    ERR_TOPOLOGY_EMPTY_GRAPH = "ERR_TOPOLOGY_EMPTY_GRAPH"
    ERR_TOPOLOGY_RACE_CONDITION = "ERR_TOPOLOGY_RACE_CONDITION"
    ERR_TOPOLOGY_MISSING_ENTRY = "ERR_TOPOLOGY_MISSING_ENTRY"
    ERR_TOPOLOGY_DANGLING_EDGE = "ERR_TOPOLOGY_DANGLING_EDGE"
    ERR_TOPOLOGY_BROKEN_SWITCH = "ERR_TOPOLOGY_BROKEN_SWITCH"
    ERR_TOPOLOGY_LINEAR_EMPTY = "ERR_TOPOLOGY_LINEAR_EMPTY"
    ERR_TOPOLOGY_NODE_ID_COLLISION = "ERR_TOPOLOGY_NODE_ID_COLLISION"
    ERR_TOPOLOGY_ID_MISMATCH = "ERR_TOPOLOGY_ID_MISMATCH"

    # Capability / Resource
    ERR_CAP_MISSING_TOOL_001 = "ERR_CAP_MISSING_TOOL_001"
    ERR_CAP_UNDEFINED_PROFILE_002 = "ERR_CAP_UNDEFINED_PROFILE_002"
    ERR_CAP_MISSING_VAR = "ERR_CAP_MISSING_VAR"
    ERR_CAP_TYPE_MISMATCH = "ERR_CAP_TYPE_MISMATCH"
    ERR_CAP_MISSING_MIDDLEWARE = "ERR_CAP_MISSING_MIDDLEWARE"

    # Resilience
    ERR_RESILIENCE_MISSING_TEMPLATE = "ERR_RESILIENCE_MISSING_TEMPLATE"
    ERR_RESILIENCE_INVALID_REF = "ERR_RESILIENCE_INVALID_REF"
    ERR_RESILIENCE_MISMATCH = "ERR_RESILIENCE_MISMATCH"
    ERR_RESILIENCE_FALLBACK_MISSING = "ERR_RESILIENCE_FALLBACK_MISSING"
    ERR_RESILIENCE_ESCALATION_INVALID = "ERR_RESILIENCE_ESCALATION_INVALID"

    # Governance
    ERR_GOV_INVALID_CONFIG = "ERR_GOV_INVALID_CONFIG"
    ERR_GOV_CIRCUIT_FALLBACK_MISSING = "ERR_GOV_CIRCUIT_FALLBACK_MISSING"


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

    code: ErrorCatalog | str  # Allow str for backward compat or custom codes if needed
    severity: Literal["violation", "warning", "info"]
    message: str
    node_id: str | None = None
    remediation: RemediationAction | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class SecurityVisitor(ast.NodeVisitor):
    """
    Centralized strict AST whitelisting to prevent code injection via eval/exec interfaces.
    Enforces a strict subset of safe Python expression nodes.
    """

    def generic_visit(self, node: ast.AST) -> None:
        # Whitelist of allowed AST nodes (Tuple for fast isinstance checks)
        allowed = (
            ast.Expression,
            ast.BoolOp,
            ast.BinOp,
            ast.UnaryOp,
            ast.Compare,
            ast.Constant,
            ast.Name,
            ast.Load,
            ast.And,
            ast.Or,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.IsNot,
            ast.In,
            ast.NotIn,
            ast.Not,
            ast.Add,
            ast.Attribute,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
        )
        if not isinstance(node, allowed):
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.KILL_SWITCH_VIOLATION,
                message=f"Security Violation: forbidden AST node {type(node).__name__} in evaluated condition",
            )
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # Ensure Name usage is strictly Load context (prevents variable reassignment)
        if not isinstance(node.ctx, ast.Load):
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.KILL_SWITCH_VIOLATION,
                message=f"Security Violation: Name ctx {type(node.ctx).__name__} forbidden in evaluated condition",
            )
        super().generic_visit(node)
