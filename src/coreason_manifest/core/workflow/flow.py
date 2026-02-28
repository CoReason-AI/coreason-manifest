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
    name: str
    version: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class DataSchema(CoreasonModel):
    # Compatibility: Field is 'json_schema' to avoid shadowing BaseModel.schema
    id: str = Field(default_factory=lambda: str(uuid4()))
    json_schema: dict[str, Any] = Field(default_factory=dict)

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
    variables: dict[str, Any] = Field(default_factory=dict)
    schemas: list[DataSchema] = Field(default_factory=list)
    persistence: PersistenceConfig | None = None


class Edge(CoreasonModel):
    from_node: NodeID
    to_node: NodeID
    condition: str | None = None
    cost_weight: float = Field(0.0, ge=0.0, description="Estimated financial cost (USD) to traverse this edge.")
    latency_weight_ms: float = Field(0.0, ge=0.0, description="Estimated latency in milliseconds.")

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
    nodes: dict[str, AnyNode]
    edges: list[Edge]
    entry_point: NodeID | None = None

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
    inputs: dict[str, Any] | DataSchema = Field(default_factory=dict)
    outputs: dict[str, Any] | DataSchema = Field(default_factory=dict)


class FlowDefinitions(CoreasonModel):
    profiles: dict[str, Any] = Field(default_factory=dict)
    schemas: dict[str, Any] = Field(default_factory=dict)
    tools: dict[str, AnyTool] = Field(default_factory=dict)
    tool_packs: dict[str, ToolPack] = Field(default_factory=dict)
    skills: dict[str, Any] = Field(default_factory=dict)
    middlewares: dict[MiddlewareID, MiddlewareDef] = Field(default_factory=dict)
    supervision_templates: Any | None = None


class VariableDef(CoreasonModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    description: str | None = None


class GraphFlow(CoreasonModel):
    """
    Standard graph-based execution flow.
    """

    type: Literal["graph"] = "graph"
    kind: Literal["GraphFlow"] = "GraphFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    interface: FlowInterface
    governance: Governance | None = None
    blackboard: Blackboard | None = Field(default_factory=Blackboard)
    definitions: FlowDefinitions | None = None
    graph: Graph

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
    """
    Simplified linear execution flow (sequence of steps).
    """

    type: Literal["linear"] = "linear"
    kind: Literal["LinearFlow"] = "LinearFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    steps: list[AnyNode] = Field(default_factory=list)
    governance: Governance | None = None
    definitions: FlowDefinitions | None = None

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
    """
    Strict envelope for agent execution requests.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    manifest: GraphFlow | LinearFlow
    metadata: dict[str, Any] = Field(default_factory=dict)
