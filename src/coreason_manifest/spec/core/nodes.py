from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.spec.core.engines import (
    Optimizer,
    ReasoningEngine,
    Reflex,
    Supervision,
)


class Node(BaseModel):
    """Base class for vertices of the execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str
    metadata: dict[str, Any]
    supervision: Supervision | None
    type: str  # Base type field


class Brain(BaseModel):
    """The active processing unit of an agent."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    role: str
    persona: str
    reasoning: ReasoningEngine | None
    reflex: Reflex | None


class AgentNode(Node):
    """A node representing an agent."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["agent"] = "agent"
    brain: Brain
    tools: list[str]


class SwitchNode(Node):
    """A node for branching logic tracks."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["switch"] = "switch"
    variable: str = Field(..., description="The blackboard variable to evaluate.")
    cases: dict[str, str]
    default: str


class InspectorNode(Node):
    """A node that evaluates a variable against criteria."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["inspector"] = "inspector"
    target_variable: str
    criteria: str
    pass_threshold: float | None = None
    output_variable: str
    optimizer: Optimizer | None = None


class PlannerNode(Node):
    """A node that dynamically plans/solves."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["planner"] = "planner"
    goal: str
    optimizer: Optimizer | None
    output_schema: dict[str, Any] = Field(
        ...,
        description="JSON Schema defining the structure of the generated plan/result.",
    )


class HumanNode(Node):
    """A node representing human interaction."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["human"] = "human"
    prompt: str
    timeout_seconds: int


class Placeholder(Node):
    """An empty slot to be filled later."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["placeholder"] = "placeholder"
    required_capabilities: list[str]
