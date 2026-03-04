from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID  # noqa: TC001
from coreason_manifest.workflow.nodes import AnyNode  # noqa: TC001


class BaseTopology(CoreasonBaseModel):
    """
    Base configuration for any workflow topology.
    """

    nodes: dict[NodeID, AnyNode] = Field(description="Flat registry of all nodes in this topology.")


class DAGTopology(BaseTopology):
    """
    A Directed Acyclic Graph workflow topology.
    """

    type: Literal["dag"] = Field(default="dag", description="Discriminator for a DAG topology.")
    allow_cycles: bool = Field(
        default=False,
        description="Configuration indicating if cycles are allowed during validation.",
    )


class CouncilTopology(BaseTopology):
    """
    A Council workflow topology involving multiple voting members and an adjudicator.
    """

    type: Literal["council"] = Field(default="council", description="Discriminator for a Council topology.")
    adjudicator_id: NodeID = Field(description="The NodeID of the adjudicator that synthesizes the council's output.")


class SwarmTopology(BaseTopology):
    """
    A dynamic Swarm workflow topology.
    """

    type: Literal["swarm"] = Field(default="swarm", description="Discriminator for a Swarm topology.")
    spawning_threshold: int = Field(
        default=3,
        description="Threshold limit for dynamic spawning of additional nodes.",
    )


type AnyTopology = Annotated[
    DAGTopology | CouncilTopology | SwarmTopology,
    Field(discriminator="type", description="A discriminated union of workflow topologies."),
]
