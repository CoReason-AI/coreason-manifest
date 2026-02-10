# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import logging
from collections import Counter
from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.spec.common.presentation import NodePresentation
from coreason_manifest.spec.common_base import ManifestBaseModel
from coreason_manifest.spec.simulation import SimulationScenario
from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.compliance import ComplianceConfig
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.evaluation import EvaluationProfile
from coreason_manifest.spec.v2.guardrails import GuardrailsConfig
from coreason_manifest.spec.v2.identity import IdentityRequirement
from coreason_manifest.spec.v2.reasoning import ReasoningConfig
from coreason_manifest.spec.v2.resources import ModelSelectionPolicy, RuntimeEnvironment

logger = logging.getLogger(__name__)

# ==========================================
# 1. Configuration Schemas (New)
# ==========================================


class RecipeStatus(StrEnum):
    """Lifecycle status of a Recipe."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RecipeRecommendation(ManifestBaseModel):
    """
    Stores search results from the catalog.

    Attributes:
        ref (str): ID of the candidate.
        score (float): 0.0 - 1.0 score.
        rationale (str): Rationale for the recommendation.
        warnings (list[str]): Warnings if any.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    ref: str = Field(..., description="ID of the candidate.")
    score: float = Field(..., description="0.0 - 1.0 score.")
    rationale: str = Field(..., description="Rationale for the recommendation.")
    warnings: list[str] = Field(default_factory=list, description="Warnings if any.")


class OptimizationIntent(ManifestBaseModel):
    """
    Directives for 'Fork & Improve' workflows (harvested from Foundry).

    Attributes:
        base_ref (str): Parent ID to fork.
        improvement_goal (str): Prompt for the optimizer (e.g., 'Reduce hallucinations').
        strategy (Literal["atomic", "parallel"]): Optimization strategy. (Default: "parallel").
        metric_name (str): The grading function to optimize against (e.g., 'faithfulness', 'json_validity').
            (Default: "exact_match").
        teacher_model (str | None): ID of a stronger model to use for bootstrapping synthetic training data.
        max_demonstrations (int): Maximum number of few-shot examples to learn and inject.
            (Default: 5, Constraint: >= 0).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    base_ref: str = Field(..., description="Parent ID to fork.")
    improvement_goal: str = Field(..., description="Prompt for the optimizer (e.g., 'Reduce hallucinations').")
    strategy: Literal["atomic", "parallel"] = Field("parallel", description="Optimization strategy.")

    # --- New Harvesting Fields ---
    metric_name: str = Field(
        "exact_match",
        description="The grading function to optimize against (e.g., 'faithfulness', 'json_validity').",
    )
    teacher_model: str | None = Field(
        None,
        description="ID of a stronger model to use for bootstrapping synthetic training data (e.g., 'gpt-4-turbo').",
    )
    max_demonstrations: int = Field(5, ge=0, description="Maximum number of few-shot examples to learn and inject.")


class SemanticRef(ManifestBaseModel):
    """
    A semantic reference (placeholder) for an agent or tool.

    Attributes:
        intent (str): The intent description for this placeholder.
        constraints (list[str]): Hard requirements.
        candidates (list[RecipeRecommendation]): AI suggestions.
        optimization (OptimizationIntent | None): Optional directive.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    intent: str = Field(..., description="The intent description for this placeholder.")
    constraints: list[str] = Field(default_factory=list, description="Hard requirements.")
    candidates: list[RecipeRecommendation] = Field(default_factory=list, description="AI suggestions.")
    optimization: OptimizationIntent | None = Field(None, description="Optional directive.")


class RecipeInterface(ManifestBaseModel):
    """
    Defines the Input/Output contract for the Recipe using JSON Schema.

    Attributes:
        inputs (dict[str, Any]): JSON Schema defining the expected input arguments.
        outputs (dict[str, Any]): JSON Schema defining the structure of the final result.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    inputs: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema defining the expected input arguments."
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema defining the structure of the final result."
    )


class StateDefinition(ManifestBaseModel):
    """
    Defines the shared memory (Blackboard) structure and persistence.

    Attributes:
        properties (dict[str, Any]): JSON Schema properties for the shared state variables.
        persistence (Literal["ephemeral", "redis", "postgres"]): How the state should be stored across steps.
            (Default: "ephemeral").
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    properties: dict[str, Any] = Field(..., description="JSON Schema properties for the shared state variables.")
    persistence: Literal["ephemeral", "redis", "postgres"] = Field(
        "ephemeral", description="How the state should be stored across steps."
    )


