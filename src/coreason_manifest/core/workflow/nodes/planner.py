# Prosperity-3.0
from typing import Any, Literal

from pydantic import Field, field_validator

from coreason_manifest.core.compute.reasoning import Optimizer
from coreason_manifest.core.primitives.registry import register_node

from .base import Node


@register_node
class PlannerNode(Node):
    type: Literal["planner"] = "planner"
    goal: str = Field(..., description="The high-level goal to plan for.", examples=["Build a website"])
    optimizer: Optimizer | None = Field(None, description="Optimization configuration.")
    output_schema: dict[str, Any] = Field(
        ...,
        description="JSON Schema for the plan output.",
        examples=[{"type": "object", "properties": {"steps": {"type": "array"}}}],
    )

    @field_validator("output_schema")
    @classmethod
    def validate_planner_output_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        if v.get("type") not in ["object", "array"]:
            raise ValueError("PlannerNode output_schema must define an object or array representing the PlanTree.")
        return v
