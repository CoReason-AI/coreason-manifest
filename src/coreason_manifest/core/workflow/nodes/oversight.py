# Prosperity-3.0
from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.compute.reasoning import ModelRef, Optimizer
from coreason_manifest.core.primitives.registry import register_node
from coreason_manifest.core.primitives.types import VariableID

from .base import Node


class InspectorNodeBase(Node):
    """Shared logic for all inspection/judgement nodes."""

    target_variable: VariableID = Field(..., description="The variable to inspect.", examples=["generated_content"])
    criteria: str = Field(..., description="The criteria to evaluate against.", examples=["Is the content safe?"])
    output_variable: VariableID = Field(..., description="The variable to store the result.", examples=["is_safe"])
    judge_model: Annotated[
        ModelRef | None,
        Field(description="Model/Policy to use for semantic evaluation.", examples=["gpt-4"]),
    ] = None
    optimizer: Optimizer | None = Field(None, description="Optimization configuration.")

    @property
    def to_node_variable(self) -> VariableID:
        return self.target_variable


@register_node
class InspectorNode(InspectorNodeBase):
    """
    A node that evaluates a variable against criteria.
    Can operate in deterministic mode (regex/numeric) or semantic mode (LLM Judge).
    """

    type: Literal["inspector"] = "inspector"

    mode: Literal["programmatic", "semantic"] = Field(
        "programmatic", description="Evaluation mode.", examples=["semantic"]
    )

    pass_threshold: float | None = Field(None, description="Threshold for passing the check (0.0-1.0).", examples=[0.8])


@register_node
class EmergenceInspectorNode(InspectorNodeBase):
    """
    Specialized inspector for detecting novel/emergent behaviors.
    """

    type: Literal["emergence_inspector"] = "emergence_inspector"

    # Pre-defined behavioral markers to scan for
    detect_sycophancy: bool = Field(True, description="Detect if the agent is being sycophantic.")
    detect_power_seeking: bool = Field(True, description="Detect power-seeking behavior.")
    detect_deception: bool = Field(True, description="Detect deceptive behavior.")

    # Override defaults - Forced semantic mode
    mode: Literal["semantic"] = "semantic"
    judge_model: ModelRef = Field(..., description="Model required for emergence detection")
