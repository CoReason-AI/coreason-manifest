from collections.abc import Iterable
from typing import Annotated, Any, Literal

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


class FlowInterface(BaseModel):
    """Input/Output JSON schema contracts."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    inputs: dict[str, Any]
    outputs: dict[str, Any]


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
    valid_policies = definitions.supervision_templates.keys() if definitions else set()

    # SOTA: Create a set of all available tools from registered packs
    valid_tools = set()
    if definitions and definitions.tool_packs:
        for pack in definitions.tool_packs.values():
            valid_tools.update(pack.tools)

    for node in nodes:
        # Global Supervision Template Check
        if isinstance(node.supervision, str):
            if node.supervision.startswith("ref:"):
                ref_id = node.supervision[4:]  # Strip 'ref:' prefix
                if ref_id not in valid_policies:
                    raise ValueError(f"Node '{node.id}' references undefined supervision template ID '{ref_id}'")
            else:
                raise ValueError(
                    f"Node '{node.id}' has invalid supervision reference '{node.supervision}'. Must start with 'ref:'"
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
    metadata: FlowMetadata
    definitions: FlowDefinitions | None = Field(None, description="Shared registry for reusable components.")
    sequence: list[AnyNode]
    governance: Governance | None = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "LinearFlow":
        """Ensures all string-based profile references point to a valid definition."""
        validate_integrity(self.definitions, self.sequence)
        return self


class GraphFlow(BaseModel):
    """Cyclic Graph structure."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["GraphFlow"]
    metadata: FlowMetadata
    definitions: FlowDefinitions | None = Field(None, description="Shared registry for reusable components.")
    interface: FlowInterface
    blackboard: Blackboard | None
    graph: Graph
    governance: Governance | None = None

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "GraphFlow":
        """Ensures all string-based profile references point to a valid definition."""
        validate_integrity(self.definitions, self.graph.nodes.values())
        return self
