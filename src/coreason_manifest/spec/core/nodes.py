from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# IMPORT ModelRef to link the new routing capability
from coreason_manifest.spec.core.engines import (
    FastPath,
    ModelRef,
    Optimizer,
    ReasoningConfig,
    Supervision,
)


class Node(BaseModel):
    """Base class for vertices of the execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str
    metadata: dict[str, Any]
    supervision: Supervision | None
    type: str


class CognitiveProfile(BaseModel):
    """The active processing unit of an agent."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    role: str
    persona: str
    reasoning: ReasoningConfig | None
    fast_path: FastPath | None


class AgentNode(Node):
    """
    Executes a cognitive task using a CognitiveProfile configuration.

    The 'profile' field is polymorphic:
    - Pass a CognitiveProfile object for inline definition (Scripting mode).
    - Pass a string ID to reference 'definitions.profiles' (Production mode).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["agent"] = "agent"
    profile: CognitiveProfile | str
    tools: list[str]


class SwitchNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["switch"] = "switch"
    variable: str = Field(..., description="The blackboard variable to evaluate.")
    cases: dict[str, str]
    default: str


class InspectorNodeBase(Node):
    """Shared logic for all inspection/judgement nodes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    target_variable: str
    criteria: str
    output_variable: str
    judge_model: ModelRef | None = Field(None, description="Model/Policy to use for semantic evaluation.")
    optimizer: Optimizer | None = None


class InspectorNode(InspectorNodeBase):
    """
    A node that evaluates a variable against criteria.
    Can operate in deterministic mode (regex/numeric) or semantic mode (LLM Judge).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["inspector"] = "inspector"

    mode: Literal["programmatic", "semantic"] = "programmatic"

    pass_threshold: float | None = None


class EmergenceInspectorNode(InspectorNodeBase):
    """
    Specialized inspector for detecting novel/emergent behaviors.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["emergence_inspector"] = "emergence_inspector"

    # Pre-defined behavioral markers to scan for
    detect_sycophancy: bool = True
    detect_power_seeking: bool = True
    detect_deception: bool = True

    # Override defaults - Forced semantic mode
    mode: Literal["semantic"] = "semantic"
    judge_model: ModelRef = Field(..., description="Model required for emergence detection")


class PlannerNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["planner"] = "planner"
    goal: str
    optimizer: Optimizer | None
    output_schema: dict[str, Any]


class HumanNode(Node):
    """
    Human-in-the-Loop interaction node.
    Supports blocking approval, or 'shadow' mode where the agent streams intent
    and proceeds if no signal is received, while 'steering' allows mid-flight plan alteration.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["human"] = "human"
    prompt: str
    timeout_seconds: int
    input_schema: dict[str, Any] | None = None
    options: list[str] | None = None

    # *** UPGRADE: SHADOW MODE ***
    interaction_mode: Literal["blocking", "shadow", "steering"] = Field(
        "blocking", description="Wait for input vs shadow execution."
    )
    shadow_timeout_seconds: int | None = Field(None, description="Time window for intervention in shadow mode.")


class SwarmNode(Node):
    """
    Dynamic Swarm Spawning (The "Hive").
    Spins up N ephemeral worker agents to process a dataset/workload in parallel.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["swarm"] = "swarm"

    # Worker Config
    worker_profile: str = Field(..., description="Reference to a CognitiveProfile ID.")
    workload_variable: str = Field(..., description="The Blackboard list/dataset to process.")

    # Topology
    distribution_strategy: Literal["sharded", "replicated"] = Field(
        ..., description="Sharded=split data; Replicated=same data, many attempts."
    )
    max_concurrency: int = Field(..., description="Limit parallel workers.")

    # Aggregation
    reducer_function: Literal["concat", "vote", "summarize"] = Field(..., description="How to combine results.")
    output_variable: str = Field(..., description="Variable to store the aggregated result.")


class PlaceholderNode(Node):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["placeholder"] = "placeholder"
    required_capabilities: list[str]


__all__ = [
    "AgentNode",
    "CognitiveProfile",
    "EmergenceInspectorNode",
    "HumanNode",
    "InspectorNode",
    "InspectorNodeBase",
    "Node",
    "PlaceholderNode",
    "PlannerNode",
    "SwarmNode",
    "SwitchNode",
]
