from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# IMPORT ModelRef to link the new routing capability
from coreason_manifest.spec.core.engines import (
    ModelRef,
    Optimizer,
    ReasoningConfig,
    Reflex,
    Supervision,
)


class Node(BaseModel):
    """Base class for vertices of the execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str
    metadata: dict[str, Any]
    supervision: Supervision | None
    type: str


class Brain(BaseModel):
    """The active processing unit of an agent."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    role: str
    persona: str
    reasoning: ReasoningConfig | None
    reflex: Reflex | None


class AgentNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["agent"] = "agent"
    brain: Brain
    tools: list[str]


class SwitchNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["switch"] = "switch"
    variable: str = Field(..., description="The blackboard variable to evaluate.")
    cases: dict[str, str]
    default: str


class InspectorNode(Node):
    """
    A node that evaluates a variable against criteria.
    Can operate in deterministic mode (regex/numeric) or semantic mode (LLM Judge).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["inspector"] = "inspector"
    target_variable: str

    # Dual-mode criteria: regex/python expression OR natural language rubric
    criteria: str

    mode: Literal["programmatic", "semantic"] = "programmatic"

    # SOTA UPGRADE: Use the new ModelRef for the judge
    judge_model: ModelRef | None = Field(None, description="Model/Policy to use for semantic evaluation.")

    pass_threshold: float | None = None
    output_variable: str
    optimizer: Optimizer | None = None


class PlannerNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["planner"] = "planner"
    goal: str
    optimizer: Optimizer | None
    output_schema: dict[str, Any]


class HumanNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["human"] = "human"
    prompt: str
    timeout_seconds: int
    input_schema: dict[str, Any] | None = None
    options: list[str] | None = None


class Placeholder(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["placeholder"] = "placeholder"
    required_capabilities: list[str]