class ExecutionPriority(IntEnum):
    """Traffic priority for the AI Gateway (Load Shedding)."""

    CRITICAL = 10  # Real-time user interaction (CEO bot)
    HIGH = 8  # Standard synchronous flows
    NORMAL = 5  # Default
    LOW = 2  # Background tasks / Bulk processing
    BATCH = 1  # Overnight jobs


class PolicyConfig(ManifestBaseModel):
    """
    Governance rules for execution limits (harvested from Connect).

    Attributes:
        max_retries (int): Global retry limit for failed steps. (Default: 0).
        timeout_seconds (int | None): Global execution timeout.
        execution_mode (Literal["sequential", "parallel"]): Default execution strategy. (Default: "sequential").
        priority (ExecutionPriority): Traffic priority. Low priority requests may be queued or dropped during high load.
            (Default: NORMAL).
        rate_limit_rpm (int | None): Max requests per minute allowed for this recipe execution. (Constraint: >= 0).
        rate_limit_tpm (int | None): Max tokens per minute allowed (input + output). (Constraint: >= 0).
        caching_enabled (bool): Allow the Gateway to serve cached responses for identical inputs (Semantic Caching).
            (Default: True).
        budget_cap_usd (float | None): Hard limit for estimated token + tool costs. Execution halts if exceeded.
        token_budget (int | None): Max tokens for the assembled prompt. Low-priority contexts will be pruned if
            exceeded.
        sensitive_tools (list[str]): List of tool names that ALWAYS require human confirmation (InteractionConfig
            override).
        allowed_mcp_servers (list[str]): Whitelist of MCP server names this recipe is allowed to access.
        safety_preamble (str | None): Mandatory safety instruction injected into the system prompt.
        legal_disclaimer (str | None): Text that must be appended to the final output.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    max_retries: int = Field(0, description="Global retry limit for failed steps.")
    timeout_seconds: int | None = Field(None, description="Global execution timeout.")
    execution_mode: Literal["sequential", "parallel"] = Field("sequential", description="Default execution strategy.")

    # --- New QoS Fields for AI Gateway ---
    priority: ExecutionPriority = Field(
        ExecutionPriority.NORMAL,
        description="Traffic priority. Low priority requests may be queued or dropped during high load.",
    )

    rate_limit_rpm: int | None = Field(
        None, ge=0, description="Max requests per minute allowed for this recipe execution."
    )

    rate_limit_tpm: int | None = Field(None, ge=0, description="Max tokens per minute allowed (input + output).")

    caching_enabled: bool = Field(
        True,
        description="Allow the Gateway to serve cached responses for identical inputs (Semantic Caching).",
    )

    # --- New Harvesting Fields ---
    budget_cap_usd: float | None = Field(
        None, description="Hard limit for estimated token + tool costs. Execution halts if exceeded."
    )
    token_budget: int | None = Field(
        None,
        description="Max tokens for the assembled prompt. Low-priority contexts will be pruned if exceeded.",
    )
    sensitive_tools: list[str] = Field(
        default_factory=list,
        description="List of tool names that ALWAYS require human confirmation (InteractionConfig override).",
    )
    allowed_mcp_servers: list[str] = Field(
        default_factory=list,
        description="Whitelist of MCP server names this recipe is allowed to access.",
    )

    # --- New Harvesting Fields from Coreason-Protocol ---
    safety_preamble: str | None = Field(
        None, description="Mandatory safety instruction injected into the system prompt."
    )

    legal_disclaimer: str | None = Field(None, description="Text that must be appended to the final output.")


# ==========================================
# 2. Node Definitions
# ==========================================


class TransparencyLevel(StrEnum):
    """Visibility of the node's internal state."""

    OPAQUE = "opaque"
    OBSERVABLE = "observable"
    INTERACTIVE = "interactive"


class InterventionTrigger(StrEnum):
    """When to pause for human intervention."""

    ON_START = "on_start"
    ON_PLAN_GENERATION = "on_plan_generation"
    ON_FAILURE = "on_failure"
    ON_COMPLETION = "on_completion"


