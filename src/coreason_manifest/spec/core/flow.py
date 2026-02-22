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
from coreason_manifest.spec.core.types import NodeID
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
    # Compatibility: default ID, alias json_schema to schema_def
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_def: dict[str, Any] = Field(default_factory=dict, alias="schema")

    @model_validator(mode="before")
    @classmethod
    def compat_json_schema(cls, data: Any) -> Any:
        if isinstance(data, dict) and "json_schema" in data and "schema" not in data:
            data["schema"] = data.pop("json_schema")
        return data

    @property
    def json_schema(self) -> dict[str, Any]:
        return self.schema_def

    @model_validator(mode="after")
    def validate_schema_validity(self) -> "DataSchema":
        try:
            jsonschema.validators.validator_for(self.schema_def).check_schema(self.schema_def)
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
    persistence: Any | None = None  # Compatibility


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
                data["from"] = data.pop("source")
            if "target" in data:
                data["to"] = data.pop("target")
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
    tools: dict[str, Any] = Field(default_factory=dict)
    tool_packs: dict[str, Any] = Field(default_factory=dict)
    supervision_templates: Any | None = None  # Compatibility


class VariableDef(CoreasonModel):
    id: str
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
    blackboard: Blackboard = Field(default_factory=Blackboard)
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
                                type="add_variable",
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


class LinearFlow(CoreasonModel):
    """
    Simplified linear execution flow (sequence of steps).
    """

    type: Literal["linear"] = "linear"
    kind: Literal["LinearFlow"] = "LinearFlow"  # Compatibility
    status: Literal["draft", "published", "archived"] = "draft"  # Compatibility
    metadata: FlowMetadata
    steps: list[AnyNode] = Field(default_factory=list, alias="sequence")
    governance: Governance | None = None
    definitions: FlowDefinitions | None = None  # Compatibility

    @model_validator(mode="before")
    @classmethod
    def compat_sequence(cls, data: Any) -> Any:
        if isinstance(data, dict) and "sequence" in data:
            data["steps"] = data.pop("sequence")
        return data
