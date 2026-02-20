from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.spec.common.presentation import PresentationHints

# IMPORT ModelRef to link the new routing capability
from coreason_manifest.spec.core.engines import (
    FastPath,
    ModelRef,
    Optimizer,
    ReasoningConfig,
)
from coreason_manifest.spec.core.exceptions import DomainValidationError
from coreason_manifest.spec.core.resilience import ResilienceConfig
from coreason_manifest.spec.interop.compliance import RemediationAction
from coreason_manifest.utils.logger import logger


class Node(BaseModel):
    """Base class for vertices of the execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str
    metadata: dict[str, Any]
    resilience: Annotated[ResilienceConfig | str | None, Field(description="Error handling policy.")] = None
    presentation: Annotated[PresentationHints | None, Field(description="UI rendering hints.")] = None
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
    judge_model: Annotated[ModelRef | None, Field(description="Model/Policy to use for semantic evaluation.")] = None
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
    timeout_seconds: Annotated[
        int | Literal["infinite"] | None,
        Field(description="Max wait time for blocking/steering. Use 'infinite' for no timeout."),
    ]
    input_schema: dict[str, Any] | None = None
    options: list[str] | None = None

    # *** UPGRADE: SHADOW MODE ***
    interaction_mode: Annotated[
        Literal["blocking", "shadow", "steering"], Field(description="Wait for input vs shadow execution.")
    ] = "blocking"
    shadow_timeout_seconds: Annotated[
        int | Literal["infinite"] | None,
        Field(description="Time window for intervention in shadow mode. Use 'infinite' for no timeout."),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def coerce_magic_numbers(cls, data: Any) -> Any:
        """
        Directive 1: Semantic Coercion.
        Intercepts legacy '-1' magic numbers and converts them to 'infinite'.
        """
        if isinstance(data, dict):
            # Check timeout_seconds
            if "timeout_seconds" in data and data["timeout_seconds"] == -1:
                logger.warning(
                    "Deprecation Warning: Magic number '-1' detected in 'timeout_seconds'. Coercing to 'infinite'."
                )
                data["timeout_seconds"] = "infinite"

            # Check shadow_timeout_seconds
            if "shadow_timeout_seconds" in data and data["shadow_timeout_seconds"] == -1:
                logger.warning(
                    "Deprecation Warning: Magic number '-1' detected in 'shadow_timeout_seconds'. "
                    "Coercing to 'infinite'."
                )
                data["shadow_timeout_seconds"] = "infinite"
        return data

    @model_validator(mode="after")
    def validate_interaction_config(self) -> "HumanNode":
        if self.interaction_mode == "shadow" and self.shadow_timeout_seconds is None:
            raise DomainValidationError(
                message="HumanNode in 'shadow' mode requires 'shadow_timeout_seconds'.",
                remediation=RemediationAction(
                    type="prune_node",  # Or update_node if supported, but defaulting to JSON patch on the node
                    target_node_id=self.id,
                    description="Set 'shadow_timeout_seconds' to a valid value.",
                    patch_data={
                        "op": "add",
                        "path": f"/graph/nodes/{self.id}/shadow_timeout_seconds",
                        "value": 300,
                    },
                ),
            )
        if self.interaction_mode == "blocking" and self.shadow_timeout_seconds is not None:
            raise DomainValidationError(
                message="HumanNode in 'blocking' mode must not have 'shadow_timeout_seconds'.",
                remediation=RemediationAction(
                    type="prune_node",  # Using generic patch mechanism
                    target_node_id=self.id,
                    description="Remove 'shadow_timeout_seconds'.",
                    patch_data={
                        "op": "remove",
                        "path": f"/graph/nodes/{self.id}/shadow_timeout_seconds",
                    },
                ),
            )
        return self


class SwarmNode(Node):
    """
    Dynamic Swarm Spawning (The "Hive").
    Spins up N ephemeral worker agents to process a dataset/workload in parallel.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["swarm"] = "swarm"

    # Worker Config
    worker_profile: str = Field(..., min_length=1, description="Reference to a CognitiveProfile ID.")
    workload_variable: str = Field(..., min_length=1, description="The Blackboard list/dataset to process.")

    # Topology
    distribution_strategy: Literal["sharded", "replicated"] = Field(
        ..., description="Sharded=split data; Replicated=same data, many attempts."
    )
    max_concurrency: Annotated[
        int | Literal["infinite"] | None,
        Field(description="Limit parallel workers. Use 'infinite' for no limit."),
    ]

    # SOTA: Reliability (Partial Failure)
    failure_tolerance_percent: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description=(
                "0.0 = All must succeed. 0.2 = Allow 20% failure. "
                "Executed AFTER the Node's 'resilience' strategy. "
                "E.g., if retries exhaust, this tolerance allows the Swarm to still succeed partially."
            ),
        ),
    ] = 0.0

    # Aggregation
    reducer_function: Literal["concat", "vote", "summarize"] = Field(..., description="How to combine results.")
    aggregator_model: Annotated[
        ModelRef | None,
        Field(description="If set, uses this model to summarize the worker outputs into a single string."),
    ] = None
    output_variable: str = Field(..., description="Variable to store the aggregated result.")

    @model_validator(mode="before")
    @classmethod
    def coerce_magic_numbers(cls, data: Any) -> Any:
        if isinstance(data, dict) and "max_concurrency" in data and data["max_concurrency"] == -1:
            logger.warning(
                "Deprecation Warning: Magic number '-1' detected in 'max_concurrency'. Coercing to 'infinite'."
            )
            data["max_concurrency"] = "infinite"
        return data

    @model_validator(mode="after")
    def validate_reducer_requirements(self) -> "SwarmNode":
        if self.reducer_function == "summarize" and not self.aggregator_model:
            raise DomainValidationError(
                message="SwarmNode with reducer='summarize' requires an 'aggregator_model'.",
                remediation=RemediationAction(
                    type="prune_node",  # Or update/patch
                    target_node_id=self.id,
                    description="Add a default 'aggregator_model'.",
                    patch_data={
                        "op": "add",
                        "path": f"/graph/nodes/{self.id}/aggregator_model",
                        "value": "gpt-4-turbo",  # Reasonable default
                    },
                ),
            )
        return self


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
