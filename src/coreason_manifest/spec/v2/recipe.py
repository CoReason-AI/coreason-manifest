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
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, ConfigDict, Field, model_validator

from coreason_manifest.spec.common.presentation import NodePresentation
from coreason_manifest.spec.common_base import CoReasonBaseModel
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.evaluation import EvaluationProfile

logger = logging.getLogger(__name__)

# ==========================================
# 1. Configuration Schemas (New)
# ==========================================


class RecipeStatus(StrEnum):
    """Lifecycle status of a Recipe."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RecipeRecommendation(CoReasonBaseModel):
    """Stores search results from the catalog."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    ref: str = Field(..., description="ID of the candidate.")
    score: float = Field(..., description="0.0 - 1.0 score.")
    rationale: str = Field(..., description="Rationale for the recommendation.")
    warnings: list[str] = Field(default_factory=list, description="Warnings if any.")


class OptimizationIntent(CoReasonBaseModel):
    """Directives for 'Fork & Improve' workflows."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    base_ref: str = Field(..., description="Parent ID to fork.")
    improvement_goal: str = Field(..., description="Prompt for the optimizer.")
    strategy: Literal["atomic", "parallel"] = Field("parallel", description="Strategy for improvement.")


class SemanticRef(CoReasonBaseModel):
    """A semantic reference (placeholder) for an agent or tool."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    intent: str = Field(..., description="The intent description for this placeholder.")
    constraints: list[str] = Field(default_factory=list, description="Hard requirements.")
    candidates: list[RecipeRecommendation] = Field(default_factory=list, description="AI suggestions.")
    optimization: OptimizationIntent | None = Field(None, description="Optional directive.")


class RecipeInterface(CoReasonBaseModel):
    """Defines the Input/Output contract for the Recipe using JSON Schema."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    inputs: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema defining the expected input arguments."
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema defining the structure of the final result."
    )


class StateDefinition(CoReasonBaseModel):
    """Defines the shared memory (Blackboard) structure and persistence."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    properties: dict[str, Any] = Field(..., description="JSON Schema properties for the shared state variables.")
    persistence: Literal["ephemeral", "redis", "postgres"] = Field(
        "ephemeral", description="How the state should be stored across steps."
    )


class PolicyConfig(CoReasonBaseModel):
    """Governance rules for execution limits and error handling."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    max_retries: int = Field(0, description="Global retry limit for failed steps.")
    timeout_seconds: int | None = Field(None, description="Global execution timeout.")
    execution_mode: Literal["sequential", "parallel"] = Field(
        "sequential", description="Default execution strategy for independent branches."
    )


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


class InteractionConfig(CoReasonBaseModel):
    """Configuration for the Interactive Control Plane."""

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


class PresentationHints(CoReasonBaseModel):
    """Directives for the frontend on how to render the internal reasoning."""

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


class CollaborationConfig(CoReasonBaseModel):
    """Rules for human-agent engagement."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    mode: CollaborationMode = Field(CollaborationMode.COMPLETION, description="Engagement mode.")
    feedback_schema: dict[str, Any] | None = Field(None, description="JSON Schema for structured feedback.")
    supported_commands: list[str] = Field(default_factory=list, description="Slash commands the agent understands.")


class RecipeNode(CoReasonBaseModel):
    """Base class for all nodes in a Recipe graph."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    id: str = Field(..., description="Unique identifier within the graph.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata (not for UI layout).")
    presentation: NodePresentation | None = Field(None, description="Static visual layout (x, y, color).")
    interaction: InteractionConfig | None = Field(None, description="Interactive control plane configuration.")
    visualization: PresentationHints | None = Field(None, description="Dynamic rendering hints (Glass Box).")
    collaboration: CollaborationConfig | None = Field(None, description="Human engagement rules (Co-Pilot).")


class AgentNode(RecipeNode):
    """A node that executes an AI Agent."""

    type: Literal["agent"] = "agent"
    agent_ref: str | SemanticRef = Field(
        ..., description="The ID or URI of the Agent Definition, or a Semantic Reference."
    )
    system_prompt_override: str | None = Field(None, description="Context-specific instructions.")
    inputs_map: dict[str, str] = Field(default_factory=dict, description="Mapping parent outputs to agent inputs.")


class SolverStrategy(StrEnum):
    """Defines the algorithmic approach for the Generative Node."""

    STANDARD = "standard"  # Simple Depth-First Decomposition (ROMA)
    TREE_SEARCH = "tree_search"  # MCTS / LATS (Backtracking & Simulation)
    ENSEMBLE = "ensemble"  # SPIO (Parallel generation + Voting)


class SolverConfig(CoReasonBaseModel):
    """Configuration for the autonomous planning capabilities."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    strategy: SolverStrategy = Field(SolverStrategy.STANDARD, description="The planning strategy to use.")
    depth_limit: int = Field(3, ge=1, description="Hard limit on recursion depth.")
    n_samples: int = Field(1, ge=1, description="For SPIO: How many distinct plans to generate in parallel.")
    beam_width: int = Field(1, ge=1, description="For LATS: How many children to expand per node.")
    max_iterations: int = Field(10, ge=1, description="For LATS: The 'Search Budget' (total simulations).")
    aggregation_method: Literal["best_of_n", "majority_vote", "weighted_merge"] | None = Field(
        None, description="How to combine results if n_samples > 1 (SPIO-E logic)."
    )


