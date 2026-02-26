from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.co_intelligence import EscalationCriteria
from coreason_manifest.spec.core.contracts import AtomicSkill, PlanTree
from coreason_manifest.spec.core.engines import (
    DecompositionReasoning,
    FastPath,
    ModelRef,
    Optimizer,
    ReasoningConfig,
)
from coreason_manifest.spec.core.governance import OperationalPolicy
from coreason_manifest.spec.core.memory import MemorySubsystem
from coreason_manifest.spec.core.resilience import EscalationStrategy, ResilienceConfig
from coreason_manifest.spec.core.types import (
    CoercibleStringList,
    NodeID,
    ProfileID,
    VariableID,
)
from coreason_manifest.spec.interop.compliance import RemediationAction
from coreason_manifest.spec.interop.exceptions import ManifestError, ManifestErrorCode


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
    memory: MemorySubsystem | None = Field(None, description="The 4-tier hierarchical memory configuration.")


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
    tools: CoercibleStringList = Field(
        default_factory=list,
        description="List of tool names available to this agent.",
        examples=[["calculator", "web_search"]],
    )
    operational_policy: OperationalPolicy | None = Field(
        None, description="Local operational limits. Overrides global Governance limits if set."
    )
    escalation_rules: list[EscalationCriteria] = Field(
        default_factory=list,
        description="Local escalation rules for this agent.",
        examples=[{"condition": "confidence < 0.5", "role": "supervisor"}],
    )
    immutable: bool = Field(
        False, description="If True, this node represents a fixed recipe step that cannot be altered by planners."
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

    @property
    def to_node_variable(self) -> VariableID:
        return self.target_variable


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

    def process(
        self,
        input_payload: Any,
        context: dict[str, Any],
        constraints: list[str | AtomicSkill] | None = None,
    ) -> Any:
        """
        Executes the planning logic to produce a PlanTree, and then compiles it into a graph representation.
        """
        if constraints is None:
            constraints = []

        # 1. Select Engine (Mocking selection logic, using default configuration if available)
        # In a real system, this might come from the node configuration or be injected via context
        # We avoid hardcoding "gpt-4" by allowing the model to be specified in context or defaulting to a generic placeholder
        model_id = context.get("model", "default_model")
        engine = DecompositionReasoning(
             model=model_id,
             decomposition_breadth=3
        )

        # 1.5 Extract constraints from input if available
        # This allows users to pass dynamic constraints at runtime via the input payload
        if isinstance(input_payload, dict) and "constraints" in input_payload:
            dynamic_constraints = input_payload.get("constraints")
            if isinstance(dynamic_constraints, list):
                constraints.extend(dynamic_constraints)

        # 2. Decompose Goal
        plan: PlanTree = engine.decompose(
            goal=self.goal,
            _context=context,
            strategy="auto",
            constraints=constraints
        )

        # 3. Compile Plan to Graph (FlowSpec)
        return self._compile_to_graph(plan)

    def _compile_to_graph(self, plan: PlanTree) -> dict[str, Any]:
        """
        Compiles the PlanTree into a flat list of nodes and edges (simple graph representation),
        tagging immutable nodes as locked.
        """
        graph_nodes = []
        graph_edges = []

        def traverse(node: PlanTree):
             if isinstance(node, AtomicSkill):
                 graph_nodes.append({
                     "id": node.id,
                     "description": node.description,
                     "locked": node.immutable,  # KEY: Transfer immutable flag to locked
                     "tool_ref": node.tool_ref,
                     "params": node.params
                 })
             elif isinstance(node, list):
                 for child in node:
                     if isinstance(child, dict): # Handle legacy Step dicts
                          graph_nodes.append({
                              "id": child.get("id"),
                              "description": child.get("description"),
                              "locked": False, # Legacy steps are mutable by default
                              "tool_ref": child.get("tool_ref"),
                              "params": {}
                          })
                     else:
                          traverse(child)

        traverse(plan)

        # Generate sequential edges for linear execution
        # A real planner might generate branching edges based on plan structure
        for i in range(len(graph_nodes) - 1):
            source = graph_nodes[i]["id"]
            target = graph_nodes[i+1]["id"]
            graph_edges.append({
                "from": source,
                "to": target
            })

        return {"nodes": graph_nodes, "edges": graph_edges}


class SteeringConfig(CoreasonModel):
    """
    Configuration for human steering permissions.
    """

    allow_variable_mutation: bool = Field(False, description="Whether the human can mutate blackboard variables.")
    allowed_targets: list[VariableID] | None = Field(
        None, description="List of variable IDs that can be mutated. If None, all are allowed (if mutation is enabled)."
    )

    @model_validator(mode="after")
    def validate_mutation_permissions(self) -> "SteeringConfig":
        if not self.allow_variable_mutation and self.allowed_targets is not None:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_STEERING,
                message="SteeringConfig defines 'allowed_targets' but 'allow_variable_mutation' is False.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        description="Enable mutation or remove targets.",
                        patch_data=[{"op": "remove", "path": "/allowed_targets"}],
                    ).model_dump()
                },
            )
        if self.allow_variable_mutation and self.allowed_targets is not None and len(self.allowed_targets) == 0:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_STEERING,
                message="allowed_targets cannot be empty when mutation is allowed. Use None to allow all targets.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        description="Set allowed_targets to None or populate it.",
                        patch_data=[{"op": "replace", "path": "/allowed_targets", "value": None}],
                    ).model_dump()
                },
            )
        return self


