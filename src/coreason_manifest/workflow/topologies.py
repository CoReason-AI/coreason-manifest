# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.workflow.nodes import AnyNode


class DiversityConstraint(CoreasonBaseModel):
    """
    Constraints enforcing cognitive heterogeneity.
    """

    min_adversaries: int = Field(
        description="The minimum number of adversarial or 'Devil's Advocate' roles required to prevent groupthink."
    )
    model_variance_required: bool = Field(
        description="If True, forces the orchestrator to route sub-agents to different foundational models."
    )
    temperature_variance: float | None = Field(
        default=None, description="Required statistical variance in temperature settings across the council."
    )


class BackpressurePolicy(CoreasonBaseModel):
    """
    Declarative backpressure constraints.
    """

    max_queue_depth: int = Field(
        description="The maximum number of unprocessed messages/observations "
        "allowed between connected nodes before yielding."
    )
    token_budget_per_branch: float | None = Field(
        default=None, description="The maximum token cost allowed per execution branch before rate-limiting."
    )


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
    backpressure: BackpressurePolicy | None = Field(
        default=None, description="Declarative backpressure constraints for the graph edges."
    )


class CouncilTopology(BaseTopology):
    """
    A Council workflow topology involving multiple voting members and an adjudicator.
    """

    type: Literal["council"] = Field(default="council", description="Discriminator for a Council topology.")
    adjudicator_id: NodeID = Field(description="The NodeID of the adjudicator that synthesizes the council's output.")
    diversity_policy: DiversityConstraint | None = Field(
        default=None, description="Constraints enforcing cognitive heterogeneity across the council."
    )


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
