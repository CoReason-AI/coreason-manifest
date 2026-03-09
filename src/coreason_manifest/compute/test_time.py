# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps test-time computation resources like process reward modeling and escalation
mechanisms. This is a STRICTLY KINETIC BOUNDARY. These schemas dictate non-deterministic scaling boundaries,
probabilistic search trees, and test-time kinetic thresholds. YOU ARE EXPLICITLY FORBIDDEN from injecting
long-term persistent state workflows, database models, or downstream business logic. Operations here translate
strictly to hardware budgets and tensor inferences.
"""

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class SubstrateEnvelope(CoreasonBaseModel):
    """
    AGENT INSTRUCTION: Declarative mathematical boundaries for hardware exhaustion.
    Downstream orchestrators MUST abort routing if node capacity cannot satisfy these bounds.
    """

    algorithmic_token_budget: int = Field(..., gt=0, description="Maximum latent activations permitted.")
    vram_frontier_bound: int = Field(..., gt=0, description="Peak memory footprint threshold in bytes.")
    latency_sla_ms: int = Field(..., gt=0, description="Maximum allowable clock time before forced degradation.")
    probabilistic_exhaustion_halt: bool = Field(
        ...,
        description="Flag to trigger early termination if trajectory models indicate inevitable breach of envelope.",
    )


class DynamicConvergenceSLA(CoreasonBaseModel):
    """Service Level Agreement defining the mathematical conditions for early termination of a reasoning search."""

    convergence_delta_epsilon: float = Field(
        ge=0.0,
        description="The minimal required PRM score improvement across the lookback "
        "window to justify continued compute.",
    )
    lookback_window_steps: int = Field(
        gt=0, description="The N-step temporal window over which the PRM gradient is calculated."
    )
    minimum_reasoning_steps: int = Field(
        gt=0,
        description="The mandatory 'burn-in' period. The orchestrator cannot terminate the search "
        "before this structural depth is reached, preventing premature collapse.",
    )


class ProcessRewardContract(CoreasonBaseModel):
    convergence_sla: DynamicConvergenceSLA | None = Field(
        default=None,
        description="The dynamic circuit breaker that halts the search when PRM variance converges, "
        "preventing VRAM waste.",
    )
    pruning_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="If a ThoughtBranch's prm_score falls below this threshold, "
        "the orchestrator MUST halt its generation.",
    )
    max_backtracks_allowed: int = Field(
        ge=0,
        description="The absolute limit on how many times the agent can start a new branch "
        "before throwing a SystemFaultEvent.",
    )
    evaluator_model_name: str | None = Field(
        default=None,
        description="The specific PRM model used to score the logic (e.g., 'math-prm-v2').",
    )


class EscalationContract(CoreasonBaseModel):
    uncertainty_escalation_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The exact Epistemic Uncertainty score that triggers the opening of the Latent Scratchpad.",
    )
    max_latent_tokens_budget: int = Field(
        gt=0,
        description="The maximum number of hidden tokens the orchestrator is authorized to buy "
        "for the internal monologue.",
    )
    max_test_time_compute_ms: int = Field(
        gt=0,
        description="The physical time limit allowed for the scratchpad search before forcing a timeout.",
    )
