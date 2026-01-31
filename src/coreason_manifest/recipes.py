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

from .models import VersionStr


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


# Discriminated Union for polymorphism
Node = Annotated[
    Union[AgentNode, HumanNode, LogicNode], Field(discriminator="type", description="Polymorphic node definition.")
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


class GraphTopology(BaseModel):
    """The topology definition of the recipe.

    Attributes:
        nodes: List of nodes in the graph.
        edges: List of edges connecting the nodes.
    """

    model_config = ConfigDict(extra="forbid")

    nodes: List[Node] = Field(..., description="List of nodes in the graph.")
    edges: List[Edge] = Field(..., description="List of edges connecting the nodes.")


class RecipeManifest(BaseModel):
    """The executable specification for the MACO engine.

    Attributes:
        id: Unique identifier for the recipe.
        version: Version of the recipe.
        name: Human-readable name of the recipe.
        description: Detailed description of the recipe.
        inputs: Schema defining global variables this recipe accepts.
        graph: The topology definition of the workflow.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique identifier for the recipe.")
    version: VersionStr = Field(..., description="Version of the recipe.")
    name: str = Field(..., description="Human-readable name of the recipe.")
    description: Optional[str] = Field(None, description="Detailed description of the recipe.")
    inputs: Dict[str, Any] = Field(..., description="Schema defining global variables this recipe accepts.")
    graph: GraphTopology = Field(..., description="The topology definition of the workflow.")