class GenerativeNode(RecipeNode):
    """A node that acts as an interface definition for dynamic solvers."""

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
    """A node that pauses execution for human input/approval."""

    type: Literal["human"] = "human"
    prompt: str = Field(..., description="Instruction for the human user.")
    timeout_seconds: int | None = Field(None, description="SLA for approval.")
    required_role: str | None = Field(None, description="Role required to approve (e.g., manager).")


class RouterNode(RecipeNode):
    """A node that routes execution based on a variable."""

    type: Literal["router"] = "router"
    input_key: str = Field(..., description="The variable to evaluate (e.g., 'classification').")
    routes: dict[str, str] = Field(..., description="Map of value -> target_node_id.")
    default_route: str = Field(..., description="Fallback target_node_id.")


class EvaluatorNode(RecipeNode):
    """A node that evaluates a target variable using an LLM judge."""

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


class GraphEdge(CoReasonBaseModel):
    """A directed edge between two nodes."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    source: str = Field(..., description="Source Node ID.")
    target: str = Field(..., description="Target Node ID.")
    condition: str | None = Field(None, description="Label for visualization (e.g., 'approved').")


class GraphTopology(CoReasonBaseModel):
    """The directed cyclic graph structure defining the control flow."""

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
            duplicates = {id_ for id_ in ids if ids.count(id_) > 1}
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


class TaskSequence(CoReasonBaseModel):
    """A linear sequence of tasks that simplifies graph creation."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    steps: list[
        Annotated[AgentNode | HumanNode | RouterNode | EvaluatorNode | GenerativeNode, Field(discriminator="type")]
    ] = Field(..., min_length=1, description="Ordered list of steps to execute.")

    def to_graph(self) -> GraphTopology:
        """Compiles the sequence into a GraphTopology."""
        nodes = self.steps
        edges = []

        for i in range(len(nodes) - 1):
            edges.append(GraphEdge(source=nodes[i].id, target=nodes[i + 1].id))

        return GraphTopology(nodes=nodes, edges=edges, entry_point=nodes[0].id)


def coerce_topology(v: Any) -> Any:
    """Coerce linear lists or TaskSequence dicts into GraphTopology."""
    # 1. If topology is a list (simplification), treat as steps
    if isinstance(v, list):
        return TaskSequence(steps=v).to_graph()

    # 2. If topology is a dict
    if isinstance(v, dict) and "steps" in v and "nodes" not in v:
        # If it has "steps", treat as TaskSequence
        return TaskSequence.model_validate(v).to_graph()
    # Otherwise assume it's GraphTopology structure, let Pydantic handle it

    return v


class Constraint(CoReasonBaseModel):
    """Represents a feasibility constraint for a Recipe."""

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


class RecipeDefinition(CoReasonBaseModel):
    """Definition of a Recipe (Graph-based Workflow)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    apiVersion: Literal["coreason.ai/v2"] = Field("coreason.ai/v2", description="API Version.")
    kind: Literal["Recipe"] = Field("Recipe", description="Kind of the object.")

    metadata: ManifestMetadata = Field(..., description="Metadata including name and design info.")

    status: RecipeStatus = Field(
        default=RecipeStatus.DRAFT, description="Lifecycle state. 'published' enforces strict validation."
    )

    # --- New Components ---
    interface: RecipeInterface = Field(..., description="Input/Output contract.")
    requirements: list[Constraint] = Field(default_factory=list, description="List of feasibility constraints.")
    state: StateDefinition | None = Field(None, description="Internal state schema.")
    policy: PolicyConfig | None = Field(None, description="Execution limits and error handling.")
    # ----------------------

    topology: Annotated[GraphTopology, BeforeValidator(coerce_topology)] = Field(
        ..., description="The execution graph topology."
    )

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "RecipeDefinition":
        """
        Lifecycle Guardrail:
        - DRAFT: Allows SemanticRefs and partial graphs.
        - PUBLISHED: Requires concrete IDs and valid graph.
        """
        if self.status == RecipeStatus.PUBLISHED:
            # 1. Enforce Concrete Resolution
            abstract_nodes = []
            for node in self.topology.nodes:
                if isinstance(node, AgentNode) and isinstance(node.agent_ref, SemanticRef):
                    abstract_nodes.append(node.id)

            if abstract_nodes:
                raise ValueError(
                    f"Lifecycle Error: Nodes {abstract_nodes} are still abstract. "
                    "Resolve all SemanticRefs to concrete IDs before publishing."
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