class InteractionConfig(ManifestBaseModel):
    """
    Configuration for the Interactive Control Plane.

    Attributes:
        transparency (TransparencyLevel): Visibility level. (Default: OPAQUE).
        triggers (list[InterventionTrigger]): When to pause.
        editable_fields (list[str]): Whitelist of fields modifiable during pause.
        enforce_contract (bool): Validate steered output against original schema. (Default: True).
        guidance_hint (str | None): Hint for the human operator.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    transparency: TransparencyLevel = Field(TransparencyLevel.OPAQUE, description="Visibility level.")
    triggers: list[InterventionTrigger] = Field(default_factory=list, description="When to pause.")
    editable_fields: list[str] = Field(default_factory=list, description="Whitelist of fields modifiable during pause.")
    enforce_contract: bool = Field(True, description="Validate steered output against original schema.")
    guidance_hint: str | None = Field(None, description="Hint for the human operator.")


class VisualizationStyle(StrEnum):
    """How the UI should render the node's running state."""

    CHAT = "chat"
    TREE = "tree"
    KANBAN = "kanban"
    DOCUMENT = "document"


class PresentationHints(ManifestBaseModel):
    """
    Directives for the frontend on how to render the internal reasoning.

    Attributes:
        style (VisualizationStyle): Visualization style. (Default: CHAT).
        display_title (str | None): Human-friendly label override.
        icon (str | None): Icon name/emoji, e.g., 'lucide:brain'.
        hidden_fields (list[str]): Whitelist of internal variables to hide from the non-debug UI.
        progress_indicator (str | None): Name of the context variable to watch for % completion.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    style: VisualizationStyle = Field(VisualizationStyle.CHAT, description="Visualization style.")
    display_title: str | None = Field(None, description="Human-friendly label override.")
    icon: str | None = Field(None, description="Icon name/emoji, e.g., 'lucide:brain'.")
    hidden_fields: list[str] = Field(
        default_factory=list, description="Whitelist of internal variables to hide from the non-debug UI."
    )
    progress_indicator: str | None = Field(None, description="Name of the context variable to watch for % completion.")


class CollaborationMode(StrEnum):
    """The protocol for human engagement."""

    COMPLETION = "completion"
    INTERACTIVE = "interactive"
    CO_EDIT = "co_edit"


class CollaborationConfig(ManifestBaseModel):
    """
    Rules for human-agent engagement (harvested from Human-Layer).

    Attributes:
        mode (CollaborationMode): Engagement mode. (Default: COMPLETION).
        feedback_schema (dict[str, Any] | None): JSON Schema for structured feedback.
        supported_commands (list[str]): Slash commands the agent understands.
        channels (list[str]): Communication channels to notify (e.g., ['slack', 'email', 'mobile_push']).
        timeout_seconds (int | None): How long to wait for human input before triggering fallback.
        fallback_behavior (Literal["fail", "proceed_with_default", "escalate"]): Action to take if the timeout
            is exceeded. (Default: "fail").
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    mode: CollaborationMode = Field(CollaborationMode.COMPLETION, description="Engagement mode.")
    feedback_schema: dict[str, Any] | None = Field(None, description="JSON Schema for structured feedback.")
    supported_commands: list[str] = Field(default_factory=list, description="Slash commands the agent understands.")

    # --- New Harvesting Fields ---
    channels: list[str] = Field(
        default_factory=list,
        description="Communication channels to notify (e.g., ['slack', 'email', 'mobile_push']).",
    )
    timeout_seconds: int | None = Field(
        None, description="How long to wait for human input before triggering fallback."
    )
    fallback_behavior: Literal["fail", "proceed_with_default", "escalate"] = Field(
        "fail", description="Action to take if the timeout is exceeded."
    )


class FailureBehavior(StrEnum):
    """Action to take when a node fails after retries are exhausted."""

    FAIL_WORKFLOW = "fail_workflow"  # Default: Stop everything
    CONTINUE_WITH_DEFAULT = "continue_with_default"  # Use 'default_output'
    ROUTE_TO_FALLBACK = "route_to_fallback"  # Jump to specific node
    IGNORE = "ignore"  # Return None and proceed


