import ast
from typing import Any, Literal
from uuid import uuid4

import jsonschema
from jsonschema.exceptions import SchemaError
from pydantic import ConfigDict, Field, field_validator, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.contracts import NodeSpec
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.contracts import AtomicSkill
from coreason_manifest.spec.core.nodes import CognitiveProfile
from coreason_manifest.spec.core.tools import AnyTool, ToolPack
from coreason_manifest.spec.core.types import (
    MiddlewareDef,
    MiddlewareID,
    NodeID,
    StrictJson,
    StrictPayload,
)
from coreason_manifest.spec.interop.compliance import RemediationAction
from coreason_manifest.spec.interop.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.utils.io import SecurityViolationError

# Export NodeSpec so it can be imported from here as well
__all__ = [
    "AgentRequest",
    "Blackboard",
    "DataSchema",
    "EdgeSpec",
    "FlowDefinitions",
    "FlowInterface",
    "FlowMetadata",
    "FlowSpec",
    "Graph",
    "Manifest",
    "NodeSpec",
    "PersistenceConfig",
    "SupervisionConfig",
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
    json_schema: dict[str, StrictJson] = Field(default_factory=dict, alias="schema")

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
                        patch_data=[{"op": "replace", "path": "/schema", "value": {}}],
                    ).model_dump()
                },
            ) from e
        return self


class PersistenceConfig(CoreasonModel):
    type: str
    config: dict[str, StrictJson] = Field(default_factory=dict)


class Blackboard(CoreasonModel):
    variables: dict[str, StrictJson] = Field(default_factory=dict)
    schemas: list[DataSchema] = Field(default_factory=list)
    persistence: PersistenceConfig | None = None


class EdgeSpec(CoreasonModel):
    from_node: NodeID = Field(..., alias="from")
    to_node: NodeID = Field(..., alias="to")
    condition: str | None = None
    max_iterations: int | None = Field(None, ge=1, description="Max loop iterations (must be >= 1).")
    timeout: int | None = Field(None, ge=1, description="Timeout in seconds (must be >= 1).")

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
                    ast.Attribute,
                    ast.Subscript,
                    ast.Index,
                    ast.Slice,
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

            def visit_Attribute(self, node: ast.Attribute) -> None:
                if node.attr.startswith("__"):
                    raise SecurityViolationError(
                        f"Security Violation: Dunder attribute access '{node.attr}' forbidden in condition '{v}'"
                    )
                super().generic_visit(node)

            def visit_Subscript(self, node: ast.Subscript) -> None:
                # Block dynamic slice construction (e.g. payload["__" + "class__"])
                class SliceVisitor(ast.NodeVisitor):
                    def visit_BinOp(self, n: ast.BinOp) -> None:
                        raise SecurityViolationError(
                            f"Security Violation: Dynamic slice construction (BinOp) forbidden in condition '{v}'"
                        )

                    def visit_Call(self, n: ast.Call) -> None:
                        raise SecurityViolationError(
                            f"Security Violation: Dynamic slice construction (Call) forbidden in condition '{v}'"
                        )

                    def visit_JoinedStr(self, n: ast.JoinedStr) -> None:
                        raise SecurityViolationError(
                            f"Security Violation: Dynamic slice construction (f-string) forbidden in condition '{v}'"
                        )

                SliceVisitor().visit(node.slice)

                # Check if the slice is a constant string starting with "__"
                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    if node.slice.value.startswith("__"):
                        raise SecurityViolationError(
                            f"Security Violation: Dunder subscript access '{node.slice.value}' forbidden in condition '{v}'"
                        )
                super().generic_visit(node)

        visitor = SecurityVisitor()
        visitor.visit(tree)
        return v


class Graph(CoreasonModel):
    nodes: dict[str, NodeSpec]
    edges: list[EdgeSpec]
    entry_point: NodeID | None = None


class FlowInterface(CoreasonModel):
    inputs: StrictPayload | DataSchema = Field(default_factory=StrictPayload)
    outputs: StrictPayload | DataSchema = Field(default_factory=StrictPayload)


class SupervisionConfig(CoreasonModel):
    ref: str
    params: dict[str, StrictJson] = Field(default_factory=dict)


class FlowDefinitions(CoreasonModel):
    profiles: dict[str, CognitiveProfile] = Field(default_factory=dict)
    schemas: dict[str, DataSchema] = Field(default_factory=dict)
    tools: dict[str, AnyTool] = Field(default_factory=dict)
    tool_packs: dict[str, ToolPack] = Field(default_factory=dict)
    skills: dict[str, AtomicSkill] = Field(default_factory=dict)
    middlewares: dict[MiddlewareID, MiddlewareDef] = Field(default_factory=dict)
    supervision_templates: dict[str, SupervisionConfig] | None = None


class VariableDef(CoreasonModel):
    id: str = Field(default_factory=lambda: str(uuid4()), alias="name")
    type: str
    description: str | None = None


class FlowSpec(CoreasonModel):
    """
    Unified execution flow specification.
    """

    type: Literal["flow"] = "flow"
    kind: Literal["FlowSpec"] = "FlowSpec"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    interface: FlowInterface
    governance: Governance | None = None
    blackboard: Blackboard | None = Field(default_factory=Blackboard)
    definitions: FlowDefinitions | None = None
    graph: Graph


Manifest = FlowSpec


class AgentRequest(CoreasonModel):
    """
    Strict envelope for agent execution requests.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    manifest: FlowSpec
    metadata: StrictPayload = Field(default_factory=StrictPayload)
