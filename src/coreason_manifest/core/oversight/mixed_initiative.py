import ast
from typing import Literal

from pydantic import Field, field_validator

from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode


class SecurityVisitor(ast.NodeVisitor):
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
                code=ManifestErrorCode.CRSN_SEC_KILL_SWITCH_VIOLATION,
                message=f"Security Violation: forbidden AST node {type(node).__name__} in allocation rule condition",
            )
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # Ensure Name usage is strictly Load context (prevents variable reassignment)
        if not isinstance(node.ctx, ast.Load):
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_SEC_KILL_SWITCH_VIOLATION,
                message=f"Security Violation: Name ctx {type(node.ctx).__name__} forbidden in rule condition",
            )
        super().generic_visit(node)


class AllocationRule(CoreasonModel):
    condition: str
    target_queue: str

    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition_sandbox(cls, v: str) -> str:
        try:
            tree = ast.parse(v, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in condition: {e}") from e

        visitor = SecurityVisitor()
        visitor.visit(tree)
        return v


class BoundedAutonomyConfig(CoreasonModel):
    intervention_window_seconds: int
    timeout_behavior: Literal["proceed", "escalate", "fail"]


class MixedInitiativePolicy(CoreasonModel):
    enable_shadow_telemetry: bool = False
    bounded_autonomy: BoundedAutonomyConfig | None = None
    dynamic_allocation_rules: list[AllocationRule] = Field(default_factory=list)