class RecoveryConfig(ManifestBaseModel):
    """
    Configuration for node-level resilience (harvested from Maco).

    Attributes:
        max_retries (int | None): Override global retry limit.
        retry_delay_seconds (float): Backoff start. (Default: 1.0).
        behavior (FailureBehavior): Strategy on final failure. (Default: FAIL_WORKFLOW).
        fallback_node_id (str | None): The ID of the node to transition to if behavior is ROUTE_TO_FALLBACK.
        default_output (dict[str, Any] | None): Static payload to return if behavior is CONTINUE_WITH_DEFAULT.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    max_retries: int | None = Field(None, description="Override global retry limit.")
    retry_delay_seconds: float = Field(1.0, description="Backoff start.")

    behavior: FailureBehavior = Field(FailureBehavior.FAIL_WORKFLOW, description="Strategy on final failure.")

    fallback_node_id: str | None = Field(
        None,
        description="The ID of the node to transition to if behavior is ROUTE_TO_FALLBACK.",
    )
    default_output: dict[str, Any] | None = Field(
        None,
        description="Static payload to return if behavior is CONTINUE_WITH_DEFAULT.",
    )


class RecipeNode(ManifestBaseModel):
    """
    Base class for all nodes in a Recipe graph.

    Attributes:
        id (str): Unique identifier within the graph.
        metadata (dict[str, Any]): Custom metadata (not for UI layout).
        presentation (NodePresentation | None): Static visual layout (x, y, color).
        interaction (InteractionConfig | None): Interactive control plane configuration.
        visualization (PresentationHints | None): Dynamic rendering hints (Glass Box).
        collaboration (CollaborationConfig | None): Human engagement rules (Co-Pilot).
        recovery (RecoveryConfig | None): Error handling and resilience settings.
        reasoning (ReasoningConfig | None): Meta-cognition settings: Review loops, gap scanning, and validation
            strategies.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    id: str = Field(..., description="Unique identifier within the graph.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata (not for UI layout).")
    presentation: NodePresentation | None = Field(None, description="Static visual layout (x, y, color).")
    interaction: InteractionConfig | None = Field(None, description="Interactive control plane configuration.")
    visualization: PresentationHints | None = Field(None, description="Dynamic rendering hints (Glass Box).")
    collaboration: CollaborationConfig | None = Field(None, description="Human engagement rules (Co-Pilot).")

    # --- New Field: Flow Governance ---
    recovery: RecoveryConfig | None = Field(None, description="Error handling and resilience settings.")

    # --- New Field for Episteme ---
    reasoning: ReasoningConfig | None = Field(
        None,
        description="Meta-cognition settings: Review loops, gap scanning, and validation strategies.",
    )


class AgentNode(RecipeNode):
    """
    A node that executes an AI Agent.

    Attributes:
        type (Literal["agent"]): Discriminator. (Default: "agent").
        cognitive_profile (CognitiveProfile | None): Inline definition of the agent's cognitive architecture
            (for the Weaver).
        agent_ref (str | SemanticRef | None): The ID or URI of the Agent Definition, or a Semantic Reference.
        model_policy (ModelSelectionPolicy | str | None): The routing policy for the LLM. Can be an inline policy
            or a reference to a Model ID.
        system_prompt_override (str | None): Context-specific instructions.
        inputs_map (dict[str, str]): Mapping parent outputs to agent inputs.
    """

    type: Literal["agent"] = "agent"

    # New Field: Inline Definition
    # If provided, this overrides 'agent_ref' lookup.
    cognitive_profile: CognitiveProfile | None = Field(
        None,
        description="Inline definition of the agent's cognitive architecture (for the Weaver).",
    )

    agent_ref: str | SemanticRef | None = Field(
        None, description="The ID or URI of the Agent Definition, or a Semantic Reference."
    )

    # --- New Field for Arbitrage Support ---
    model_policy: ModelSelectionPolicy | str | None = Field(
        None,
        description="The routing policy for the LLM. Can be an inline policy or a reference to a Model ID.",
    )

    system_prompt_override: str | None = Field(None, description="Context-specific instructions.")
    inputs_map: dict[str, str] = Field(default_factory=dict, description="Mapping parent outputs to agent inputs.")


class SolverStrategy(StrEnum):
    """Defines the algorithmic approach for the Generative Node."""

    STANDARD = "standard"  # Simple Depth-First Decomposition (ROMA)
    TREE_SEARCH = "tree_search"  # MCTS / LATS (Backtracking & Simulation)
    ENSEMBLE = "ensemble"  # SPIO (Parallel generation + Voting)


