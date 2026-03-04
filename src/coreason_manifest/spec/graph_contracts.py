from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SemanticTraversalRequest(BaseModel):
    """
    Contract representing a request for a semantic traversal of a graph structure.
    Strictly declarative; it does not contain syntax for database operations.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    semantic_intent: str = Field(..., description="The high-level objective.")
    anchor_nodes: list[str] = Field(..., description="Strict entry points.")
    max_hops: int = Field(..., description="Depth limit to prevent graph explosion.")
    allowed_edge_types: list[str] = Field(..., description="Strict boundary filters.")


class GraphNode(BaseModel):
    """
    Model representing a node in a knowledge graph.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str = Field(..., description="The unique identifier of the node.")
    properties: dict[str, Any] = Field(default_factory=dict, description="Metadata properties.")
    embedding: list[float] | None = Field(default=None, description="Vector embedding for the node.")


class GraphEdge(BaseModel):
    """
    Model representing a directed edge between two graph nodes.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    source: str = Field(..., description="The unique identifier of the source node.")
    target: str = Field(..., description="The unique identifier of the target node.")
    edge_type: str = Field(..., description="The type/label of the edge.")
    properties: dict[str, Any] = Field(default_factory=dict, description="Metadata properties.")


class SubgraphResponse(BaseModel):
    """
    Strictly typed response returning the topology of a requested traversal.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    nodes: list[GraphNode] = Field(..., description="Nodes retrieved.")
    edges: list[GraphEdge] = Field(..., description="Edges retrieved.")
