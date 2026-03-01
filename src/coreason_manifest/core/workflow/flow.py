import ast
from typing import Any, Literal
from uuid import uuid4

import jsonschema  # type: ignore[import-untyped]
from jsonschema.exceptions import SchemaError  # type: ignore[import-untyped]
from pydantic import ConfigDict, Field, field_validator, model_validator

from coreason_manifest.core.common.semantic import SemanticRef
from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.compliance import RemediationAction, SecurityVisitor
from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.oversight.governance import Governance
from coreason_manifest.core.primitives.types import MiddlewareDef, MiddlewareID, NodeID
from coreason_manifest.core.state.persistence import PersistenceConfig
from coreason_manifest.core.state.tools import AnyTool, ToolPack
from coreason_manifest.core.workflow.nodes import (
    AnyNode,
)

# Export AnyNode so it can be imported from here as well
__all__ = [
    "AgentRequest",
    "AnyNode",
    "Blackboard",
    "DataSchema",
    "Edge",
    "FlowDefinitions",
    "FlowInterface",
    "FlowMetadata",
    "Graph",
    "GraphFlow",
    "LinearFlow",
    "VariableDef",
]


class FlowMetadata(CoreasonModel):
    name: str = Field(..., description="The name of the flow.", examples=["customer_onboarding_flow"])
    version: str = Field(..., description="The semantic version of the flow.", examples=["1.0.0"])
    description: str | None = Field(
        default=None, description="A description of the flow's purpose.", examples=["Flow to onboard new customers."]
    )
    tags: list[str] = Field(
        default_factory=list,
        description="A list of tags for categorizing the flow.",
        examples=[["onboarding", "customer"]],
    )
    created_at: str | None = Field(
        default=None, description="The ISO-8601 timestamp when the flow was created.", examples=["2025-01-01T00:00:00Z"]
    )
    updated_at: str | None = Field(
        default=None,
        description="The ISO-8601 timestamp when the flow was last updated.",
        examples=["2025-01-02T00:00:00Z"],
    )


class DataSchema(CoreasonModel):
    # Compatibility: Field is 'json_schema' to avoid shadowing BaseModel.schema
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="The unique identifier for the schema.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    json_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="The JSON schema definition.",
        examples=[{"type": "object", "properties": {"name": {"type": "string"}}}],
    )

    @model_validator(mode="after")
    def validate_schema_validity(self) -> "DataSchema":
        try:
            jsonschema.validators.validator_for(self.json_schema).check_schema(self.json_schema)
        except SchemaError as e:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_SCHEMA_INVALID,
                message=f"Invalid JSON Schema definition: {e.message}",
                context={
                    "remediation": RemediationAction(
                        type="update_field",
                        description="Correct the JSON Schema syntax.",
                        patch_data=[{"op": "replace", "path": "/json_schema", "value": {}}],
                    ).model_dump()
                },
            ) from e
        return self


class Blackboard(CoreasonModel):
    variables: dict[str, Any] = Field(
        default_factory=dict, description="The variables stored in the blackboard.", examples=[{"customer_id": "12345"}]
    )
    schemas: list[DataSchema] = Field(
        default_factory=list,
        description="The schemas available on the blackboard.",
        examples=[
            [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "json_schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                }
            ]
        ],
    )
    persistence: PersistenceConfig | None = Field(
        default=None,
        description="The persistence configuration for the blackboard state.",
        examples=[{"backend_type": "redis", "ttl_seconds": 3600}],
    )


class Edge(CoreasonModel):
    from_node: NodeID = Field(..., description="The ID of the source node.", examples=["node_a"])
    to_node: NodeID = Field(..., description="The ID of the target node.", examples=["node_b"])
    condition: str | None = Field(
        default=None,
        description="A python expression string evaluated to determine if the edge should be traversed.",
        examples=["x > 10"],
    )
    cost_weight: float = Field(
        0.0, ge=0.0, description="Estimated financial cost (USD) to traverse this edge.", examples=[0.05]
    )
    latency_weight_ms: float = Field(0.0, ge=0.0, description="Estimated latency in milliseconds.", examples=[150.0])

    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition_ast(cls, v: str | None) -> str | None:
        if not v:
            return v

        try:
            tree = ast.parse(v, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in condition: {e}") from e  # pragma: no cover
        visitor = SecurityVisitor()
        visitor.visit(tree)
        return v


class Graph(CoreasonModel):
    nodes: dict[str, AnyNode] = Field(
        ...,
        description="A dictionary of nodes in the graph, keyed by their ID.",
        examples=[{"node_a": {"id": "node_a", "type": "agent"}}],
    )
    edges: list[Edge] = Field(
        ...,
        description="A list of edges connecting the nodes.",
        examples=[[{"from_node": "node_a", "to_node": "node_b", "cost_weight": 0.0, "latency_weight_ms": 0.0}]],
    )
    entry_point: NodeID | None = Field(
        default=None, description="The ID of the entry node for the graph.", examples=["node_a"]
    )

    @model_validator(mode="after")
    def validate_graph_structure(self) -> "Graph":
        valid_ids = set(self.nodes.keys())

        if not self.nodes:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_EMPTY,
                message="Graph must contain at least one node.",
            )

        # ID Mismatch
        for key, node in self.nodes.items():
            if key != node.id:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_ID_MISMATCH,
                    message=f"Node key '{key}' does not match Node ID '{node.id}'.",
                )

        # Entry Point
        if self.entry_point and self.entry_point not in valid_ids:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_MISSING_ENTRY,
                message=f"Entry point '{self.entry_point}' not found in nodes.",
            )

        # Edges
        for edge in self.edges:
            if edge.from_node not in valid_ids:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_DANGLING_EDGE,
                    message=f"Source '{edge.from_node}' not found in graph nodes.",
                )
            if edge.to_node not in valid_ids:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_DANGLING_EDGE,
                    message=f"Target '{edge.to_node}' not found in graph nodes.",
                )

        # Cycle Detection
        adj_map: dict[str, set[str]] = {n: set() for n in valid_ids}
        for edge in self.edges:
            adj_map[edge.from_node].add(edge.to_node)

        def has_cycle(v: str, visited: set[str], rec_stack: set[str]) -> bool:
            visited.add(v)
            rec_stack.add(v)
            for neighbor in adj_map.get(v, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(v)
            return False

        visited: set[str] = set()
        rec_stack: set[str] = set()
        for node in valid_ids:
            if node not in visited and has_cycle(node, visited, rec_stack):
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_CYCLE,
                    message="Execution graphs must be strict Directed Acyclic Graphs (DAGs). Cycle detected.",
                )

        return self


