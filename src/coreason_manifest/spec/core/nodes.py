from pydantic import BaseModel, ConfigDict

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
    metadata: dict[str, str]
    supervision: Supervision | None


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

    brain: Brain
    tools: list[str]


class SwitchNode(Node):
    """A node for branching logic tracks."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    cases: dict[str, str]
    default: str


class PlannerNode(Node):
    """A node that dynamically plans/solves."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    goal: str
    optimizer: Optimizer | None


class HumanNode(Node):
    """A node representing human interaction."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    prompt: str
    timeout_seconds: int


class Placeholder(Node):
    """An empty slot to be filled later."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    required_capabilities: list[str]