class SolverConfig(ManifestBaseModel):
    """
    Configuration for the autonomous planning capabilities.

    Attributes:
        strategy (SolverStrategy): The planning strategy to use. (Default: STANDARD).
        depth_limit (int): Hard limit on recursion depth. (Default: 3, Constraint: >= 1).
        n_samples (int): Council size: How many plans to generate. (Default: 1, Constraint: >= 1).
        diversity_threshold (float | None): For Ensemble: Minimum Jaccard distance required between generated plans.
            (Default: 0.3, Constraint: 0.0-1.0).
        enable_dissenter (bool): If True, an adversarial agent will critique plans before voting. (Default: False).
        consensus_threshold (float | None): Percentage of votes required to ratify a plan.
            (Default: 0.6, Constraint: 0.0-1.0).
        beam_width (int): For LATS: How many children to expand per node. (Default: 1, Constraint: >= 1).
        max_iterations (int): For LATS: The 'Search Budget' (total simulations). (Default: 10, Constraint: >= 1).
        aggregation_method (Literal["best_of_n", "majority_vote", "weighted_merge"] | None): How to combine results
            if n_samples > 1.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    strategy: SolverStrategy = Field(SolverStrategy.STANDARD, description="The planning strategy to use.")
    depth_limit: int = Field(3, ge=1, description="Hard limit on recursion depth.")
    # --- Ensemble / Council Configuration (Harvested) ---
    n_samples: int = Field(1, ge=1, description="Council size: How many plans to generate.")

    diversity_threshold: float | None = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="For Ensemble: Minimum Jaccard distance required between generated plans.",
    )

    enable_dissenter: bool = Field(
        False, description="If True, an adversarial agent will critique plans before voting."
    )

    consensus_threshold: float | None = Field(
        0.6, ge=0.0, le=1.0, description="Percentage of votes required to ratify a plan."
    )

    # --- Tree Search Configuration ---
    beam_width: int = Field(1, ge=1, description="For LATS: How many children to expand per node.")
    max_iterations: int = Field(10, ge=1, description="For LATS: The 'Search Budget' (total simulations).")
    aggregation_method: Literal["best_of_n", "majority_vote", "weighted_merge"] | None = Field(
        None, description="How to combine results if n_samples > 1."
    )


class GenerativeNode(RecipeNode):
    """
    A node that acts as an interface definition for dynamic solvers.

    Attributes:
        type (Literal["generative"]): Discriminator. (Default: "generative").
        goal (str): The high-level objective.
        solver (SolverConfig): Configuration for the autonomous planning capabilities.
        allowed_tools (list[str]): Whitelist of Tool IDs the solver is permitted to use.
        output_schema (dict[str, Any]): The contract for the result.
    """

    type: Literal["generative"] = "generative"
    goal: str = Field(..., description="The high-level objective.")
    solver: SolverConfig = Field(
        default_factory=SolverConfig,
        description="Configuration for the autonomous planning capabilities.",
    )
    allowed_tools: list[str] = Field(
        default_factory=list, description="Whitelist of Tool IDs the solver is permitted to use."
    )
    output_schema: dict[str, Any] = Field(..., description="The contract for the result.")


class HumanNode(RecipeNode):
    """
    A node that pauses execution for human input/approval.

    Attributes:
        type (Literal["human"]): Discriminator. (Default: "human").
        prompt (str): Instruction for the human user.
        timeout_seconds (int | None): SLA for approval.
        required_role (str | None): Role required to approve (e.g., manager).
    """

    type: Literal["human"] = "human"
    prompt: str = Field(..., description="Instruction for the human user.")
    timeout_seconds: int | None = Field(None, description="SLA for approval.")
    required_role: str | None = Field(None, description="Role required to approve (e.g., manager).")


class RouterNode(RecipeNode):
    """
    A node that routes execution based on a variable.

    Attributes:
        type (Literal["router"]): Discriminator. (Default: "router").
        input_key (str): The variable to evaluate (e.g., 'classification').
        routes (dict[str, str]): Map of value -> target_node_id.
        default_route (str): Fallback target_node_id.
    """

    type: Literal["router"] = "router"
    input_key: str = Field(..., description="The variable to evaluate (e.g., 'classification').")
    routes: dict[str, str] = Field(..., description="Map of value -> target_node_id.")
    default_route: str = Field(..., description="Fallback target_node_id.")


class EvaluatorNode(RecipeNode):
    """
    A node that evaluates a target variable using an LLM judge.

    Attributes:
        type (Literal["evaluator"]): Discriminator. (Default: "evaluator").
        target_variable (str): The key in the shared state/blackboard containing the content to evaluate.
        evaluator_agent_ref (str): Reference to the Agent Definition ID that will act as the judge.
        evaluation_profile (EvaluationProfile | str): Inline criteria definition or a reference to a preset profile.
        pass_threshold (float): The score, 0.0-1.0, required to proceed.
        max_refinements (int): Maximum number of loops allowed before forcing a generic fail/fallback.
        pass_route (str): Node ID to go to if score >= threshold.
        fail_route (str): Node ID to go to if score < threshold.
        feedback_variable (str): The key in the state where the critique/reasoning will be written.
    """

    type: Literal["evaluator"] = "evaluator"
    target_variable: str = Field(
        ..., description="The key in the shared state/blackboard containing the content to evaluate."
    )
    evaluator_agent_ref: str = Field(
        ..., description="Reference to the Agent Definition ID that will act as the judge."
    )
    evaluation_profile: EvaluationProfile | str = Field(
        ..., description="Inline criteria definition or a reference to a preset profile."
    )
    pass_threshold: float = Field(..., description="The score, 0.0-1.0, required to proceed.")
    max_refinements: int = Field(
        ..., description="Maximum number of loops allowed before forcing a generic fail/fallback."
    )
    pass_route: str = Field(..., description="Node ID to go to if score >= threshold.")
    fail_route: str = Field(..., description="Node ID to go to if score < threshold.")
    feedback_variable: str = Field(
        ..., description="The key in the state where the critique/reasoning will be written."
    )


class GraphEdge(ManifestBaseModel):
    """
    A directed edge between two nodes.

    Attributes:
        source (str): Source Node ID.
        target (str): Target Node ID.
        condition (str | None): Label for visualization (e.g., 'approved').
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    source: str = Field(..., description="Source Node ID.")
    target: str = Field(..., description="Target Node ID.")
    condition: str | None = Field(None, description="Label for visualization (e.g., 'approved').")


