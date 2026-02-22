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
    # Compatibility: Rename schema_def back to json_schema, alias to "schema" for serialization
    id: str = Field(default_factory=lambda: str(uuid4()))
    json_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")

    @model_validator(mode="before")
    @classmethod
    def compat_schema(cls, data: Any) -> Any:
        if isinstance(data, dict) and "name" in data and "id" not in data:
            # Allow "json_schema" or "schema"
            # If "json_schema" is present and "schema" is not, alias mapping handles it?
            # No, alias applies to input "schema" mapping to field "json_schema".
            # So if input has "schema", it works.
            # If input has "json_schema", it works (by field name) IF `populate_by_name=True`.
            # CoreasonModel might not have `populate_by_name=True` by default?
            # Let's ensure strict compatibility.
            pass
        return data

    @property
    def schema_def(self) -> dict[str, Any]:
        return self.json_schema

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
    # Compatibility: source/target instead of from_node/to_node
    # Aliased for serialization if needed, assuming "from"/"to" were external names?
    # Or "source"/"target"? The error log said: `Unexpected keyword argument "source"`.
    # This implies the input was `source`, but the model didn't accept it.
    # So the model must accept `source`.
    source: NodeID = Field(..., alias="from")
    target: NodeID = Field(..., alias="to")
    condition: str | None = None

    @model_validator(mode="before")
    @classmethod
    def compat_source_target(cls, data: Any) -> Any:
        if isinstance(data, dict) and "name" in data and "id" not in data:
            # If "source" is present, it maps to "source" field.
            # But alias="from" means "from" maps to "source".
            # If `populate_by_name` is False (default in V2?), then "source" might fail if alias is set?
            # No, usually alias takes precedence.
            # To support BOTH "from" and "source" keys in input:
            if "from" in data:
                data["source"] = data.pop("from")
            if "to" in data:
                data["target"] = data.pop("to")
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
    supervision_templates: Any | None = None


class VariableDef(CoreasonModel):
    id: str = Field(..., alias="name")  # Support "name" as alias for "id"? Or vice versa?
    # Error: Missing named argument "id".
    # This implies "id" is required.
    # If the caller is passing "name", we need alias="name"?
    # Or maybe the field IS "name"?
    # I'll stick to `id` and allow `name` alias.
    type: str
    description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def compat_id_name(cls, data: Any) -> Any:
        if isinstance(data, dict) and "name" in data and "id" not in data:
                data["id"] = data["name"]
        return data


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
    # Allow None in type hint to satisfy mypy when blackboard=None is passed
    blackboard: Blackboard | None = Field(default_factory=Blackboard)
    definitions: FlowDefinitions | None = None
    graph: Graph

    @model_validator(mode="after")
    def ensure_blackboard(self) -> "GraphFlow":
        if self.blackboard is None:
            self.blackboard = Blackboard()
        return self

    @model_validator(mode="after")
    def validate_swarm_variables(self) -> "GraphFlow":
        if not self.blackboard:  # Should be caught by ensure_blackboard but for safety
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
    kind: Literal["LinearFlow"] = "LinearFlow"
    status: Literal["draft", "published", "archived"] = "draft"
    metadata: FlowMetadata
    # Compatibility: Rename steps to sequence
    sequence: list[AnyNode] = Field(default_factory=list, alias="steps")
    governance: Governance | None = None
    definitions: FlowDefinitions | None = None

    @model_validator(mode="before")
    @classmethod
    def compat_sequence(cls, data: Any) -> Any:
        if isinstance(data, dict) and "name" in data and "id" not in data:
                data["sequence"] = data.pop("steps")
        return data

    @property
    def steps(self) -> list[AnyNode]:
        return self.sequence