class FlowInterface(CoreasonModel):
    inputs: dict[str, Any] | DataSchema = Field(
        default_factory=dict, description="The expected inputs for the flow.", examples=[{"user_id": "123"}]
    )
    outputs: dict[str, Any] | DataSchema = Field(
        default_factory=dict, description="The expected outputs from the flow.", examples=[{"status": "success"}]
    )


class FlowDefinitions(CoreasonModel):
    profiles: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent profiles available in the flow.",
        examples=[{"sales_agent": {"role": "sales"}}],
    )
    schemas: dict[str, Any] = Field(
        default_factory=dict,
        description="Schemas referenced in the flow.",
        examples=[{"customer_schema": {"type": "object"}}],
    )
    tools: dict[str, AnyTool] = Field(
        default_factory=dict,
        description="Tools available to agents in the flow.",
        examples=[{"search_tool": {"id": "search", "name": "search", "description": "Search the web"}}],
    )
    tool_packs: dict[str, ToolPack] = Field(
        default_factory=dict,
        description="Tool packs available in the flow.",
        examples=[{"research_pack": {"tools": ["search_tool"]}}],
    )
    skills: dict[str, Any] = Field(
        default_factory=dict,
        description="Skills available to agents.",
        examples=[{"negotiation": {"level": "advanced"}}],
    )
    middlewares: dict[MiddlewareID, MiddlewareDef] = Field(
        default_factory=dict,
        description="Middlewares defined for the flow.",
        examples=[{"logger": {"id": "logger", "type": "logging"}}],
    )
    supervision_templates: Any | None = Field(
        default=None, description="Supervision templates for oversight.", examples=[{"approval": {"type": "human"}}]
    )


class VariableDef(CoreasonModel):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="The unique identifier for the variable definition.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    type: str = Field(..., description="The type of the variable.", examples=["string"])
    description: str | None = Field(
        default=None, description="A description of the variable.", examples=["The user's first name."]
    )


class GraphFlow(CoreasonModel):
    """
    Standard graph-based execution flow.
    """

    type: Literal["graph"] = Field("graph", description="The flow type.", examples=["graph"])
    kind: Literal["GraphFlow"] = Field(
        "GraphFlow", description="The kind of the flow manifest.", examples=["GraphFlow"]
    )
    status: Literal["draft", "published", "archived"] = Field(
        "draft", description="The publication status of the flow.", examples=["published"]
    )
    metadata: FlowMetadata = Field(
        ...,
        description="Metadata describing the flow.",
        examples=[
            {
                "name": "sales_flow",
                "version": "1.0.0",
                "description": "Flow for sales",
                "tags": [],
                "created_at": None,
                "updated_at": None,
            }
        ],
    )
    interface: FlowInterface = Field(
        ..., description="The input/output interface of the flow.", examples=[{"inputs": {}, "outputs": {}}]
    )
    governance: Governance | None = Field(
        default=None,
        description="Governance policies applied to the flow.",
        examples=[{"operational_policy": {"max_cost_usd": 10.0}}],
    )
    blackboard: Blackboard | None = Field(
        default_factory=Blackboard,
        description="The blackboard state for the flow.",
        examples=[{"variables": {}, "schemas": [], "persistence": None}],
    )
    definitions: FlowDefinitions | None = Field(
        default=None,
        description="Definitions for components used in the flow.",
        examples=[
            {
                "profiles": {},
                "schemas": {},
                "tools": {},
                "tool_packs": {},
                "skills": {},
                "middlewares": {},
                "supervision_templates": None,
            }
        ],
    )
    graph: Graph = Field(
        ...,
        description="The execution graph topology.",
        examples=[{"nodes": {"n1": {"id": "n1", "type": "agent"}}, "edges": [], "entry_point": "n1"}],
    )

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "GraphFlow":
        if self.status != "published":
            return self
        for node in self.graph.nodes.values():
            if node.type == "placeholder":
                raise ValueError("Cannot publish a flow with placeholder nodes")
        if self.graph.entry_point is None:
            raise ValueError("Cannot publish a GraphFlow without an entry point")
        return self

    @model_validator(mode="after")
    def enforce_aot_compilation(self) -> "GraphFlow":
        if self.status == "published":
            unresolved = [
                str(getattr(node, "id", ""))
                for node in self.graph.nodes.values()
                if getattr(node, "type", None) == "agent"
                and (
                    isinstance(getattr(node, "profile", None), SemanticRef)
                    or isinstance(getattr(node, "tools", None), SemanticRef)
                )
            ]
            if unresolved:
                msg = (
                    f"Lifecycle Violation: Cannot publish graph. Nodes [{','.join(unresolved)}] "
                    "contain unresolved SemanticRefs. A Weaver must compile this graph into "
                    "concrete profiles before publication."
                )
                raise ManifestError.critical_halt(code=ManifestErrorCode.CRSN_VAL_LIFECYCLE_UNRESOLVED, message=msg)
        return self


