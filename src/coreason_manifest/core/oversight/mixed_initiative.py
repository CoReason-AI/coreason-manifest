import ast
from typing import Literal

from pydantic import Field, field_validator

from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.compliance import SecurityVisitor


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
