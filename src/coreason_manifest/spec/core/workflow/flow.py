import ast
from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

import jsonschema  # type: ignore[import-untyped]
from jsonschema.exceptions import SchemaError  # type: ignore[import-untyped]
from pydantic import ConfigDict, Field, field_validator, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.primitives.types import MiddlewareDef, MiddlewareID, NodeID
from coreason_manifest.spec.core.state.tools import AnyTool, ToolPack
from coreason_manifest.spec.core.workflow.nodes import (
    AnyNode,
)
from coreason_manifest.spec.interop.compliance import RemediationAction
from coreason_manifest.spec.interop.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.utils.io import SecurityViolationError

if TYPE_CHECKING:
    from coreason_manifest.spec.core.oversight.governance import Governance

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
    persistence: Any | None = None


class Edge(CoreasonModel):
    from_node: NodeID
    to_node: NodeID
    condition: str | None = None

    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition_ast(cls, v: str | None) -> str | None:
        if not v:
            return v

        try:
            tree = ast.parse(v, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in condition: {e}") from e  # pragma: no cover

        class SecurityVisitor(ast.NodeVisitor):
            def generic_visit(self, node: ast.AST) -> None:
                # Whitelist of allowed AST nodes
                allowed = (
                    ast.Expression,
                    ast.BoolOp,
                    ast.BinOp,
                    ast.UnaryOp,
                    ast.Compare,
                    ast.Constant,
                    ast.Name,
                    ast.Load,
                    ast.And,
                    ast.Or,
                    ast.Eq,
                    ast.NotEq,
                    ast.Lt,
                    ast.LtE,
                    ast.Gt,
                    ast.GtE,
                    ast.Is,
                    ast.IsNot,
                    ast.In,
                    ast.NotIn,
                    ast.Not,
                    ast.Add,
                    ast.Sub,
                    ast.Mult,
                    ast.Div,
                    ast.FloorDiv,
                    ast.Mod,
                    ast.Pow,
                    ast.USub,
                    ast.UAdd,
                )
                if not isinstance(node, allowed):
                    raise SecurityViolationError(
                        f"Security Violation: forbidden AST node {type(node).__name__} in condition '{v}'"
                    )
                super().generic_visit(node)

            def visit_Name(self, node: ast.Name) -> None:
                # Ensure Name usage is strictly Load context
                if not isinstance(node.ctx, ast.Load):
                    raise SecurityViolationError(
                        f"Security Violation: Name context {type(node.ctx).__name__} forbidden in condition '{v}'"
                    )  # pragma: no cover
                super().generic_visit(node)

        visitor = SecurityVisitor()
        visitor.visit(tree)
        return v


class Graph(CoreasonModel):
    nodes: dict[str, AnyNode]
    edges: list[Edge]
    entry_point: NodeID | None = None


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
    governance: "Governance | None" = None
    blackboard: Blackboard | None = Field(default_factory=Blackboard)
    definitions: FlowDefinitions | None = None
    graph: Graph


class LinearFlow(CoreasonModel):
    """
    Simplified linear execution flow (sequence of steps).
    """

    type: Literal["linear"] = "linear"
    kind: Literal["LinearFlow"] = "LinearFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    steps: list[AnyNode] = Field(default_factory=list)
    governance: "Governance | None" = None
    definitions: FlowDefinitions | None = None


class AgentRequest(CoreasonModel):
    """
    Strict envelope for agent execution requests.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    manifest: GraphFlow | LinearFlow
    metadata: dict[str, Any] = Field(default_factory=dict)
