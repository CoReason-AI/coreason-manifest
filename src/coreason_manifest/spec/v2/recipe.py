# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Annotated, Any, Literal

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.spec.common.presentation import NodePresentation
from coreason_manifest.spec.common_base import CoReasonBaseModel
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.evaluation import EvaluationProfile

# ==========================================
# 1. Configuration Schemas (New)
# ==========================================


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


class RecipeNode(CoReasonBaseModel):
    """Base class for all nodes in a Recipe graph."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    id: str = Field(..., description="Unique identifier within the graph.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata (not for UI layout).")
    presentation: NodePresentation | None = Field(None, description="Visual layout and styling metadata.")


class AgentNode(RecipeNode):
    """A node that executes an AI Agent."""

    type: Literal["agent"] = "agent"
    agent_ref: str = Field(..., description="The ID or URI of the Agent Definition to execute.")
    system_prompt_override: str | None = Field(None, description="Context-specific instructions.")
    inputs_map: dict[str, str] = Field(default_factory=dict, description="Mapping parent outputs to agent inputs.")


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

    nodes: list[Annotated[AgentNode | HumanNode | RouterNode | EvaluatorNode, Field(discriminator="type")]] = Field(
        ..., description="List of nodes in the graph."
    )
    edges: list[GraphEdge] = Field(..., description="List of directed edges.")
    entry_point: str = Field(..., description="ID of the start node.")

    @model_validator(mode="after")
    def validate_integrity(self) -> "GraphTopology":
        """Verify graph integrity (entry point exists, no dangling edges)."""
        # 1. Check for duplicate IDs
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            duplicates = {id_ for id_ in ids if ids.count(id_) > 1}
            raise ValueError(f"Duplicate node IDs found: {duplicates}")

        valid_ids = set(ids)

        # 2. Check entry point
        if self.entry_point not in valid_ids:
            raise ValueError(f"Entry point '{self.entry_point}' not found in nodes: {valid_ids}")

        # 2. Check edges
        for edge in self.edges:
            if edge.source not in valid_ids:
                raise ValueError(f"Dangling edge source: {edge.source} -> {edge.target}")
            if edge.target not in valid_ids:
                raise ValueError(f"Dangling edge target: {edge.source} -> {edge.target}")

        return self


class RecipeDefinition(CoReasonBaseModel):
    """Definition of a Recipe (Graph-based Workflow)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    apiVersion: Literal["coreason.ai/v2"] = Field("coreason.ai/v2", description="API Version.")
    kind: Literal["Recipe"] = Field("Recipe", description="Kind of the object.")

    metadata: ManifestMetadata = Field(..., description="Metadata including name and design info.")

    # --- New Components ---
    interface: RecipeInterface = Field(..., description="Input/Output contract.")
    state: StateDefinition | None = Field(None, description="Internal state schema.")
    policy: PolicyConfig | None = Field(None, description="Execution limits and error handling.")
    # ----------------------

    topology: GraphTopology = Field(..., description="The execution graph topology.")
