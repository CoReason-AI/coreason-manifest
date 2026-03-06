# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.compute.stochastic import CrossoverStrategy, FitnessObjective, MutationPolicy
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.oversight.dlp import InformationFlowPolicy
from coreason_manifest.oversight.governance import ConsensusPolicy
from coreason_manifest.telemetry.schemas import ObservabilityPolicy
from coreason_manifest.workflow.auctions import AuctionPolicy
from coreason_manifest.workflow.nodes import AnyNode


class StateContract(CoreasonBaseModel):
    """
    A strict Cryptographic State Contract (Typed Blackboard) for multi-agent memory sharing.
    """

    schema_definition: dict[str, Any] = Field(
        description="A strict JSON Schema dictionary defining the required shape of the shared memory blackboard."
    )
    strict_validation: bool = Field(
        default=True,
        description="If True, the orchestrator must reject any state mutation that fails the schema definition.",
    )


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
    shared_state_contract: StateContract | None = Field(
        default=None, description="The schema-on-write contract governing the internal state of this topology."
    )
    information_flow: InformationFlowPolicy | None = Field(
        default=None,
        description="The structural Data Loss Prevention (DLP) contract governing all state mutations in this "
        "topology.",
    )
    observability: ObservabilityPolicy | None = Field(
        default=None, description="The distributed tracing rules bound to this specific execution graph."
    )


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

        # Step 2: Cycle detection (Iterative DFS to avoid RecursionError CWE-674)
        if not self.allow_cycles:
            adj: dict[NodeID, list[NodeID]] = {node_id: [] for node_id in self.nodes}
            for source, target in self.edges:
                adj[source].append(target)

            visited: set[NodeID] = set()
            recursion_stack: set[NodeID] = set()

            for start_node in self.nodes:
                if start_node in visited:
                    continue

                # The stack holds tuples of (node, neighbor_iterator)
                # This explicitly replicates the system call stack on the heap.
                stack = [(start_node, iter(adj[start_node]))]
                visited.add(start_node)
                recursion_stack.add(start_node)

                while stack:
                    curr, neighbors = stack[-1]
                    try:
                        neighbor = next(neighbors)
                        if neighbor not in visited:
                            visited.add(neighbor)
                            recursion_stack.add(neighbor)
                            stack.append((neighbor, iter(adj[neighbor])))
                        elif neighbor in recursion_stack:
                            raise ValueError("Graph contains cycles but allow_cycles is False.")
                    except StopIteration:
                        recursion_stack.remove(curr)
                        stack.pop()

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
    consensus_policy: ConsensusPolicy | None = Field(
        default=None, description="The explicit ruleset governing how the council resolves disagreements."
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
    max_concurrent_agents: int = Field(
        default=10, le=100, description="The absolute ceiling for concurrent agent threads."
    )
    auction_policy: AuctionPolicy | None = Field(
        default=None, description="The mathematical policy governing task decentralization via Spot Markets."
    )

    @model_validator(mode="after")
    def enforce_concurrency_ceiling(self) -> Self:
        if self.spawning_threshold > self.max_concurrent_agents:
            raise ValueError("spawning_threshold cannot exceed max_concurrent_agents")
        return self


class EvolutionaryTopology(BaseTopology):
    """
    An Evolutionary workflow topology that mutates and breeds agents over generations.
    """

    type: Literal["evolutionary"] = Field(
        default="evolutionary", description="Discriminator for an Evolutionary topology."
    )
    generations: int = Field(description="The absolute limit on evolutionary breeding cycles.")
    population_size: int = Field(description="The number of concurrent agents instantiated per generation.")
    mutation: MutationPolicy = Field(description="The constraints governing random heuristic mutations.")
    crossover: CrossoverStrategy = Field(description="The mathematical rules for combining elite agents.")
    fitness_objectives: list[FitnessObjective] = Field(
        description="The multi-dimensional criteria used to score and cull the population."
    )

    @model_validator(mode="after")
    def sort_objectives(self) -> Self:
        object.__setattr__(
            self, "fitness_objectives", sorted(self.fitness_objectives, key=lambda obj: obj.target_metric)
        )
        return self


type AnyTopology = Annotated[
    DAGTopology | CouncilTopology | SwarmTopology | EvolutionaryTopology,
    Field(discriminator="type", description="A discriminated union of workflow topologies."),
]