class LinearFlow(CoreasonModel):
    """
    Simplified linear execution flow (sequence of steps).
    """

    type: Literal["linear"] = Field("linear", description="The flow type.", examples=["linear"])
    kind: Literal["LinearFlow"] = Field(
        "LinearFlow", description="The kind of the flow manifest.", examples=["LinearFlow"]
    )
    status: Literal["draft", "published", "archived"] = Field(
        "draft", description="The publication status of the flow.", examples=["draft"]
    )
    metadata: FlowMetadata = Field(
        ...,
        description="Metadata describing the flow.",
        examples=[
            {
                "name": "simple_linear",
                "version": "1.0.0",
                "description": "A simple sequence of steps",
                "tags": [],
                "created_at": None,
                "updated_at": None,
            }
        ],
    )
    steps: list[AnyNode] = Field(
        default_factory=list,
        description="An ordered list of nodes to execute sequentially.",
        examples=[[{"id": "step_1", "type": "agent"}]],
    )
    governance: Governance | None = Field(
        default=None,
        description="Governance policies applied to the flow.",
        examples=[{"operational_policy": {"max_cost_usd": 10.0}}],
    )
    definitions: FlowDefinitions | None = Field(
        default=None,
        description="Definitions for components used in the flow.",
        examples=[
            {
                "profiles": {},
                "schemas": {},
                "tools": {},
                "tool_packs": {},
                "skills": {},
                "middlewares": {},
                "supervision_templates": None,
            }
        ],
    )

    @model_validator(mode="after")
    def validate_linear_structure(self) -> "LinearFlow":
        if not self.steps:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_LINEAR_EMPTY,
                message="Sequence cannot be empty.",
            )

        seen = set()
        for step in self.steps:
            if step.id in seen:
                raise ManifestError.critical_halt(
                    code=ManifestErrorCode.CRSN_VAL_TOPOLOGY_NODE_ID_COLLISION,
                    message=f"Duplicate Node ID '{step.id}' found.",
                )
            seen.add(step.id)

        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "LinearFlow":
        if self.status != "published":
            return self
        for node in self.steps:
            if node.type == "placeholder":
                raise ValueError("Cannot publish a flow with placeholder nodes")
        return self

    @model_validator(mode="after")
    def enforce_aot_compilation(self) -> "LinearFlow":
        if self.status == "published":
            unresolved = [
                str(getattr(node, "id", ""))
                for node in self.steps
                if getattr(node, "type", None) == "agent"
                and (
                    isinstance(getattr(node, "profile", None), SemanticRef)
                    or isinstance(getattr(node, "tools", None), SemanticRef)
                )
            ]
            if unresolved:
                msg = (
                    f"Lifecycle Violation: Cannot publish linear flow. Nodes [{','.join(unresolved)}] "
                    "contain unresolved SemanticRefs. A Weaver must compile this linear flow into "
                    "concrete profiles before publication."
                )
                raise ManifestError.critical_halt(code=ManifestErrorCode.CRSN_VAL_LIFECYCLE_UNRESOLVED, message=msg)
        return self


class AgentRequest(CoreasonModel):
    """
    Strict envelope for agent execution requests.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    manifest: GraphFlow | LinearFlow = Field(
        ...,
        description="The flow manifest detailing the execution logic.",
        examples=[
            {
                "type": "linear",
                "kind": "LinearFlow",
                "status": "draft",
                "metadata": {"name": "f", "version": "1"},
                "steps": [],
                "interface": {"inputs": {}, "outputs": {}},
            }
        ],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context or metadata for the request.",
        examples=[{"client_id": "abc-123"}],
    )
