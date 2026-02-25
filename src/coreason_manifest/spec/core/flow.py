import ast
from typing import Annotated, Any, Literal
from uuid import uuid4

import jsonschema
from jsonschema.exceptions import SchemaError
from pydantic import ConfigDict, Field, field_validator, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    EmergenceInspectorNode,
    HumanNode,
    InspectorNode,
    PlaceholderNode,
    PlannerNode,
    SwarmNode,
    SwitchNode,
)
from coreason_manifest.spec.core.tools import AnyTool, ToolCapability, ToolPack
from coreason_manifest.spec.core.types import NodeID, RiskLevel
from coreason_manifest.spec.interop.compliance import RemediationAction
from coreason_manifest.spec.interop.exceptions import FaultSeverity, ManifestError, RecoveryAction, SemanticFault
from coreason_manifest.utils.io import SecurityViolationError


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
    json_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")

    @model_validator(mode="after")
    def validate_schema_validity(self) -> "DataSchema":
        try:
            jsonschema.validators.validator_for(self.json_schema).check_schema(self.json_schema)
        except SchemaError as e:
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-SCHEMA-INVALID",
                    message=f"Invalid JSON Schema definition: {e.message}",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={
                        "remediation": RemediationAction(
                            type="update_field",
                            description="Correct the JSON Schema syntax.",
                            patch_data=[{"op": "replace", "path": "/schema", "value": {}}],
                        ).model_dump()
                    },
                )
            ) from e
        return self


class Blackboard(CoreasonModel):
    variables: dict[str, Any] = Field(default_factory=dict)
    schemas: list[DataSchema] = Field(default_factory=list)
    persistence: Any | None = None


AnyNode = Annotated[
    AgentNode
    | SwitchNode
    | InspectorNode
    | EmergenceInspectorNode
    | PlannerNode
    | HumanNode
    | SwarmNode
    | PlaceholderNode,
    Field(discriminator="type"),
]


class Edge(CoreasonModel):
    from_node: NodeID = Field(..., alias="from")
    to_node: NodeID = Field(..., alias="to")
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
    supervision_templates: Any | None = None


class VariableDef(CoreasonModel):
    id: str = Field(default_factory=lambda: str(uuid4()), alias="name")
    type: str
    description: str | None = None


