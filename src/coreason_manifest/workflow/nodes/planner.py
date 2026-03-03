# Prosperity-3.0
from typing import Any, Literal

from pydantic import Field, field_validator

from coreason_manifest.compute.reasoning import Optimizer, ReasoningConfig

from .base import Node


class PlannerNode(Node):
    """A node that generates a structured plan to achieve a goal."""

    type: Literal["planner"] = Field("planner", description="The type of the node.", examples=["planner"])
    goal: str = Field(..., description="The high-level goal to plan for.", examples=["Build a website"])
    optimizer: Optimizer | None = Field(
        None, description="Optimization configuration.", examples=[{"strategy": "greedy"}]
    )
    reasoning: ReasoningConfig | None = Field(
        None,
        description="The advanced reasoning engine (e.g., TreeSearchReasoning, AdaptiveReasoning) "
        "assigned to generate the plan.",
    )
    output_schema: dict[str, Any] = Field(
        ...,
        description="JSON Schema for the plan output.",
        examples=[{"type": "object", "properties": {"steps": {"type": "array"}}}],
    )

    @field_validator("output_schema")
    @classmethod
    def validate_planner_output_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Enforce that output_schema is an object or array."""
        if v.get("type") not in ["object", "array"]:
            raise ValueError("PlannerNode output_schema must define an object or array representing the PlanTree.")
        return v
