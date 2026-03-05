# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

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
    edges: list[tuple[NodeID, NodeID]] = Field(default_factory=list, description="List of edges between nodes.")
    allow_cycles: bool = Field(
        default=False,
        description="Configuration indicating if cycles are allowed during validation.",
    )
    backpressure: BackpressurePolicy | None = Field(
        default=None, description="Declarative backpressure constraints for the graph edges."
    )

    @model_validator(mode="after")
    def verify_edges_exist(self) -> Self:
        # Step 1: Referential integrity
        for source, target in self.edges:
            if source not in self.nodes:
                raise ValueError(f"Edge source '{source}' does not exist in nodes registry.")
            if target not in self.nodes:
                raise ValueError(f"Edge target '{target}' does not exist in nodes registry.")

        # Step 2: Cycle detection
        if not self.allow_cycles:
            adj: dict[NodeID, list[NodeID]] = {node_id: [] for node_id in self.nodes}
            for source, target in self.edges:
                adj[source].append(target)

            visited: set[NodeID] = set()
            recursion_stack: set[NodeID] = set()

            def dfs(node: NodeID) -> bool:
                visited.add(node)
                recursion_stack.add(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in recursion_stack:
                        return True
                recursion_stack.remove(node)
                return False

            for node in self.nodes:
                if node not in visited and dfs(node):
                    raise ValueError("Graph contains cycles but allow_cycles is False.")

        return self


class CouncilTopology(BaseTopology):
    """
    A Council workflow topology involving multiple voting members and an adjudicator.
    """

    type: Literal["council"] = Field(default="council", description="Discriminator for a Council topology.")
    adjudicator_id: NodeID = Field(description="The NodeID of the adjudicator that synthesizes the council's output.")
    diversity_policy: DiversityConstraint | None = Field(
        default=None, description="Constraints enforcing cognitive heterogeneity across the council."
    )

    @model_validator(mode="after")
    def check_adjudicator_id(self) -> Self:
        if self.adjudicator_id not in self.nodes:
            raise ValueError(f"Adjudicator ID '{self.adjudicator_id}' is not in nodes registry.")
        return self


class SwarmTopology(BaseTopology):
    """
    A dynamic Swarm workflow topology.
    """

    type: Literal["swarm"] = Field(default="swarm", description="Discriminator for a Swarm topology.")
    spawning_threshold: int = Field(
        default=3,
        description="Threshold limit for dynamic spawning of additional nodes.",
    )
    max_concurrent_agents: int = Field(default=10, description="The absolute ceiling for concurrent agent threads.")

    @model_validator(mode="after")
    def enforce_concurrency_ceiling(self) -> Self:
        if self.spawning_threshold > self.max_concurrent_agents:
            raise ValueError("spawning_threshold cannot exceed max_concurrent_agents")
        return self


type AnyTopology = Annotated[
    DAGTopology | CouncilTopology | SwarmTopology,
    Field(discriminator="type", description="A discriminated union of workflow topologies."),
]
