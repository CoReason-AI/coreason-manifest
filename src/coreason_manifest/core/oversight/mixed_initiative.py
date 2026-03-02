import ast
from typing import Literal

from pydantic import Field, field_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.security.compliance import SecurityVisitor


class AllocationRule(CoreasonModel):
    """Rule defining condition for dynamic allocation to a target queue."""

    condition: str = Field(..., description="Python expression (AST-whitelisted) to evaluate.", examples=["risk > 5"])
    target_queue: str = Field(..., description="Queue to route to if the condition is met.", examples=["review_queue"])

    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition_sandbox(cls, v: str) -> str:
        """Validate the condition string using the SecurityVisitor."""
        if not v or not v.strip():
            raise ValueError("Condition string cannot be empty.")
        try:
            tree = ast.parse(v, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Syntax error in condition '{v}': {e}") from e
        visitor = SecurityVisitor()
        visitor.visit(tree)
        return v


class BoundedAutonomyConfig(CoreasonModel):
    """Configuration for bounding agent autonomy during human intervention."""

    intervention_window_seconds: int = Field(
        ..., description="Seconds to wait for a human intervention.", examples=[30]
    )
    timeout_behavior: Literal["proceed", "escalate", "fail"] = Field(
        ..., description="Behavior when the intervention window times out.", examples=["escalate"]
    )


class MixedInitiativePolicy(CoreasonModel):
    """Policy configuring mixed initiative human-AI interaction."""

    enable_shadow_telemetry: bool = Field(
        False, description="Enable shadow telemetry for observability.", examples=[True]
    )
    bounded_autonomy: BoundedAutonomyConfig | None = Field(
        None,
        description="Configuration for bounded autonomy.",
        examples=[{"intervention_window_seconds": 60, "timeout_behavior": "proceed"}],
    )
    dynamic_allocation_rules: list[AllocationRule] = Field(
        default_factory=list,
        description="Rules for dynamic task allocation.",
        examples=[[{"condition": "confidence < 0.5", "target_queue": "human_review"}]],
    )
