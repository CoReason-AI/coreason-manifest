import ast
from typing import Any, Literal
from uuid import uuid4

import jsonschema  # type: ignore[import-untyped]
from jsonschema.exceptions import SchemaError  # type: ignore[import-untyped]
from pydantic import ConfigDict, Field, field_validator, model_validator

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
        default_factory=list, description="A list of tags for categorization.", examples=[["onboarding", "customer"]]
    )
    created_at: str | None = Field(
        default=None, description="The creation timestamp of the flow.", examples=["2023-10-27T10:00:00Z"]
    )
    updated_at: str | None = Field(
        default=None, description="The last update timestamp of the flow.", examples=["2023-10-27T11:00:00Z"]
    )


class DataSchema(CoreasonModel):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="The unique identifier for the schema.",
        examples=["schema-1234"],
    )
    json_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="The JSON Schema definition to be validated.",
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
        default_factory=dict, description="A collection of variables.", examples=[{"user_id": "u123", "score": 85.5}]
    )
    schemas: list[DataSchema] = Field(
        default_factory=list,
        description="A list of schemas for validation.",
        examples=[[{"id": "schema1", "json_schema": {"type": "string"}}]],
    )
    persistence: PersistenceConfig | None = Field(
        default=None,
        description="Configuration for state persistence backend.",
        examples=[{"backend_type": "redis", "ttl_seconds": 3600}],
    )


class Edge(CoreasonModel):
    from_node: NodeID = Field(..., description="The ID of the source node.", examples=["node_a"])
    to_node: NodeID = Field(..., description="The ID of the target node.", examples=["node_b"])
    condition: str | None = Field(
        default=None,
        description="An optional Python expression string evaluated to determine edge traversal.",
        examples=["user.age > 18"],
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
        description="A dictionary mapping Node IDs to Node objects.",
        examples=[{"node_1": {"id": "node_1", "type": "agent", "profile": "assistant"}}],
    )
    edges: list[Edge] = Field(
        ...,
        description="A list of edges connecting the nodes.",
        examples=[[{"from_node": "node_1", "to_node": "node_2"}]],
    )
    entry_point: NodeID | None = Field(
        default=None, description="The ID of the node where execution starts.", examples=["node_1"]
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
        default_factory=dict,
        description="The required inputs for the flow.",
        examples=[{"user_name": "string", "age": "integer"}],
    )
    outputs: dict[str, Any] | DataSchema = Field(
        default_factory=dict,
        description="The expected outputs from the flow.",
        examples=[{"status": "string", "result_data": "object"}],
    )


class FlowDefinitions(CoreasonModel):
    profiles: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared profile definitions.",
        examples=[{"assistant": {"role": "helper", "reasoning": {"model": "gpt-4"}}}],
    )
    schemas: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared data schemas.",
        examples=[{"user_schema": {"type": "object", "properties": {"name": {"type": "string"}}}}],
    )
    tools: dict[str, AnyTool] = Field(
        default_factory=dict,
        description="Shared tool definitions.",
        examples=[{"calculator": {"name": "calculator", "type": "capability"}}],
    )
    tool_packs: dict[str, ToolPack] = Field(
        default_factory=dict,
        description="Shared tool pack definitions.",
        examples=[{"math_pack": {"namespace": "math", "tools": [{"name": "add", "type": "capability"}]}}],
    )
    skills: dict[str, Any] = Field(
        default_factory=dict, description="Shared skill definitions.", examples=[{"greeting": "Say hello"}]
    )
    middlewares: dict[MiddlewareID, MiddlewareDef] = Field(
        default_factory=dict,
        description="Shared middleware definitions.",
        examples=[{"logger": {"type": "logging"}}],
    )
    supervision_templates: Any | None = Field(
        default=None,
        description="Templates used for supervision configurations.",
        examples=[{"strict_approval": {"requires_approval": True}}],
    )


class VariableDef(CoreasonModel):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="The unique identifier for the variable.",
        examples=["var_123"],
    )
    type: str = Field(..., description="The type of the variable.", examples=["string"])
    description: str | None = Field(
        default=None, description="A description of the variable's purpose.", examples=["The user's email address."]
    )


class GraphFlow(CoreasonModel):
    type: Literal["graph"] = Field("graph", description="Discriminator for graph flows.", examples=["graph"])
    kind: Literal["GraphFlow"] = Field("GraphFlow", description="The kind of manifest.", examples=["GraphFlow"])
    status: Literal["draft", "published", "archived"] = Field(
        "draft", description="The lifecycle status of the flow.", examples=["draft", "published"]
    )
    metadata: FlowMetadata = Field(
        ...,
        description="Metadata describing the flow.",
        examples=[{"name": "test_flow", "version": "1.0.0", "description": "Test flow"}],
    )
    interface: FlowInterface = Field(
        ...,
        description="The interface definition for inputs and outputs.",
        examples=[{"inputs": {}, "outputs": {}}],
    )
    governance: Governance | None = Field(
        default=None,
        description="Governance policies applied to the flow.",
        examples=[{"operational_policy": {"max_cost": 10.0}}],
    )
    blackboard: Blackboard | None = Field(
        default_factory=Blackboard,
        description="The blackboard definition for state tracking.",
        examples=[{"variables": {"count": 0}}],
    )
    definitions: FlowDefinitions | None = Field(
        default=None,
        description="Shared definitions used across the flow.",
        examples=[{"profiles": {"assistant": {"role": "helper"}}}],
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


class LinearFlow(CoreasonModel):
    type: Literal["linear"] = Field("linear", description="Discriminator for linear flows.", examples=["linear"])
    kind: Literal["LinearFlow"] = Field("LinearFlow", description="The kind of manifest.", examples=["LinearFlow"])
    status: Literal["draft", "published", "archived"] = Field(
        "draft", description="The lifecycle status of the flow.", examples=["draft", "published"]
    )
    metadata: FlowMetadata = Field(
        ...,
        description="Metadata describing the flow.",
        examples=[{"name": "linear_test", "version": "1.0.0"}],
    )
    steps: list[AnyNode] = Field(
        default_factory=list,
        description="An ordered sequence of execution nodes.",
        examples=[[{"id": "step1", "type": "agent", "profile": "assistant"}]],
    )
    governance: Governance | None = Field(
        default=None,
        description="Governance policies applied to the flow.",
        examples=[{"operational_policy": {"max_retries": 3}}],
    )
    definitions: FlowDefinitions | None = Field(
        default=None,
        description="Shared definitions used across the flow.",
        examples=[{"schemas": {"input": {"type": "object"}}}],
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


class AgentRequest(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    manifest: GraphFlow | LinearFlow = Field(
        ...,
        description="The execution flow to run.",
        examples=[{"kind": "LinearFlow", "type": "linear", "metadata": {"name": "test", "version": "1"}, "steps": []}],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata associated with the request.",
        examples=[{"request_id": "req-1234", "client": "web"}],
    )
