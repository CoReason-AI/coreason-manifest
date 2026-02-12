from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    Brain,
    EmergenceInspector,
    HumanNode,
    InspectorNode,
    Placeholder,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.core.tools import ToolPack

# Polymorphic Node Type
AnyNode = Annotated[
    AgentNode | SwitchNode | PlannerNode | HumanNode | Placeholder | InspectorNode | EmergenceInspector,
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
    agents: dict[str, Brain] = Field(default_factory=dict)
    tool_packs: dict[str, ToolPack] = Field(default_factory=dict)


class LinearFlow(BaseModel):
    """A deterministic script."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["LinearFlow"]
    metadata: FlowMetadata
    definitions: FlowDefinitions | None = Field(None, description="Shared registry for reusable components.")
    sequence: list[AnyNode]
    governance: Governance | None = None
    tool_packs: list[ToolPack] = Field(default_factory=list)


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
    tool_packs: list[ToolPack] = Field(default_factory=list)
