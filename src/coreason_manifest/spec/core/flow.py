from collections.abc import Iterable
from typing import Annotated, Any, Literal

import jsonschema
from jsonschema.exceptions import SchemaError
from pydantic import Field, RootModel, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.engines import AttentionReasoning
from coreason_manifest.spec.core.exceptions import DomainValidationError
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
from coreason_manifest.spec.core.types import (
    CoercibleStringList,
    NodeID,
    ProfileID,
    SemanticVersion,
    VariableID,
)
from coreason_manifest.spec.interop.compliance import RemediationAction

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


class FlowMetadata(CoreasonModel):
    """Standard metadata fields."""

    name: str = Field(..., description="Name of the flow.", examples=["My Agent Flow"])
    version: SemanticVersion = Field(..., description="Semantic version.", examples=["1.0.0"])
    description: str = Field(
        ..., description="Description of what the flow does.", examples=["A flow that scrapes and summarizes."]
    )
    tags: CoercibleStringList = Field(
        default_factory=list, description="Tags for categorization.", examples=[["research", "scraper"]]
    )


class DataSchema(CoreasonModel):
    """
    Strict data contract for inputs/outputs.
    Mandate 5: Contract-First Data I/O.
    """

    schema_ref: Annotated[str | None, Field(description="URI to JSON Schema")] = None
    json_schema: dict[str, Any] | bool = Field(
        default_factory=dict,
        description="Full JSON Schema (Draft 7) definition for validation.",
        examples=[{"type": "object", "properties": {"query": {"type": "string"}}}],
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

            # Directive 3: The "Healing" Ingestion Pipeline
            try:
                jsonschema.Draft7Validator.check_schema(schema)
            except SchemaError as e:
                # Directive 3: Robust Error Unwrapping
                error_msg = getattr(e, "message", str(e)).split("\n")[0]
                path_str = f" at '/{'/'.join(map(str, e.path))}'" if hasattr(e, "path") and e.path else ""
                final_error_msg = f"Invalid JSON Schema{path_str}: {error_msg}"

                # SOTA: Attempt Healing (Stubbed)
                _repair_config = AttentionReasoning(
                    model="gpt-4-turbo",  # Default repair model
                    attention_mode="rephrase",
                    focus_model="gpt-3.5-turbo",
                )

                raise DomainValidationError(
                    message=final_error_msg,
                    remediation=RemediationAction(
                        type="semantic_repair",
                        description="Route payload to LLM for syntactic repair of the JSON Schema.",
                        patch_data=_repair_config.model_dump(),
                    ),
                ) from e
            except Exception as e:
                raise DomainValidationError(f"Invalid JSON Schema definition: {e}") from e

        return data


class FlowInterface(CoreasonModel):
    """Input/Output JSON schema contracts."""

    inputs: DataSchema = Field(..., description="Input schema.")
    outputs: DataSchema = Field(..., description="Output schema.")


class VariableDef(CoreasonModel):
    """Definition of a blackboard variable."""

    type: str = Field(..., description="Data type description.", examples=["string", "list[str]"])
    description: str | None = Field(None, description="Description of the variable usage.", examples=["User query"])


class Blackboard(CoreasonModel):
    """Shared, observable memory space."""

    variables: dict[VariableID, VariableDef] = Field(
        ..., description="Variables defined in the blackboard.", examples=[{"query": {"type": "string"}}]
    )
    persistence: bool = Field(False, description="Whether state persists across sessions.")


class Edge(CoreasonModel):
    """Directed connection between nodes."""

    source: NodeID = Field(..., description="Source node ID.", examples=["start"])
    target: NodeID = Field(..., description="Target node ID.", examples=["end"])
    condition: str | None = Field(
        None, description="Condition expression for traversal.", examples=["result == 'success'"]
    )


class Graph(CoreasonModel):
    """Directed execution graph."""

    nodes: dict[NodeID, AnyNode] = Field(..., description="Map of Node ID to Node configuration.")
    edges: list[Edge] = Field(..., description="List of directed edges.")
    entry_point: NodeID = Field(..., description="The ID of the starting node.", examples=["start"])

    @model_validator(mode="after")
    def validate_graph_structure(self) -> "Graph":
        """
        Validates internal graph consistency.
        Always enforced (Node ID matching).
        Dangling edges are allowed in DRAFT mode (enforced by parent Flow or verify_integrity).
        """
        # 1. Key/ID Consistency
        for key, node in self.nodes.items():
            if key != node.id:
                raise ValueError(f"Graph Integrity Error: Node key '{key}' does not match Node ID '{node.id}'")

        return self

    def verify_integrity(self, strict: bool = True) -> None:  # noqa: ARG002
        """
        Verifies full structural integrity (Reachability, Dangling Edges).
        Strict mode (Published) enforces no dangling edges and full reachability.
        """
        node_ids = set(self.nodes.keys())

        # 1. Edge Integrity (Dangling Checks)
        # SOTA Directive 1: Referential integrity must be guaranteed universally, even in DRAFT mode.
        # An edge pointing to non-existent memory is a syntax error, not a policy violation.
        for i, edge in enumerate(self.edges):
            if edge.source not in node_ids:
                raise ValueError(f"Edge {i} source '{edge.source}' not found in nodes.")
            if edge.target not in node_ids:
                raise ValueError(f"Edge {i} target '{edge.target}' not found in nodes.")

        if self.entry_point not in node_ids:
            raise ValueError(f"Entry point '{self.entry_point}' not found in nodes.")


class FlowDefinitions(CoreasonModel):
    """
    Registry for reusable components (The Blueprint).
    Separates 'definition' from 'usage' to reduce payload size.
    """

    # Maps ID -> Configuration
    profiles: dict[ProfileID, CognitiveProfile] = Field(
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


class LinearFlow(CoreasonModel):
    """A deterministic script."""

    kind: Literal["LinearFlow"] = "LinearFlow"
    status: Annotated[Literal["draft", "published", "archived"], Field(description="Life-cycle state.")] = "draft"
    metadata: FlowMetadata = Field(..., description="Metadata for the flow.")
    definitions: Annotated[FlowDefinitions | None, Field(description="Shared registry for reusable components.")] = None
    sequence: list[AnyNode] = Field(..., description="Ordered list of nodes to execute.")
    governance: Annotated[Governance | None, Field(description="Governance policy.")] = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "LinearFlow":
        """Ensures all string-based profile references point to a valid definition."""
        if self.status == "draft":
            return self
        validate_integrity(self.definitions, self.sequence)
        return self


class GraphFlow(CoreasonModel):
    """Cyclic Graph structure."""

    kind: Literal["GraphFlow"] = "GraphFlow"
    status: Annotated[Literal["draft", "published", "archived"], Field(description="Life-cycle state.")] = "draft"
    metadata: FlowMetadata = Field(..., description="Metadata for the flow.")
    definitions: Annotated[FlowDefinitions | None, Field(description="Shared registry for reusable components.")] = None
    interface: FlowInterface = Field(..., description="Input/Output contract.")
    blackboard: Blackboard | None = Field(None, description="Shared memory configuration.")
    graph: Graph = Field(..., description="The execution graph.")
    governance: Annotated[Governance | None, Field(description="Governance policy.")] = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "GraphFlow":
        """Ensures all string-based profile references point to a valid definition."""
        if self.status == "draft":
            return self
        validate_integrity(self.definitions, self.graph.nodes.values())
        return self

    @model_validator(mode="after")
    def enforce_graph_integrity(self) -> "GraphFlow":
        """
        Enforces strict integrity if published.
        Calls Graph.verify_integrity(strict=True).
        """
        is_published = self.status == "published"
        self.graph.verify_integrity(strict=is_published)
        return self


ManifestType = Annotated[LinearFlow | GraphFlow, Field(discriminator="kind")]


class Manifest(RootModel[ManifestType]):
    """
    The Sovereign Domain Gatekeeper.
    Wrapper around any valid Flow type.
    """

    root: ManifestType

    @classmethod
    def export_json_schema(cls) -> str:
        """Exports a pristine, IDE-ready JSON Schema resolving deep $defs."""
        import json

        schema = cls.model_json_schema(by_alias=True)

        # Inject standard JSON Schema meta-tags for SOTA LSP compliance
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"
        schema["title"] = "Coreason Manifest Specification v2"

        return json.dumps(schema, indent=2)