class GraphTopology(ManifestBaseModel):
    """
    The directed cyclic graph structure defining the control flow.

    Attributes:
        nodes (list[AgentNode | HumanNode | RouterNode | EvaluatorNode | GenerativeNode]): List of nodes in the graph.
        edges (list[GraphEdge]): List of directed edges.
        entry_point (str): ID of the start node.
        status (Literal["draft", "valid"]): Validation status of the topology. (Default: "valid").

    Validators:
        validate_integrity (@model_validator):
            Verifies graph integrity:
            1. Checks for duplicate node IDs.
            2. If status is 'valid', calls _validate_completeness() to ensure:
                - Entry point exists in nodes.
                - All edges connect existing nodes (no dangling edges).
                - All fallback nodes (from RecoveryConfig) exist.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    nodes: list[
        Annotated[AgentNode | HumanNode | RouterNode | EvaluatorNode | GenerativeNode, Field(discriminator="type")]
    ] = Field(..., description="List of nodes in the graph.")
    edges: list[GraphEdge] = Field(..., description="List of directed edges.")
    entry_point: str = Field(..., description="ID of the start node.")
    status: Literal["draft", "valid"] = Field("valid", description="Validation status of the topology.")

    @model_validator(mode="after")
    def validate_integrity(self) -> "GraphTopology":
        """Verify graph integrity (entry point exists, no dangling edges)."""
        # 1. Check for duplicate IDs
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            counts = Counter(ids)
            duplicates = {id_ for id_, count in counts.items() if count > 1}
            raise ValueError(f"Duplicate node IDs found: {duplicates}")

        # If status is draft, skip semantic checks
        if self.status == "draft":
            return self

        self._validate_completeness()
        return self

    def verify_completeness(self) -> bool:
        """Check if the graph is semantically complete (valid entry point and edges)."""
        try:
            self._validate_completeness()
            return True
        except ValueError:
            return False

    def _validate_completeness(self) -> None:
        """Internal validation logic for entry point and edges."""
        valid_ids = {node.id for node in self.nodes}

        # 2. Check entry point
        if self.entry_point not in valid_ids:
            raise ValueError(f"Entry point '{self.entry_point}' not found in nodes: {valid_ids}")

        # 3. Check edges
        for edge in self.edges:
            if edge.source not in valid_ids:
                raise ValueError(f"Dangling edge source: {edge.source} -> {edge.target}")
            if edge.target not in valid_ids:
                raise ValueError(f"Dangling edge target: {edge.source} -> {edge.target}")

        # 4. Check fallback nodes (Flow Governance)
        for node in self.nodes:
            if (
                node.recovery
                and node.recovery.behavior == FailureBehavior.ROUTE_TO_FALLBACK
                and node.recovery.fallback_node_id
            ):
                fallback_id = node.recovery.fallback_node_id
                if fallback_id not in valid_ids:
                    raise ValueError(
                        f"Invalid fallback_node_id '{fallback_id}' in node '{node.id}': Node not found in graph."
                    )


class TaskSequence(ManifestBaseModel):
    """
    A linear sequence of tasks that simplifies graph creation.

    Attributes:
        steps (list[AgentNode | ...]): Ordered list of steps to execute. (Constraint: Min length 1).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    steps: list[
        Annotated[AgentNode | HumanNode | RouterNode | EvaluatorNode | GenerativeNode, Field(discriminator="type")]
    ] = Field(..., min_length=1, description="Ordered list of steps to execute.")

    def to_graph(self) -> GraphTopology:
        """Compiles the sequence into a GraphTopology."""
        nodes = self.steps
        edges = [GraphEdge(source=nodes[i].id, target=nodes[i + 1].id) for i in range(len(nodes) - 1)]

        return GraphTopology(nodes=nodes, edges=edges, entry_point=nodes[0].id)


