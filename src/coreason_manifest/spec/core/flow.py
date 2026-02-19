from collections.abc import Iterable
from typing import Annotated, Any, Literal

import jsonschema
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    EmergenceInspectorNode,
    HumanNode,
    InspectorNode,
    PlaceholderNode,
    PlannerNode,
    SwarmNode,
    SwitchNode,
)
from coreason_manifest.spec.core.resilience import SupervisionPolicy
from coreason_manifest.spec.core.tools import ToolPack

# Polymorphic Node Type
AnyNode = Annotated[
    AgentNode
    | SwitchNode
    | PlannerNode
    | HumanNode
    | PlaceholderNode
    | InspectorNode
    | EmergenceInspectorNode
    | SwarmNode,
    Field(discriminator="type"),
]


class FlowMetadata(BaseModel):
    """Standard metadata fields."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: str
    description: str
    tags: list[str]


class DataSchema(BaseModel):
    """
    Strict data contract for inputs/outputs.
    Mandate 5: Contract-First Data I/O.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_ref: Annotated[str | None, Field(description="URI to JSON Schema")] = None
    json_schema: dict[str, Any] | bool = Field(
        default_factory=dict,
        description="Full JSON Schema (Draft 7) definition for validation.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_meta_schema(cls, data: Any) -> Any:
        # Idempotency Guard
        if isinstance(data, cls):
            return data

        # Check if we have json_schema key in the input dict
        if isinstance(data, dict) and "json_schema" in data:
            schema = data["json_schema"]

            # Directive 2: Boolean Schema Tolerance
            if isinstance(schema, bool):
                try:
                    jsonschema.Draft7Validator.check_schema(schema)
                    return data
                except SchemaError as e:
                    error_msg = getattr(e, "message", str(e)).split("\n")[0]
                    path_str = f" at '/{'/'.join(map(str, e.path))}'" if hasattr(e, "path") and e.path else ""
                    raise ValueError(f"Invalid JSON Schema{path_str}: {error_msg}") from e

            # Directive 1: Explicit Type Guarding
            if not isinstance(schema, dict):
                raise ValueError("JSON Schema must be a dictionary or a boolean.")

            # Directive 3: Strict Validation (No Heuristic Repair)
            try:
                jsonschema.Draft7Validator.check_schema(schema)
            except SchemaError as e:
                # Directive 3: Robust Error Unwrapping
                error_msg = getattr(e, "message", str(e)).split("\n")[0]
                # Directive 4: High-Fidelity Error Context
                path_str = f" at '/{'/'.join(map(str, e.path))}'" if hasattr(e, "path") and e.path else ""
                raise ValueError(f"Invalid JSON Schema{path_str}: {error_msg}") from e
            except Exception as e:
                raise ValueError(f"Invalid JSON Schema definition: {e}") from e

        return data


class FlowInterface(BaseModel):
    """Input/Output JSON schema contracts."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    inputs: DataSchema
    outputs: DataSchema


class VariableDef(BaseModel):
    """Definition of a blackboard variable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: str
    description: str | None = None


class Blackboard(BaseModel):
    """Shared, observable memory space."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    variables: dict[str, VariableDef]
    persistence: bool


class Edge(BaseModel):
    """Directed connection between nodes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    source: str
    target: str
    condition: str | None = None


class Graph(BaseModel):
    """Directed execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    nodes: dict[str, AnyNode]
    edges: list[Edge]
    entry_point: str = Field(..., description="The ID of the starting node.")


class FlowDefinitions(BaseModel):
    """
    Registry for reusable components (The Blueprint).
    Separates 'definition' from 'usage' to reduce payload size.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # Maps ID -> Configuration
    profiles: dict[str, CognitiveProfile] = Field(
        default_factory=dict, description="Reusable cognitive configurations."
    )
    tool_packs: dict[str, ToolPack] = Field(default_factory=dict, description="Reusable tool dependencies.")
    supervision_templates: dict[str, SupervisionPolicy] = Field(
        default_factory=dict, description="Reusable resilience policies."
    )
    skills: dict[str, Any] = Field(default_factory=dict, description="Reusable executable skills (Future use).")


def validate_integrity(definitions: FlowDefinitions | None, nodes: Iterable[AnyNode]) -> None:
    """Shared referential integrity validation logic."""
    valid_profiles = definitions.profiles.keys() if definitions else set()

    # SOTA: Create a set of all available tools from registered packs
    valid_tools: set[str] = set()
    if definitions and definitions.tool_packs:
        for pack in definitions.tool_packs.values():
            valid_tools.update(t.name for t in pack.tools)

    valid_policies = definitions.supervision_templates.keys() if definitions else set()

    for node in nodes:
        # Check resilience references
        if isinstance(node.resilience, str):
            if node.resilience.startswith("ref:"):
                ref_id = node.resilience[4:]  # Strip 'ref:' prefix
                if ref_id not in valid_policies:
                    raise ValueError(f"Node '{node.id}' references undefined supervision template ID '{ref_id}'")
            else:
                raise ValueError(
                    f"Node '{node.id}' has invalid resilience reference '{node.resilience}'. Must start with 'ref:'"
                )

        if isinstance(node, AgentNode):
            # 1. Profile Check
            if isinstance(node.profile, str) and node.profile not in valid_profiles:
                raise ValueError(f"AgentNode '{node.id}' references undefined profile ID '{node.profile}'")

            # 2. Tool Check
            for tool in node.tools:
                if tool not in valid_tools:
                    raise ValueError(
                        f"AgentNode '{node.id}' requires missing tool '{tool}'. Available: {list(valid_tools)}"
                    )

        elif isinstance(node, SwarmNode):
            if node.worker_profile not in valid_profiles:
                raise ValueError(
                    f"SwarmNode '{node.id}' references undefined worker profile ID '{node.worker_profile}'"
                )


class LinearFlow(BaseModel):
    """A deterministic script."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["LinearFlow"]
    status: Annotated[Literal["draft", "published", "archived"], Field(description="Life-cycle state.")] = "draft"
    metadata: FlowMetadata
    definitions: Annotated[FlowDefinitions | None, Field(description="Shared registry for reusable components.")] = None
    sequence: list[AnyNode]
    governance: Annotated[Governance | None, Field(description="Governance policy.")] = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "LinearFlow":
        """Ensures all string-based profile references point to a valid definition."""
        if self.status == "draft":
            return self
        validate_integrity(self.definitions, self.sequence)
        return self


class GraphFlow(BaseModel):
    """Cyclic Graph structure."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["GraphFlow"]
    status: Annotated[Literal["draft", "published", "archived"], Field(description="Life-cycle state.")] = "draft"
    metadata: FlowMetadata
    definitions: Annotated[FlowDefinitions | None, Field(description="Shared registry for reusable components.")] = None
    interface: FlowInterface
    blackboard: Blackboard | None
    graph: Graph
    governance: Annotated[Governance | None, Field(description="Governance policy.")] = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "GraphFlow":
        """Ensures all string-based profile references point to a valid definition."""
        if self.status == "draft":
            return self
        validate_integrity(self.definitions, self.graph.nodes.values())
        return self
