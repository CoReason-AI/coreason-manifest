# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import uuid
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from coreason_manifest.spec.base import CoreasonBaseState


class IdeationPhase(StrEnum):
    """
    Thermodynamic Phase Tracking for stochastic ideation.
    """

    STOCHASTIC_DIFFUSION = "STOCHASTIC_DIFFUSION"
    ENTROPIC_EXPLORATION = "ENTROPIC_EXPLORATION"
    TOPOLOGICAL_CRITIQUE = "TOPOLOGICAL_CRITIQUE"
    MANIFOLD_COLLAPSE = "MANIFOLD_COLLAPSE"


class StochasticStateNode(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Generate unbounded semantic structures. Do not constrain text outputs. Evaluate and assign an epistemic entropy score reflecting the variance/uncertainty of the node.
    CAUSAL AFFORDANCE: Represents a discrete semantic coordinate in the latent state-space MCTS DAG prior to mathematical collapse.
    EPISTEMIC BOUNDS: The semantic string is topologically unbounded (infinite length/complexity), but the epistemic entropy is strictly locked between 0.0 and 1.0.
    MCP ROUTING TRIGGERS: Routes to stochastic text-generation or critique models. NEVER routes to deterministic compilers or verified execution environments.
    """

    node_cid: uuid.UUID = Field(default_factory=uuid.uuid4)
    parent_node_cid: uuid.UUID | None = None
    agent_role: Literal["generator", "critic", "synthesizer"]
    stochastic_tensor: str
    epistemic_entropy: float

    @field_validator("epistemic_entropy")
    @classmethod
    def validate_entropy_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"epistemic_entropy must be between 0.0 and 1.0, got {v}")
        return v


class StochasticConsensus(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Synthesize divergent MCTS coordinates into a cohesive, proposed structure. Clearly identify and list any unresolved topological holes (contradictions) in residual_entropy_vectors.
    CAUSAL AFFORDANCE: Prepares the high-dimensional, high-entropy semantic manifold for a lossy projection into a deterministic, algebraic structure.
    EPISTEMIC BOUNDS: The confidence score must be mathematically bound between 0.0 and 1.0.
    MCP ROUTING TRIGGERS: Routes to high-context synthesizer models designed for TDA (Topological Data Analysis) and homology resolution.
    """

    consensus_cid: uuid.UUID = Field(default_factory=uuid.uuid4)
    proposed_manifold: str
    convergence_confidence: float
    residual_entropy_vectors: list[str]

    @field_validator("convergence_confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"convergence_confidence must be between 0.0 and 1.0, got {v}")
        return v


class StochasticTopology(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Populate the root topology. Add nodes to the stochastic graph to build the DAG. Do not attempt to alter the epistemic status.
    CAUSAL AFFORDANCE: Acts as the absolute, immutable mathematical container for unbounded semantic exploration, preventing entropic overflow into deterministic domains.
    EPISTEMIC BOUNDS: Strictly stochastically unbounded. No deterministic guarantees can be extracted from this topology.
    MCP ROUTING TRIGGERS: Root state object for the entire ideation/diffusion epoch.
    """

    topology_cid: uuid.UUID = Field(default_factory=uuid.uuid4)
    topology_type: Literal["stochastic_ensemble"] = "stochastic_ensemble"
    phase: IdeationPhase
    stochastic_graph: list[StochasticStateNode]
    consensus: StochasticConsensus | None = None
    epistemic_status: Literal["stochastically_unbounded"] = "stochastically_unbounded"

    @model_validator(mode="after")
    def validate_dag_integrity(self) -> "StochasticTopology":
        node_cids = {node.node_cid for node in self.stochastic_graph}
        for node in self.stochastic_graph:
            if node.parent_node_cid is not None and node.parent_node_cid not in node_cids:
                raise ValueError(
                    f"Referential integrity failure: parent_node_cid {node.parent_node_cid} "
                    f"does not exist in the stochastic_graph."
                )
        return self