class Constraint(ManifestBaseModel):
    """
    Represents a feasibility constraint for a Recipe.

    Attributes:
        variable (str): The context variable path to check (e.g., 'data.row_count').
        operator (Literal["eq", "neq", "gt", "gte", "lt", "lte", "in", "contains"]): Comparison operator.
        value (Any): The threshold or reference value.
        required (bool): If True, failure halts execution. If False, it's a warning. (Default: True).
        error_message (str | None): Custom error message to display on failure.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    variable: str = Field(..., description="The context variable path to check (e.g., 'data.row_count').")
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "in", "contains"] = Field(
        ..., description="Comparison operator."
    )
    value: Any = Field(..., description="The threshold or reference value.")
    required: bool = Field(True, description="If True, failure halts execution. If False, it's a warning.")
    error_message: str | None = Field(None, description="Custom error message to display on failure.")

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate the constraint against the given context."""
        # 1. Resolve Path
        current = context
        for part in self.variable.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Path not found
                return False

        resolved_value = current

        # 2. Compare
        try:
            if self.operator == "eq":
                return bool(resolved_value == self.value)
            if self.operator == "neq":
                return bool(resolved_value != self.value)
            if self.operator == "gt":
                return bool(resolved_value > self.value)
            if self.operator == "gte":
                return bool(resolved_value >= self.value)
            if self.operator == "lt":
                return bool(resolved_value < self.value)
            if self.operator == "lte":
                return bool(resolved_value <= self.value)
            if self.operator == "in":
                return bool(resolved_value in self.value)
            if self.operator == "contains":
                return bool(self.value in resolved_value)

            return False  # pragma: no cover
        except TypeError:
            # Type mismatch (e.g., comparing str > int)
            return False


