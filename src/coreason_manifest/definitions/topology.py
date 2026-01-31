# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_maco

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class StateSchema(BaseModel):
    """Defines the structure and persistence of the graph state.

    Attributes:
        data_schema: A JSON Schema or Pydantic definition describing the state structure.
        persistence: Configuration for how state is checkpointed.
    """

    model_config = ConfigDict(extra="forbid")

    data_schema: Dict[str, Any] = Field(
        ..., description="A JSON Schema or Pydantic definition describing the state structure."
    )
    persistence: str = Field(..., description="Configuration for how state is checkpointed (e.g., 'memory', 'redis').")


class CouncilConfig(BaseModel):
    """Configuration for 'Architectural Triangulation'.

    Attributes:
        strategy: The strategy for the council (e.g., 'consensus').
        voters: List of agents or models that vote.
    """

    model_config = ConfigDict(extra="forbid")

    strategy: str = Field(default="consensus", description="The strategy for the council, e.g., 'consensus'.")
    voters: List[str] = Field(..., description="List of agents or models that vote.")


class VisualMetadata(BaseModel):
    """Data explicitly for the UI.

    Attributes:
        label: The label to display for the node.
        x_y_coordinates: The X and Y coordinates for the node on the canvas.
        icon: The icon to represent the node.
        animation_style: The animation style for the node.
    """

    model_config = ConfigDict(extra="forbid")

    label: Optional[str] = Field(None, description="The label to display for the node.")
    x_y_coordinates: Optional[List[float]] = Field(
        None, description="The X and Y coordinates for the node on the canvas."
    )
    icon: Optional[str] = Field(None, description="The icon to represent the node.")
    animation_style: Optional[str] = Field(None, description="The animation style for the node.")


class BaseNode(BaseModel):
    """Base model for all node types.

    Attributes:
        id: Unique identifier for the node.
        council_config: Optional configuration for architectural triangulation.
        visual: Visual metadata for the UI.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique identifier for the node.")
    council_config: Optional[CouncilConfig] = Field(
        None, description="Optional configuration for architectural triangulation."
    )
    visual: Optional[VisualMetadata] = Field(None, description="Visual metadata for the UI.")


class AgentNode(BaseNode):
    """A node that calls a specific atomic agent.

    Attributes:
        type: The type of the node (must be 'agent').
        agent_name: The name of the atomic agent to call.
    """

    type: Literal["agent"] = Field("agent", description="Discriminator for AgentNode.")
    agent_name: str = Field(..., description="The name of the atomic agent to call.")


class HumanNode(BaseNode):
    """A node that pauses execution for user input/approval.

    Attributes:
        type: The type of the node (must be 'human').
        timeout_seconds: Optional timeout in seconds for the user interaction.
    """

    type: Literal["human"] = Field("human", description="Discriminator for HumanNode.")
    timeout_seconds: Optional[int] = Field(None, description="Optional timeout in seconds for the user interaction.")


class LogicNode(BaseNode):
    """A node that executes pure Python logic.

    Attributes:
        type: The type of the node (must be 'logic').
        code: The Python logic code to execute.
    """

    type: Literal["logic"] = Field("logic", description="Discriminator for LogicNode.")
    code: str = Field(..., description="The Python logic code to execute.")


class RecipeNode(BaseNode):
    """A node that executes another Recipe as a sub-graph.

    Attributes:
        type: The type of the node (must be 'recipe').
        recipe_id: The ID of the recipe to execute.
        input_mapping: How parent state maps to child inputs (parent_key -> child_key).
        output_mapping: How child result maps back to parent state (child_key -> parent_key).
    """

    type: Literal["recipe"] = Field("recipe", description="Discriminator for RecipeNode.")
    recipe_id: str = Field(..., description="The ID of the recipe to execute.")
    input_mapping: Dict[str, str] = Field(..., description="Mapping of parent state keys to child input keys.")
    output_mapping: Dict[str, str] = Field(..., description="Mapping of child output keys to parent state keys.")


class MapNode(BaseNode):
    """A node that spawns multiple parallel executions of a sub-branch.

    Attributes:
        type: The type of the node (must be 'map').
        items_path: Dot-notation path to the list in the state.
        processor_node_id: The node (or subgraph) to run for each item.
        concurrency_limit: Max parallel executions.
    """

    type: Literal["map"] = Field("map", description="Discriminator for MapNode.")
    items_path: str = Field(..., description="Dot-notation path to the list in the state.")
    processor_node_id: str = Field(..., description="The node (or subgraph) to run for each item.")
    concurrency_limit: int = Field(..., description="Max parallel executions.")


# Discriminated Union for polymorphism
Node = Annotated[
    Union[AgentNode, HumanNode, LogicNode, RecipeNode, MapNode],
    Field(discriminator="type", description="Polymorphic node definition."),
]


class Edge(BaseModel):
    """Represents a connection between two nodes.

    Attributes:
        source_node_id: The ID of the source node.
        target_node_id: The ID of the target node.
        condition: Optional Python expression for conditional branching.
    """

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., description="The ID of the source node.")
    target_node_id: str = Field(..., description="The ID of the target node.")
    condition: Optional[str] = Field(None, description="Optional Python expression for conditional branching.")


class ConditionalEdge(BaseModel):
    """Represents a dynamic routing connection from one node to multiple potential targets.

    Attributes:
        source_node_id: The ID of the source node.
        router_logic: A reference to a python function or a logic expression that returns the next node ID.
        mapping: A dictionary mapping the router's output (e.g., "approve", "reject") to target Node IDs.
    """

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., description="The ID of the source node.")
    router_logic: str = Field(
        ..., description="A reference to a python function or logic expression that determines the path."
    )
    mapping: Dict[str, str] = Field(..., description="Map of router output values to target node IDs.")


class GraphTopology(BaseModel):
    """The topology definition of the recipe.

    Attributes:
        nodes: List of nodes in the graph.
        edges: List of edges connecting the nodes.
        state_schema: Optional schema definition for the graph state.
    """

    model_config = ConfigDict(extra="forbid")

    nodes: List[Node] = Field(..., description="List of nodes in the graph.")
    edges: List[Union[Edge, ConditionalEdge]] = Field(..., description="List of edges connecting the nodes.")
    state_schema: Optional[StateSchema] = Field(None, description="Schema definition for the graph state.")


Topology = GraphTopology
