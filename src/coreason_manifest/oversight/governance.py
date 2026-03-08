# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file maps the global governance and consensus policy schemas. This is a STRICTLY REGULATORY BOUNDARY.
These schemas define the Zero-Trust information flow constraints of the swarm.
DO NOT inject kinetic execution logic here.
All policies must be declarative, deterministic, and capable of severing memory access instantly.
"""

from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID, SemanticVersion


class ConstitutionalRule(CoreasonBaseModel):
    """
    Defines a constitutional rule for AI governance.
    """

    rule_id: str = Field(description="Unique identifier for the constitutional rule.")
    description: str = Field(description="Detailed description of the rule.")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level if the rule is violated."
    )
    forbidden_intents: set[Annotated[str, StringConstraints(min_length=1)]] = Field(
        description="List of intents that are forbidden by this rule."
    )


class GovernancePolicy(CoreasonBaseModel):
    """
    Defines a governance policy comprising multiple constitutional rules.
    """

    policy_name: str = Field(description="Name of the governance policy.")
    version: SemanticVersion = Field(description="Semantic version of the governance policy.")
    rules: list[ConstitutionalRule] = Field(description="List of constitutional rules included in this policy.")


class PredictionMarketPolicy(CoreasonBaseModel):
    """
    The ruleset governing the market. It enforces Sybil resistance
    (via quadratic staking) and dictates when the market stops trading.
    """

    staking_function: Literal["linear", "quadratic"] = Field(
        description="The mathematical curve applied to stakes. Quadratic enforces Sybil resistance."
    )
    min_liquidity_cents: int = Field(ge=0, description="Minimum liquidity required.")
    convergence_delta_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The threshold indicating the market price has stabilized enough to trigger the resolution oracle.",
    )


class QuorumPolicy(CoreasonBaseModel):
    """The mathematical boundaries required to survive Byzantine failures in a decentralized swarm."""

    max_tolerable_faults: int = Field(
        ge=0,
        description=(
            "The maximum number of actively malicious, hallucinating, or degraded nodes (f) the swarm must survive."
        ),
    )
    min_quorum_size: int = Field(
        gt=0, description="The minimum number of participating agents (N) required to form consensus."
    )
    state_validation_metric: Literal["ledger_hash", "zk_proof", "semantic_embedding"] = Field(
        description="The cryptographic material the agents must sign to submit a valid vote."
    )
    byzantine_action: Literal["quarantine", "slash_escrow", "ignore"] = Field(
        description=(
            "The deterministic punishment executed by the orchestrator against nodes that violate the consensus quorum."
        )
    )

    @model_validator(mode="after")
    def enforce_bft_math(self) -> Self:
        """Mathematically guarantees the network can reach Byzantine agreement."""
        if self.min_quorum_size < (3 * self.max_tolerable_faults) + 1:
            raise ValueError("Byzantine Fault Tolerance requires min_quorum_size (N) >= 3f + 1.")
        return self


class ConsensusPolicy(CoreasonBaseModel):
    """
    Explicit ruleset governing how a council resolves disagreements.
    """

    strategy: Literal["unanimous", "majority", "debate_rounds", "prediction_market", "pbft"] = Field(
        description="The mathematical rule for reaching agreement."
    )
    tie_breaker_node_id: NodeID | None = Field(
        default=None, description="The node authorized to break deadlocks if unanimity or majority fails."
    )
    max_debate_rounds: int | None = Field(
        default=None,
        description="The maximum number of argument/rebuttal cycles permitted before forced adjudication.",
    )
    prediction_market_rules: PredictionMarketPolicy | None = Field(
        default=None,
        description="The strict algorithmic mechanism rules required if the strategy is prediction_market.",
    )
    quorum_rules: QuorumPolicy | None = Field(
        default=None, description="The strict Byzantine fault tolerance limits required if the strategy is 'pbft'."
    )

    @model_validator(mode="after")
    def validate_pbft_requirements(self) -> Self:
        if self.strategy == "pbft" and self.quorum_rules is None:
            raise ValueError("quorum_rules must be provided when strategy is 'pbft'.")
        return self


class FormalVerificationContract(CoreasonBaseModel):
    """
    Passive schema defining a mathematical proof of safety invariants.
    """

    proof_system: Literal["tla_plus", "lean4", "coq", "z3"] = Field(
        description="The mathematical dialect and theorem prover used to compile the proof."
    )
    invariant_theorem: str = Field(
        description=(
            "The exact mathematical assertion or safety invariant being proven "
            "(e.g., 'No data classified as CONFIDENTIAL routes externally')."
        )
    )
    compiled_proof_hash: str = Field(
        description=(
            "The SHA-256 fingerprint of the verified proof object that the Rust/C++ orchestrator must load and check."
        )
    )


class GlobalGovernance(CoreasonBaseModel):
    """
    Global governance bounds for a swarm executing a workflow envelope.
    """

    max_budget_cents: int = Field(
        description="The absolute maximum economic cost allowed for the entire swarm lifecycle."
    )
    max_global_tokens: int = Field(description="The maximum aggregate token usage allowed across all nodes.")
    max_carbon_budget_gco2eq: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "The absolute physical energy footprint allowed for this execution graph. "
            "If exceeded, the orchestrator terminates the swarm."
        ),
    )
    global_timeout_seconds: int = Field(
        ge=0, description="The absolute Time-To-Live (TTL) for the execution envelope before graceful termination."
    )
    formal_verification: FormalVerificationContract | None = Field(
        default=None,
        description="The mathematical proof of structural correctness mandated for this execution graph.",
    )


class AnchoringPolicy(CoreasonBaseModel):
    """
    The mathematical center of gravity preventing epistemic drift and sycophancy in the swarm.
    """

    anchor_prompt_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$", description="The undeniable SHA-256 hash of the core objective."
    )
    max_semantic_drift: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "The maximum allowed cosine deviation from the anchor before the orchestrator forces a state rollback."
        ),
    )