def _scan_for_kill_switch_violations(
    max_risk: RiskLevel, definitions: FlowDefinitions | None, nodes: list[AnyNode]
) -> None:
    """
    Centralized security scanner to enforce global risk governance.
    Recursively scans the entire object graph for tools and remote URIs.
    """
    from pydantic import BaseModel

    def _recursive_scan(obj: Any) -> None:
        # 1. Check ToolCapability objects
        if isinstance(obj, ToolCapability) and obj.risk_level.weight > max_risk.weight:
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-SEC-KILL-SWITCH-VIOLATION",
                    message=(
                        f"Security Violation: Tool '{obj.name}' has risk level '{obj.risk_level.value}' "
                        f"which exceeds the global max_risk_level '{max_risk.value}'."
                    ),
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={
                        "tool_name": obj.name,
                        "tool_risk": obj.risk_level.value,
                        "max_risk": max_risk.value,
                    },
                )
            )
            # ToolCapability might have nested fields, but typically leaf. Continue scan if needed?
            # ToolCapability inherits CoreasonModel, so we'll scan its fields below if we don't return.
            # But since we checked the tool itself, we might want to check children too if tools can contain tools.
            # Assuming ToolCapability is a leaf for risk purposes, but safety first: proceed.

        # 2. Check Strings for Remote URIs
        if isinstance(obj, str):
            if "://" in obj and RiskLevel.CRITICAL.weight > max_risk.weight:
                raise ManifestError(
                    fault=SemanticFault(
                        error_code="CRSN-SEC-KILL-SWITCH-VIOLATION",
                        message=(
                            "Security Violation: Unresolved remote tool URIs default to CRITICAL risk "
                            "and violate the global max_risk_level."
                        ),
                        severity=FaultSeverity.CRITICAL,
                        recovery_action=RecoveryAction.HALT,
                        context={
                            "tool_uri": obj,
                            "assumed_risk": RiskLevel.CRITICAL.value,
                            "max_risk": max_risk.value,
                        },
                    )
                )
            return

        # 3. Recursion
        if isinstance(obj, dict):
            for v in obj.values():
                _recursive_scan(v)
        elif isinstance(obj, (list, tuple, set)):
            for v in obj:
                _recursive_scan(v)
        elif isinstance(obj, BaseModel):
            # Efficiently iterate model fields
            for name in type(obj).model_fields:
                value = getattr(obj, name)
                _recursive_scan(value)

    # Start scan
    if definitions:
        _recursive_scan(definitions)

    _recursive_scan(nodes)


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
    def validate_topology(self) -> "GraphFlow":
        node_ids = set(self.graph.nodes.keys())

        # Validate resilience references
        template_ids = set()
        if (
            self.definitions
            and self.definitions.supervision_templates
            and isinstance(self.definitions.supervision_templates, dict)
        ):
            template_ids = set(self.definitions.supervision_templates.keys())

        for node in self.graph.nodes.values():
            if isinstance(node.resilience, str):
                ref_id = node.resilience.removeprefix("ref:")

                if ref_id not in template_ids:
                    raise ManifestError(
                        fault=SemanticFault(
                            error_code="CRSN-VAL-RESILIENCE-MISSING",
                            message=f"Node '{node.id}' references missing resilience template '{node.resilience}'.",
                            severity=FaultSeverity.CRITICAL,
                            recovery_action=RecoveryAction.HALT,
                            context={"node_id": node.id, "template_id": node.resilience},
                        )
                    )

        # Rule A: Entry Point
        if self.graph.entry_point and self.graph.entry_point not in node_ids:
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-ENTRY-POINT-MISSING",
                    message=f"Entry point '{self.graph.entry_point}' not found in nodes.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={"entry_point": self.graph.entry_point},
                )
            )

        # Rule B: Fallback Orphans
        if (
            self.governance
            and self.governance.circuit_breaker
            and self.governance.circuit_breaker.fallback_node_id
            and self.governance.circuit_breaker.fallback_node_id not in node_ids
        ):
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-FALLBACK-MISSING",
                    message=(
                        f"Circuit breaker fallback '{self.governance.circuit_breaker.fallback_node_id}' "
                        "not found in nodes."
                    ),
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={"fallback_id": self.governance.circuit_breaker.fallback_node_id},
                )
            )

        return self

    @model_validator(mode="after")
    def validate_swarm_variables(self) -> "GraphFlow":
        if not self.blackboard:
            return self

        variable_names = set(self.blackboard.variables.keys())

        nodes_iter = self.graph.nodes.values() if isinstance(self.graph.nodes, dict) else self.graph.nodes

        for node in nodes_iter:
            if isinstance(node, SwarmNode) and node.workload_variable not in variable_names:
                raise ManifestError(
                    fault=SemanticFault(
                        error_code="CRSN-VAL-SWARM-VAR-MISSING",
                        message=(
                            f"SwarmNode '{node.id}' references missing workload variable '{node.workload_variable}'."
                        ),
                        severity=FaultSeverity.CRITICAL,
                        recovery_action=RecoveryAction.HALT,
                        context={
                            "remediation": RemediationAction(
                                type="update_field",
                                description=f"Add variable '{node.workload_variable}' to blackboard.",
                                patch_data=[
                                    {  # pragma: no cover
                                        "op": "add",
                                        "path": f"/blackboard/variables/{node.workload_variable}",
                                        "value": [],
                                    }
                                ],
                            ).model_dump()
                        },
                    )
                )
        return self

    @model_validator(mode="after")
    def enforce_global_kill_switch(self) -> "GraphFlow":
        if not self.governance or not self.governance.max_risk_level:
            return self

        _scan_for_kill_switch_violations(
            self.governance.max_risk_level,
            self.definitions,
            list(self.graph.nodes.values()),
        )
        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "GraphFlow":
        # Only enforce for published flows
        if self.status != "published":
            return self

        # 1. Entry Point Presence
        if not self.graph.entry_point:
            # Try to suggest an existing node
            suggested_entry = "start_node"
            if self.graph.nodes:
                suggested_entry = next(iter(self.graph.nodes.keys()))

            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-ENTRY-POINT-MISSING",
                    message="Published flow MUST have a defined entry_point.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={
                        "remediation": RemediationAction(
                            type="update_field",
                            description="Set a valid entry_point.",
                            patch_data=[{"op": "add", "path": "/graph/entry_point", "value": suggested_entry}],
                        ).model_dump()
                    },
                )
            )

        # 2. Concrete Resolution (No PlaceholderNode)
        abstract_nodes = [node for node in self.graph.nodes.values() if isinstance(node, PlaceholderNode)]

        if abstract_nodes:
            # Dynamically generate patch_data for all abstract nodes
            patch_data = [
                {
                    "op": "replace",
                    "path": f"/graph/nodes/{node.id}",
                    "value": {"type": "agent", "id": node.id, "profile": "default"},
                }
                for node in abstract_nodes
            ]

            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-ABSTRACT-NODE",
                    message=f"Published flow contains {len(abstract_nodes)} abstract PlaceholderNode(s).",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={
                        "node_ids": [node.id for node in abstract_nodes],
                        "remediation": RemediationAction(
                            type="update_field",
                            description="Replace all PlaceholderNodes with concrete implementations.",
                            patch_data=patch_data,
                        ).model_dump(),
                    },
                )
            )
        return self


