# Prosperity-3.0
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.compute.reasoning import ModelRef, Optimizer
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
    optimizer: Optimizer | None = Field(
        None, description="Optimization configuration.", examples=[{"strategy": "greedy"}]
    )

    @property
    def to_node_variable(self) -> VariableID:
        """Return the target variable."""
        return self.target_variable


class InspectorNode(InspectorNodeBase):
    """A node that evaluates a variable against criteria in deterministic or semantic mode."""

    type: Literal["inspector"] = Field("inspector", description="The type of the node.", examples=["inspector"])

    mode: Literal["programmatic", "semantic", "symbolic_execution"] = Field(
        "programmatic", description="Evaluation mode.", examples=["semantic"]
    )

    target_solver: (
        Literal["lean4", "z3", "dafny", "r_sandbox", "mesh_ontology_validator", "emtree_validator", "meddra_validator"]
        | None
    ) = Field(
        None,
        description="The deterministic symbolic engine or ontological dictionary used to compile/verify the output.",
    )

    tutor_prompt: str | None = Field(
        None, description="System instructions injected into the LLM context if symbolic compilation fails."
    )

    pass_threshold: float | None = Field(None, description="Threshold for passing the check (0.0-1.0).", examples=[0.8])

    @model_validator(mode="after")
    def validate_symbolic_requirements(self) -> "InspectorNode":
        """Enforce that symbolic execution mode requires target_solver and tutor_prompt."""
        if self.mode == "symbolic_execution":
            if self.target_solver is None:
                raise ValueError("target_solver must be provided when mode is 'symbolic_execution'")
            if self.tutor_prompt is None:
                raise ValueError(
                    "tutor_prompt must be provided when mode is 'symbolic_execution' to guide the repair loop"
                )
        return self


class EmergenceInspectorNode(InspectorNodeBase):
    """Specialized inspector for detecting novel/emergent behaviors."""

    type: Literal["emergence_inspector", "EmergenceInspectorNode"] = Field(
        "emergence_inspector",
        description="The type of the node.",
        examples=["emergence_inspector"],
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("type") == "EmergenceInspectorNode":
            data = data.copy()
            data["type"] = "emergence_inspector"
        return data

    is_security_guard: Literal[True] = Field(
        True, description="Indicates this node acts as a valid cryptographic barrier for high-risk execution."
    )

    detect_sycophancy: bool = Field(True, description="Detect if the agent is being sycophantic.", examples=[True])
    detect_power_seeking: bool = Field(True, description="Detect power-seeking behavior.", examples=[True])
    detect_deception: bool = Field(True, description="Detect deceptive behavior.", examples=[True])

    mode: Literal["semantic"] = Field("semantic", description="Forced semantic evaluation mode.", examples=["semantic"])
    judge_model: ModelRef = Field(..., description="Model required for emergence detection.", examples=["gpt-4"])