class HumanNode(Node):
    """
    Human-in-the-Loop interaction node.
    Supports blocking approval, or 'shadow' mode where the agent streams intent
    and proceeds if no signal is received, while 'hijack_only' allows mid-flight plan alteration.
    """

    type: Literal["human"] = "human"
    prompt: str = Field(..., description="Prompt to display to the human.", examples=["Approve this plan?"])
    escalation: EscalationStrategy = Field(..., description="The escalation configuration.")
    input_schema: dict[str, Any] | None = Field(
        None, description="JSON Schema for expected human input.", examples=[{"type": "object"}]
    )
    options: list[str] | None = Field(
        None, description="List of valid options for the human.", examples=[["approve", "reject"]]
    )

    interaction_mode: Annotated[
        Literal["blocking", "shadow", "hijack_only"],
        Field(description="Wait for input vs shadow execution.", examples=["blocking"]),
    ] = "blocking"

    steering_config: SteeringConfig | None = Field(None, description="Configuration for steering permissions.")

    @model_validator(mode="after")
    def validate_interaction_mode(self) -> "HumanNode":
        if self.interaction_mode == "shadow" and (self.input_schema is not None or self.options is not None):
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_SHADOW,
                message="HumanNode in 'shadow' mode cannot have 'input_schema' or 'options'.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Remove 'input_schema' and 'options'.",
                        patch_data=[
                            {"op": "remove", "path": "/input_schema"},
                            {"op": "remove", "path": "/options"},
                        ],
                    ).model_dump()
                },
            )
        if self.interaction_mode == "hijack_only" and self.steering_config is None:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_HUMAN_STEERING,
                message="HumanNode in 'hijack_only' mode requires 'steering_config'.",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        target_node_id=self.id,
                        description="Add 'steering_config'.",
                        patch_data=[
                            {
                                "op": "add",
                                "path": "/steering_config",
                                "value": {"allow_variable_mutation": True},
                            }
                        ],
                    ).model_dump()
                },
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

    # Architecture: Reliability (Partial Failure)
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
    operational_policy: OperationalPolicy | None = Field(
        None, description="Local operational limits. Overrides global Governance limits if set."
    )
    output_variable: VariableID = Field(
        ..., description="Variable to store the aggregated result.", examples=["final_report"]
    )

    @model_validator(mode="after")
    def validate_reducer_requirements(self) -> "SwarmNode":
        if self.reducer_function == "summarize" and not self.aggregator_model:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_SWARM_REDUCER,
                message="SwarmNode with reducer='summarize' requires an 'aggregator_model'.",
                context={
                    "remediation": RemediationAction(
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
                    ).model_dump()
                },
            )
        return self


class PlaceholderNode(Node):
    type: Literal["placeholder"] = "placeholder"
    required_capabilities: CoercibleStringList = Field(
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
    "SteeringConfig",
    "SwarmNode",
    "SwitchNode",
]
