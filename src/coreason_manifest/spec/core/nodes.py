import warnings
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.engines import (
    FastPath,
    ModelRef,
    Optimizer,
    ReasoningConfig,
)
from coreason_manifest.spec.core.exceptions import DomainValidationError
from coreason_manifest.spec.core.resilience import ResilienceConfig
from coreason_manifest.spec.core.types import NodeID, ProfileID, VariableID
from coreason_manifest.spec.interop.compliance import RemediationAction


class Node(CoreasonModel):
    """Base class for vertices of the execution graph."""

    id: NodeID = Field(..., description="Unique identifier for the node.", examples=["start_node", "agent_1"])
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for the node.", examples=[{"created_by": "user123"}]
    )
    resilience: Annotated[
        ResilienceConfig | str | None,
        Field(description="Error handling policy or reference ID.", examples=["retry_policy_1"]),
    ] = None
    presentation: Annotated[
        PresentationHints | None,
        Field(description="UI rendering hints.", examples=[{"x": 100, "y": 200}]),
    ] = None
    type: str = Field(..., description="The type of the node.")


class CognitiveProfile(CoreasonModel):
    """The active processing unit of an agent."""

    role: str = Field(..., description="The role of the agent.", examples=["Assistant", "Researcher"])
    persona: str = Field(
        ..., description="The system prompt/persona description.", examples=["You are a helpful assistant."]
    )
    reasoning: ReasoningConfig | None = Field(
        None, description="The reasoning engine configuration.", examples=[{"type": "standard", "model": "gpt-4"}]
    )
    fast_path: FastPath | None = Field(
        None, description="Fast path configuration for low-latency responses.", examples=[{"model": "gpt-3.5-turbo"}]
    )


class AgentNode(Node):
    """
    Executes a cognitive task using a CognitiveProfile configuration.

    The 'profile' field is polymorphic:
    - Pass a CognitiveProfile object for inline definition (Scripting mode).
    - Pass a string ID to reference 'definitions.profiles' (Production mode).
    """

    type: Literal["agent"] = "agent"
    profile: CognitiveProfile | ProfileID = Field(
        ...,
        description="The cognitive profile configuration or a reference ID.",
        examples=["profile_1", {"role": "Assistant", "persona": "..."}],
    )
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool names available to this agent.",
        examples=[["calculator", "web_search"]],
    )


class SwitchNode(Node):
    type: Literal["switch"] = "switch"
    variable: VariableID = Field(..., description="The blackboard variable to evaluate.", examples=["user_sentiment"])
    cases: dict[str, NodeID] = Field(
        ...,
        description="Map of variable values to next node IDs.",
        examples=[{"positive": "thank_user", "negative": "apologize"}],
    )
    default: NodeID = Field(..., description="Default next node ID if no case matches.", examples=["default_handler"])


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


class PlannerNode(Node):
    type: Literal["planner"] = "planner"
    goal: str = Field(..., description="The high-level goal to plan for.", examples=["Build a website"])
    optimizer: Optimizer | None = Field(None, description="Optimization configuration.")
    output_schema: dict[str, Any] = Field(
        ...,
        description="JSON Schema for the plan output.",
        examples=[{"type": "object", "properties": {"steps": {"type": "array"}}}],
    )


