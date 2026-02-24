from typing import Annotated, Any, Literal
from uuid import uuid4

import jsonschema
from jsonschema.exceptions import SchemaError
from pydantic import Field, model_validator

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

    @model_validator(mode="before")
    @classmethod
    def compat_json_schema(cls, data: Any) -> Any:
        if isinstance(data, dict) and "schema" in data and "json_schema" not in data:
            data["json_schema"] = data.pop("schema")
        return data

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

    @model_validator(mode="before")
    @classmethod
    def compat_source_target(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "source" in data:
                data["from_node"] = data.pop("source")
            if "target" in data:
                data["to_node"] = data.pop("target")
        return data


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

    @model_validator(mode="before")
    @classmethod
    def compat_id_name(cls, data: Any) -> Any:
        if isinstance(data, dict) and "name" in data and "id" not in data:
            data["id"] = data.pop("name")
        return data


def _scan_for_kill_switch_violations(
    max_risk: RiskLevel, definitions: FlowDefinitions | None, nodes: list[AnyNode]
) -> None:
    """
    Centralized security scanner to enforce global risk governance.
    Scans definitions and inline tools in nodes.
    """
    tools_to_check: list[AnyTool] = []

    # 1. Collect tools from definitions
    if definitions:
        tools_to_check.extend(definitions.tools.values())
        for pack in definitions.tool_packs.values():
            tools_to_check.extend(pack.tools)

    # 2. Collect inline tools from nodes (if any)
    for node in nodes:
        # Check for 'tools' attribute (common in AgentNode)
        # Note: AgentNode.tools is currently list[str] (references), so we skip those.
        # But if a node had inline tool objects, we'd catch them here.
        # We also check 'inline_tools' if it exists in future node types.

        # Safely extract potential tool lists
        node_tools = getattr(node, "tools", [])
        node_inline = getattr(node, "inline_tools", [])

        # Combine potential sources
        potential_tools = []
        if isinstance(node_tools, list):
            potential_tools.extend(node_tools)
        if isinstance(node_inline, list):
            potential_tools.extend(node_inline)

        for tool in potential_tools:
            # Only evaluate actual ToolCapability objects (or polymorphic AnyTool)
            if isinstance(tool, ToolCapability):
                tools_to_check.append(tool)
                continue

            # Fail-Closed Zero-Trust Rule:
            # If a tool reference contains a remote URI scheme (e.g. mcp://, http://),
            # it bypasses local definitions and must be treated as CRITICAL risk.
            if isinstance(tool, str) and "://" in tool and RiskLevel.CRITICAL.weight > max_risk.weight:
                # Synthetically evaluate as CRITICAL
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
                            "tool_uri": tool,
                            "assumed_risk": RiskLevel.CRITICAL.value,
                            "max_risk": max_risk.value,
                        },
                    )
                )

    # 3. Enforcement
    for tool in tools_to_check:
        # Rich comparison via RiskLevel Enum
        if tool.risk_level.weight > max_risk.weight:
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-SEC-KILL-SWITCH-VIOLATION",
                    message=(
                        f"Security Violation: Tool '{tool.name}' has risk level '{tool.risk_level.value}' "
                        f"which exceeds the global max_risk_level '{max_risk.value}'."
                    ),
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.HALT,
                    context={
                        "tool_name": tool.name,
                        "tool_risk": tool.risk_level.value,
                        "max_risk": max_risk.value,
                    },
                )
            )


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

    @model_validator(mode="before")
    @classmethod
    def compat_blackboard(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("blackboard") is None:
            data["blackboard"] = Blackboard()
        return data

    @model_validator(mode="after")
    def validate_swarm_variables(self) -> "GraphFlow":
        if not self.blackboard:
            return self

        variable_names = set(self.blackboard.variables.keys())

        nodes_iter = self.graph.nodes.values()

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
                                    {
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
    def validate_lifecycle_readiness(self) -> "GraphFlow":
        if self.status != "published":
            return self

        nodes_iter = self.graph.nodes.values()

        for node in nodes_iter:
            if isinstance(node, PlaceholderNode):
                raise ManifestError(
                    fault=SemanticFault(
                        error_code="CRSN-VAL-LIFECYCLE-LEAK",
                        severity=FaultSeverity.CRITICAL,
                        recovery_action=RecoveryAction.HALT,
                        message=f"Cannot publish flow: Contains abstract PlaceholderNode '{node.id}'.",
                        context={
                            "remediation": RemediationAction(
                                type="replace_node",
                                description=(
                                    f"Replace PlaceholderNode '{node.id}' (requires {node.required_capabilities}) "
                                    "or revert to draft."
                                ),
                                patch_data=[
                                    {
                                        "op": "replace",
                                        "path": "/status",
                                        "value": "draft",
                                    }
                                ],
                                target_node_id=node.id,
                            ).model_dump()
                        },
                    )
                )
    def enforce_global_kill_switch(self) -> "GraphFlow":
        if not self.governance or not self.governance.max_risk_level:
            return self

        _scan_for_kill_switch_violations(
            self.governance.max_risk_level,
            self.definitions,
            list(self.graph.nodes.values()),
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

    @model_validator(mode="before")
    @classmethod
    def compat_sequence(cls, data: Any) -> Any:
        if isinstance(data, dict) and "sequence" in data and "steps" not in data:
            data["steps"] = data.pop("sequence")
        return data

    @property
    def sequence(self) -> list[AnyNode]:
        return self.steps

    @model_validator(mode="after")
    def validate_lifecycle_readiness(self) -> "LinearFlow":
        if self.status != "published":
            return self

        for node in self.steps:
            if isinstance(node, PlaceholderNode):
                raise ManifestError(
                    fault=SemanticFault(
                        error_code="CRSN-VAL-LIFECYCLE-LEAK",
                        severity=FaultSeverity.CRITICAL,
                        recovery_action=RecoveryAction.HALT,
                        message=f"Cannot publish linear flow: Contains abstract PlaceholderNode '{node.id}'.",
                        context={
                            "remediation": RemediationAction(
                                type="replace_node",
                                description=(
                                    f"Replace PlaceholderNode '{node.id}' (requires {node.required_capabilities}) "
                                    "or revert to draft."
                                ),
                                patch_data=[
                                    {
                                        "op": "replace",
                                        "path": "/status",
                                        "value": "draft",
                                    }
                                ],
                                target_node_id=node.id,
                            ).model_dump()
                        },
                    )
                )
    def enforce_global_kill_switch(self) -> "LinearFlow":
        if not self.governance or not self.governance.max_risk_level:
            return self

        _scan_for_kill_switch_violations(
            self.governance.max_risk_level,
            self.definitions,
            self.steps,
        )
        return self


Manifest = GraphFlow


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
