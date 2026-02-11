from typing import Literal

from pydantic import BaseModel, ConfigDict

from coreason_manifest.spec.core.nodes import Node


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

    inputs: dict[str, str]
    outputs: dict[str, str]


class Blackboard(BaseModel):
    """Shared, observable memory space."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    variables: dict[str, str]
    persistence: bool


class Step(BaseModel):
    """Wrapper for a linear step."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node: Node


class Graph(BaseModel):
    """Directed execution graph."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    nodes: dict[str, Node]
    edges: list[dict[str, str]]


class LinearFlow(BaseModel):
    """A deterministic script."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["LinearFlow"]
    metadata: FlowMetadata
    sequence: list[Step]


class GraphFlow(BaseModel):
    """Cyclic Graph structure."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["GraphFlow"]
    metadata: FlowMetadata
    interface: FlowInterface
    blackboard: Blackboard | None
    graph: Graph
