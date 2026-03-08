# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the orchestration topologies. This is a STRICTLY TOPOLOGICAL BOUNDARY.
These schemas dictate the multi-agent graph geometry and decentralized routing mechanics. DO NOT inject procedural
execution code or synchronous blocking loops. Think purely in terms of graph theory, Byzantine fault tolerance, and
multi-agent market dynamics."""

from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.compute.stochastic import CrossoverStrategy, FitnessObjective, MutationPolicy
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.oversight.dlp import InformationFlowPolicy
from coreason_manifest.oversight.governance import ConsensusPolicy
from coreason_manifest.telemetry.schemas import ObservabilityPolicy
from coreason_manifest.workflow.auctions import AuctionPolicy, EscrowPolicy
from coreason_manifest.workflow.markets import MarketResolution, PredictionMarketState
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


class DimensionalProjectionContract(CoreasonBaseModel):
    source_dimensionality: int = Field(gt=0, description="The vector size of the source agent's latent space.")
    target_dimensionality: int = Field(gt=0, description="The vector size of the receiving agent's latent space.")
    isometry_preservation_score: float = Field(
        ge=0.0, le=1.0, description="Mathematical proof of how much semantic meaning survived the translation."
    )
    projection_matrix_hash: str = Field(description="SHA-256 hash of the translation matrix used to map the spaces.")


class OntologicalHandshake(CoreasonBaseModel):
    initiating_node_id: str = Field(description="The node requesting semantic alignment.")
    receiving_node_id: str = Field(description="The node receiving the request.")
    latent_vector_similarity: float = Field(
        ge=-1.0, le=1.0, description="The calculated cosine similarity between their core definitions."
    )
    projection_contract: DimensionalProjectionContract | None = Field(
        default=None, description="The required projection if similarity falls below the required threshold."
    )


class OntologicalAlignmentPolicy(CoreasonBaseModel):
    """
    The pre-flight execution gate forcing agents to mathematically align their latent semantics.
    """

    min_cosine_similarity: float = Field(
        ge=-1.0,
        le=1.0,
        description="The absolute minimum latent vector similarity required to allow swarm communication.",
    )
    require_isometry_proof: bool = Field(
        description="If True, the orchestrator must reject dimensional projections that fall below "
        "a safe isometry preservation score."
    )
    fallback_state_contract: StateContract | None = Field(
        default=None,
        description="The rigid external JSON schema to force agents to use if their "
        "latent vector geometries are hopelessly incommensurable.",
    )


class BackpressurePolicy(CoreasonBaseModel):
    """
    Declarative backpressure constraints.
    """

    max_queue_depth: int = Field(
        description="The maximum number of unprocessed messages/observations "
        "allowed between connected nodes before yielding."
    )
    token_budget_per_branch: int | None = Field(
        default=None, description="The maximum token cost allowed per execution branch before rate-limiting."
    )
    max_tokens_per_minute: int | None = Field(
        default=None,
        gt=0,
        description="The maximum kinetic velocity of token consumption allowed before the circuit breaker trips.",
    )
    max_requests_per_minute: int | None = Field(
        default=None, gt=0, description="The maximum kinetic velocity of API requests allowed."
    )
    max_uninterruptible_span_ms: int | None = Field(
        default=None,
        gt=0,
        description="Systemic heartbeat constraint. A node cannot lock the thread longer than this without yielding "
        "to poll for BargeInInterruptEvents.",
    )
    max_concurrent_tool_invocations: int | None = Field(
        default=None,
        gt=0,
        description="The mathematical integer ceiling to prevent Sybil-like parallel mutations "
        "against the ActionSpace.",
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
    ontological_alignment: OntologicalAlignmentPolicy | None = Field(
        default=None,
        description="The pre-flight execution gate forcing agents to mathematically align their latent "
        "semantics before participating in the topology.",
    )
    council_escrow: EscrowPolicy | None = Field(
        default=None,
        description="The strictly typed mathematical surface area to lock funds specifically "
        "for PBFT council execution and slashing.",
    )

    @model_validator(mode="after")
    def enforce_funded_byzantine_slashing(self) -> Self:
        if (
            self.consensus_policy is not None
            and self.consensus_policy.strategy == "pbft"
            and self.consensus_policy.quorum_rules is not None
            and self.consensus_policy.quorum_rules.byzantine_action == "slash_escrow"
        ) and (self.council_escrow is None or self.council_escrow.escrow_locked_microcents <= 0):
            raise ValueError("Topological Interlock Failed: PBFT with slash_escrow requires a funded council_escrow.")
        return self

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
    active_prediction_markets: list[PredictionMarketState] = Field(
        default_factory=list, description="The live algorithmic betting markets resolving swarm consensus."
    )
    resolved_markets: list[MarketResolution] = Field(
        default_factory=list,
        description="The immutable records of finalized markets and reputation capital distributions.",
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


class SMPCTopology(BaseTopology):
    """
    A Secure Multi-Party Computation topology.
    """

    type: Literal["smpc"] = Field(default="smpc", description="Discriminator for SMPC Topology.")
    smpc_protocol: Literal["garbled_circuits", "secret_sharing", "oblivious_transfer"] = Field(
        description="The exact cryptographic P2P protocol the nodes must use to evaluate the function."
    )
    joint_function_uri: str = Field(
        description="The URI or hash pointing to the exact math circuit or polynomial function "
        "the ring will collaboratively compute."
    )
    participant_node_ids: list[str] = Field(
        min_length=2,
        description="The strict ordered list of NodeIDs participating in the Secure Multi-Party Computation ring.",
    )
    ontological_alignment: OntologicalAlignmentPolicy | None = Field(
        default=None,
        description="The pre-flight execution gate forcing agents to mathematically align their latent "
        "semantics before participating in the topology.",
    )


class SimulationConvergenceSLA(CoreasonBaseModel):
    """
    The statistical limits of the sandbox simulation.
    """

    max_monte_carlo_rollouts: int = Field(
        gt=0,
        description="The absolute physical limit on how many alternate futures the system is allowed to render.",
    )
    variance_tolerance: float = Field(
        ge=0.0,
        le=1.0,
        description="The statistical confidence required to collapse the probability wave early and save GPU VRAM.",
    )


class DigitalTwinTopology(BaseTopology):
    """
    An isolated sandbox graph representing a Digital Twin.
    """

    type: Literal["digital_twin"] = Field(
        default="digital_twin", description="Discriminator for a Digital Twin topology."
    )
    target_topology_id: str = Field(
        description="The identifier (expected to be a W3C DID) pointing to the real-world topology it is cloning."
    )
    convergence_sla: SimulationConvergenceSLA = Field(
        description="The strict mathematical boundaries for the simulation."
    )
    enforce_no_side_effects: bool = Field(
        default=True,
        description="A declarative flag that instructs the runtime to mathematically sever all external write access.",
    )


class EvaluatorOptimizerTopology(BaseTopology):
    """
    A formalized Actor-Critic micro-topology enforcing strict, finite generation-evaluation-revision cycles.
    """

    type: Literal["evaluator_optimizer"] = Field(
        default="evaluator_optimizer", description="Discriminator for an Evaluator-Optimizer loop."
    )
    generator_node_id: NodeID = Field(description="The ID of the actor generating the payload.")
    evaluator_node_id: NodeID = Field(description="The ID of the critic scoring the payload.")
    max_revision_loops: int = Field(
        ge=1, description="The absolute limit on Actor-Critic cycles to prevent infinite compute burn."
    )
    require_multimodal_grounding: bool = Field(
        default=False,
        description="If True, the evaluator_node_id MUST mathematically mask all tokens outside the "
        "MultimodalTokenAnchor during its forward pass to execute pure adversarial Proposer-Critique validation.",
    )

    @model_validator(mode="after")
    def verify_bipartite_nodes(self) -> Self:
        """Mathematically guarantees both the generator and evaluator exist in the node registry."""
        if self.generator_node_id not in self.nodes:
            raise ValueError(f"Generator node '{self.generator_node_id}' not found in topology nodes.")
        if self.evaluator_node_id not in self.nodes:
            raise ValueError(f"Evaluator node '{self.evaluator_node_id}' not found in topology nodes.")
        if self.generator_node_id == self.evaluator_node_id:
            raise ValueError("Generator and Evaluator cannot be the same node.")
        return self


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyTopology union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyTopology = Annotated[
    DAGTopology
    | CouncilTopology
    | SwarmTopology
    | EvolutionaryTopology
    | SMPCTopology
    | EvaluatorOptimizerTopology
    | DigitalTwinTopology,
    Field(discriminator="type", description="A discriminated union of workflow topologies."),
]