class RecipeDefinition(ManifestBaseModel):
    """
    Definition of a Recipe (Graph-based Workflow).

    Attributes:
        apiVersion (Literal["coreason.ai/v2"]): API Version. (Default: "coreason.ai/v2").
        kind (Literal["Recipe"]): Kind of the object. (Default: "Recipe").
        metadata (ManifestMetadata): Metadata including name and design info.
        status (RecipeStatus): Lifecycle state. 'published' enforces strict validation. (Default: DRAFT).
        interface (RecipeInterface): Input/Output contract.
        environment (RuntimeEnvironment | None): The infrastructure requirements for the recipe.
        default_model_policy (ModelSelectionPolicy | None): Default model selection rules for all agents in this recipe.
        tests (list[SimulationScenario]): Self-contained test scenarios (harvested from Simulacrum) to validate
            this recipe.
        requirements (list[Constraint]): List of feasibility constraints.
        state (StateDefinition | None): Internal state schema.
        policy (PolicyConfig | None): Execution limits and error handling.
        compliance (ComplianceConfig | None): Directives for the Auditor worker (logging, retention, signing).
        identity (IdentityRequirement | None): Access control and user context injection rules.
        guardrails (GuardrailsConfig | None): Active defense rules (Circuit Breakers, Drift, Spot Checks).
        topology (Annotated[GraphTopology, BeforeValidator(coerce_topology)]): The execution graph topology.
            (Validation: Applies `coerce_topology` before parsing).

    Validators:
        validate_topology_integrity (@model_validator):
            Ensures all `recovery.fallback_node_id` references point to existing Node IDs.
        enforce_lifecycle_constraints (@model_validator):
            If status is PUBLISHED:
            - Rejects abstract nodes (SemanticRef).
            - Rejects incomplete nodes (missing cognitive_profile or agent_ref).
            - Enforces strict graph integrity (no dangling edges).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    apiVersion: Literal["coreason.ai/v2"] = Field("coreason.ai/v2", description="API Version.")  # noqa: N815
    kind: Literal["Recipe"] = Field("Recipe", description="Kind of the object.")

    metadata: ManifestMetadata = Field(..., description="Metadata including name and design info.")

    status: RecipeStatus = Field(
        default=RecipeStatus.DRAFT, description="Lifecycle state. 'published' enforces strict validation."
    )

    # --- New Components ---
    interface: RecipeInterface = Field(..., description="Input/Output contract.")
    environment: RuntimeEnvironment | None = Field(None, description="The infrastructure requirements for the recipe.")

    # --- New Field for Global Default ---
    default_model_policy: ModelSelectionPolicy | None = Field(
        None, description="Default model selection rules for all agents in this recipe."
    )

    # --- New Harvesting Field ---
    tests: list[SimulationScenario] = Field(
        default_factory=list,
        description="Self-contained test scenarios (harvested from Simulacrum) to validate this recipe.",
    )

    requirements: list[Constraint] = Field(default_factory=list, description="List of feasibility constraints.")
    state: StateDefinition | None = Field(None, description="Internal state schema.")
    policy: PolicyConfig | None = Field(None, description="Execution limits and error handling.")
    # ----------------------

    # --- New Field for Auditor Support ---
    compliance: ComplianceConfig | None = Field(
        None, description="Directives for the Auditor worker (logging, retention, signing)."
    )

    # --- New Field for Identity ---
    identity: IdentityRequirement | None = Field(
        None,
        description="Access control and user context injection rules.",
    )

    # --- New Field for Sentinel ---
    guardrails: GuardrailsConfig | None = Field(
        None,
        description="Active defense rules (Circuit Breakers, Drift, Spot Checks).",
    )

    topology: GraphTopology = Field(..., description="The execution graph topology.")

    @model_validator(mode="after")
    def validate_topology_integrity(self) -> Self:
        """
        Harvested from coreason-validator.
        Ensures all node references (e.g. recovery fallbacks) point to existing Node IDs.
        """
        # 1. Collect all valid Node IDs
        if not self.topology.nodes:
            return self

        valid_node_ids = {node.id for node in self.topology.nodes}

        # 2. Iterate through all nodes to check their outgoing references
        errors = []
        for node in self.topology.nodes:
            # Check Recovery Fallback existence
            if node.recovery and node.recovery.fallback_node_id:
                target_id = node.recovery.fallback_node_id
                if target_id not in valid_node_ids:
                    errors.append(
                        f"Node '{node.id}' defines fallback_node_id='{target_id}', "
                        f"but '{target_id}' does not exist in the recipe."
                    )

            # Future proofing: If you add explicit 'next_step' fields later, add checks here.

        if errors:
            raise ValueError(f"Topology Integrity Error: {'; '.join(errors)}")

        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "RecipeDefinition":
        """
        Lifecycle Guardrail:
        - DRAFT: Allows SemanticRefs and partial graphs.
        - PUBLISHED: Requires concrete IDs and valid graph.
        """
        if self.status == RecipeStatus.PUBLISHED:
            # 1. Enforce Concrete Resolution and Complete Definition
            abstract_nodes = []
            incomplete_nodes = []
            for node in self.topology.nodes:
                if isinstance(node, AgentNode):
                    if isinstance(node.agent_ref, SemanticRef):
                        abstract_nodes.append(node.id)
                    elif not node.agent_ref and not node.cognitive_profile:
                        incomplete_nodes.append(node.id)

            if abstract_nodes:
                raise ValueError(
                    f"Lifecycle Error: Nodes {abstract_nodes} are still abstract. "
                    "Resolve all SemanticRefs to concrete IDs before publishing."
                )

            if incomplete_nodes:
                raise ValueError(
                    f"Lifecycle Error: Nodes {incomplete_nodes} are incomplete. "
                    "Must provide either 'agent_ref' or 'cognitive_profile' before publishing."
                )

            # 2. Enforce Graph Integrity
            if not self.topology.verify_completeness():
                raise ValueError(
                    "Lifecycle Error: Topology is structurally invalid (dangling edges or missing entry). "
                    "Fix graph integrity before publishing."
                )

        return self

    def check_feasibility(self, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Check if all required constraints are satisfied."""
        errors = []
        is_feasible = True

        for constraint in self.requirements:
            if not constraint.evaluate(context):
                msg = (
                    constraint.error_message
                    or f"Constraint failed: {constraint.variable} {constraint.operator} {constraint.value}"
                )
                if constraint.required:
                    is_feasible = False
                    errors.append(msg)
                else:
                    logger.warning(f"Optional constraint warning: {msg}")

        return is_feasible, errors
