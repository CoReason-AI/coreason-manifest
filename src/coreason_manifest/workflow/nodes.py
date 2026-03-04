from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class BaseNode(CoreasonBaseModel):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(description="A description of the node's function.")


class AgentNode(BaseNode):
    """
    A node representing an autonomous agent.
    """

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")


class HumanNode(BaseNode):
    """
    A node representing a human participant in the workflow.
    """

    type: Literal["human"] = Field(default="human", description="Discriminator for a Human node.")


class SystemNode(BaseNode):
    """
    A node representing a deterministic system capability.
    """

    type: Literal["system"] = Field(default="system", description="Discriminator for a System node.")


type AnyNode = Annotated[
    AgentNode | HumanNode | SystemNode,
    Field(
        discriminator="type",
        description="A discriminated union of all valid workflow nodes.",
    ),
]