class HumanNode(Node):
    """
    Human-in-the-Loop interaction node.
    Supports blocking approval, or 'shadow' mode where the agent streams intent
    and proceeds if no signal is received, while 'steering' allows mid-flight plan alteration.
    """

    type: Literal["human"] = "human"
    prompt: str = Field(..., description="Prompt to display to the human.", examples=["Approve this plan?"])
    timeout_seconds: Annotated[
        int | Literal["infinite"] | None,
        Field(
            description="Max wait time for blocking/steering. Use 'infinite' for no timeout.",
            examples=[300, "infinite"],
        ),
    ]
    input_schema: dict[str, Any] | None = Field(
        None, description="JSON Schema for expected human input.", examples=[{"type": "object"}]
    )
    options: list[str] | None = Field(
        None, description="List of valid options for the human.", examples=[["approve", "reject"]]
    )

    # *** UPGRADE: SHADOW MODE ***
    interaction_mode: Annotated[
        Literal["blocking", "shadow", "steering"],
        Field(description="Wait for input vs shadow execution.", examples=["blocking"]),
    ] = "blocking"
    shadow_timeout_seconds: Annotated[
        int | Literal["infinite"] | None,
        Field(description="Time window for intervention in shadow mode. Use 'infinite' for no timeout.", examples=[60]),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def coerce_magic_numbers(cls, data: Any) -> Any:
        """
        Directive 1: Semantic Coercion.
        Intercepts legacy '-1' magic numbers and converts them to 'infinite'.
        """
        if isinstance(data, dict):
            # Fix 5: Functional Purity - Copy data to avoid side-effects
            data = data.copy()

            # Check timeout_seconds
            val_timeout = data.get("timeout_seconds")
            if val_timeout in (-1, "-1"):
                warnings.warn(
                    "Magic number '-1' detected in 'timeout_seconds'. Coercing to 'infinite'.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                data["timeout_seconds"] = "infinite"

            # Check shadow_timeout_seconds
            val_shadow = data.get("shadow_timeout_seconds")
            if val_shadow in (-1, "-1"):
                warnings.warn(
                    "Magic number '-1' detected in 'shadow_timeout_seconds'. Coercing to 'infinite'.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                data["shadow_timeout_seconds"] = "infinite"
        return data

    @model_validator(mode="after")
    def validate_interaction_config(self) -> "HumanNode":
        # Fix 4: Temporal Collision - Enforce mutual exclusion
        if self.interaction_mode == "shadow":
            if self.shadow_timeout_seconds is None:
                raise DomainValidationError(
                    message="HumanNode in 'shadow' mode requires 'shadow_timeout_seconds'.",
                    remediation=RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Set 'shadow_timeout_seconds' to a valid value.",
                        patch_data=[
                            {
                                "op": "add",
                                "path": "/shadow_timeout_seconds",
                                "value": 300,
                            }
                        ],
                    ),
                )
            if self.timeout_seconds is not None:
                raise DomainValidationError(
                    message="HumanNode in 'shadow' mode must not have 'timeout_seconds'.",
                    remediation=RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Remove 'timeout_seconds'.",
                        patch_data=[
                            {
                                "op": "remove",
                                "path": "/timeout_seconds",
                            }
                        ],
                    ),
                )

        # SIM102: Combine nested if statements
        if self.interaction_mode == "blocking" and self.shadow_timeout_seconds is not None:
            raise DomainValidationError(
                message="HumanNode in 'blocking' mode must not have 'shadow_timeout_seconds'.",
                remediation=RemediationAction(
                    type="update_field",
                    target_node_id=self.id,
                    description="Remove 'shadow_timeout_seconds'.",
                    patch_data=[
                        {
                            "op": "remove",
                            "path": "/shadow_timeout_seconds",
                        }
                    ],
                ),
            )
        return self


class SwarmNode(Node):
    """
    Dynamic Swarm Spawning (The "Hive").
    Spins up N ephemeral worker agents to process a dataset/workload in parallel.
    """

    type: Literal["swarm"] = "swarm"

    # Worker Config
    worker_profile: ProfileID = Field(
        ..., description="Reference to a CognitiveProfile ID.", examples=["researcher_profile"]
    )
    workload_variable: VariableID = Field(
        ..., description="The Blackboard list/dataset to process.", examples=["urls_to_scrape"]
    )

    # Topology
    distribution_strategy: Literal["sharded", "replicated"] = Field(
        ..., description="Sharded=split data; Replicated=same data, many attempts.", examples=["sharded"]
    )
    max_concurrency: Annotated[
        int | Literal["infinite"] | None,
        Field(description="Limit parallel workers. Use 'infinite' for no limit.", examples=[10]),
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
            examples=[0.1],
        ),
    ] = 0.0

    # Aggregation
    reducer_function: Literal["concat", "vote", "summarize"] = Field(
        ..., description="How to combine results.", examples=["concat"]
    )
    aggregator_model: Annotated[
        ModelRef | None,
        Field(
            description="If set, uses this model to summarize the worker outputs into a single string.",
            examples=["gpt-4"],
        ),
    ] = None
    output_variable: VariableID = Field(
        ..., description="Variable to store the aggregated result.", examples=["final_report"]
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_magic_numbers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Fix 5: Functional Purity - Copy data
            data = data.copy()
            val = data.get("max_concurrency")
            if val in (-1, "-1"):
                warnings.warn(
                    "Magic number '-1' detected in 'max_concurrency'. Coercing to 'infinite'.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                data["max_concurrency"] = "infinite"
        return data

    @model_validator(mode="after")
    def validate_reducer_requirements(self) -> "SwarmNode":
        if self.reducer_function == "summarize" and not self.aggregator_model:
            raise DomainValidationError(
                message="SwarmNode with reducer='summarize' requires an 'aggregator_model'.",
                remediation=RemediationAction(
                    type="update_field",
                    target_node_id=self.id,
                    description="Add a default 'aggregator_model'.",
                    patch_data=[
                        {
                            "op": "add",
                            "path": "/aggregator_model",
                            "value": "gpt-4-turbo",  # Reasonable default
                        }
                    ],
                ),
            )
        return self


class PlaceholderNode(Node):
    type: Literal["placeholder"] = "placeholder"
    required_capabilities: list[str] = Field(
        ..., description="List of required capabilities.", examples=[["image_generation"]]
    )


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