class LinearFlow(CoreasonModel):
    """
    Simplified linear execution flow (sequence of steps).
    """

    type: Literal["linear"] = "linear"
    kind: Literal["LinearFlow"] = "LinearFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    steps: list[AnyNode] = Field(default_factory=list, alias="sequence")
    governance: Governance | None = None
    definitions: FlowDefinitions | None = None

    @property
    def sequence(self) -> list[AnyNode]:
        return self.steps

    @model_validator(mode="after")
    def validate_resilience_references(self) -> "LinearFlow":
        template_ids = set()
        if (
            self.definitions
            and self.definitions.supervision_templates
            and isinstance(self.definitions.supervision_templates, dict)
        ):
            template_ids = set(self.definitions.supervision_templates.keys())

        for node in self.steps:
            if isinstance(node.resilience, str):
                ref_id = node.resilience.removeprefix("ref:")

                if ref_id not in template_ids:
                    raise ManifestError(
                        fault=SemanticFault(
                            error_code="CRSN-VAL-RESILIENCE-MISSING",
                            message=f"Node '{node.id}' references missing resilience template '{node.resilience}'.",
                            severity=FaultSeverity.CRITICAL,
                            recovery_action=RecoveryAction.HALT,
                            context={"node_id": node.id, "template_id": node.resilience},
                        )
                    )
        return self

    @model_validator(mode="after")
    def enforce_global_kill_switch(self) -> "LinearFlow":
        if not self.governance or not self.governance.max_risk_level:
            return self

        _scan_for_kill_switch_violations(
            self.governance.max_risk_level,
            self.definitions,
            self.steps,
        )
        return self

    @model_validator(mode="after")
    def enforce_lifecycle_constraints(self) -> "LinearFlow":
        # Only enforce for published flows
        if self.status != "published":
            return self

        # 1. Concrete Resolution (No PlaceholderNode)
        abstract_nodes = []
        for idx, node in enumerate(self.steps):
            if isinstance(node, PlaceholderNode):
                abstract_nodes.append((idx, node))

        if abstract_nodes:
            # Dynamically generate patch_data for all abstract nodes
            patch_data = [
                {
                    "op": "replace",
                    "path": f"/sequence/{idx}",
                    "value": {"type": "agent", "id": node.id, "profile": "default"},
                }
                for idx, node in abstract_nodes
            ]

            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-ABSTRACT-NODE",
                    message=f"Published flow contains {len(abstract_nodes)} abstract PlaceholderNode(s).",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={
                        "node_ids": [node.id for _, node in abstract_nodes],
                        "remediation": RemediationAction(
                            type="update_field",
                            description="Replace all PlaceholderNodes with concrete implementations.",
                            patch_data=patch_data,
                        ).model_dump(),
                    },
                )
            )
        return self


Manifest = GraphFlow


class AgentRequest(CoreasonModel):
    """
    Strict envelope for agent execution requests.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    manifest: GraphFlow | LinearFlow
    metadata: dict[str, Any] = Field(default_factory=dict)


def validate_integrity(definitions: FlowDefinitions, nodes: list[AnyNode]) -> None:
    """
    Validates integrity of nodes against definitions.
    """
    profile_ids = set(definitions.profiles.keys())
    for node in nodes:
        if isinstance(node, SwarmNode) and node.worker_profile not in profile_ids:
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-VAL-INTEGRITY-PROFILE-MISSING",
                    message=f"SwarmNode '{node.id}' references missing profile '{node.worker_profile}'.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={},
                )
            )
