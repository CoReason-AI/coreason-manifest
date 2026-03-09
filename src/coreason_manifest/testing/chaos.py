# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file defines the Chaos Engineering schemas. This is a STRICTLY ADVERSARIAL BOUNDARY.
These models are not unit tests; they are systemic fault injectors designed to perturb the live
swarm topology (e.g., node latency, memory corruption, topological severing).
Do not write standard QA schemas here. Focus entirely on Blast Radius and Steady-State Hypotheses.
"""

from typing import Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type FaultType = Literal[
    "context_overload",
    "incorrect_context",
    "format_corruption",
    "latency_spike",
    "token_throttle",
    "network_degradation",
    "temporal_dilation",
    "dependency_blackout",
]


class FaultInjectionProfile(CoreasonBaseModel):
    fault_type: FaultType = Field(description="The specific type of fault to inject.")
    target_node_id: str | None = Field(default=None, description="The specific node to attack, or None for swarm-wide.")
    intensity: float = Field(description="The severity of the fault, represented from 0.0 to 1.0.")


class SteadyStateHypothesis(CoreasonBaseModel):
    expected_max_latency: float = Field(ge=0.0, description="The expected maximum latency under normal conditions.")
    max_loops_allowed: int = Field(description="The maximum allowed loops for the swarm to reach a conclusion.")
    required_tool_usage: list[str] | None = Field(
        default=None, description="A list of required tools that must be utilized."
    )


class SimulationEscrow(CoreasonBaseModel):
    locked_magnitude: int = Field(
        gt=0,
        description="The strictly typed boundary requiring locked magnitude "
        "to prevent zero-cost griefing of the swarm.",
    )


class ExogenousEpistemicShock(CoreasonBaseModel):
    shock_id: str = Field(min_length=1, description="Cryptographic identifier for the Black Swan event.")
    target_node_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="Regex-bound SHA-256 string targeting a specific Merkle root in the epistemic graph.",
    )
    bayesian_surprise_score: float = Field(
        ge=0.0,
        allow_inf_nan=False,
        description="Strictly bounded mathematical quantification of the epistemic decay or Variational Free Energy.",
    )
    synthetic_payload: dict[str, Any] = Field(
        description="Bounded dictionary representing the injected hallucination or observation."
    )
    escrow: SimulationEscrow = Field(description="The cryptographic Proof-of-Stake funding the shock.")

    @model_validator(mode="after")
    def enforce_economic_escrow(self) -> Self:
        if self.escrow.locked_magnitude <= 0:
            raise ValueError("ExogenousEpistemicShock requires a strictly positive escrow to execute.")
        return self


class ChaosExperiment(CoreasonBaseModel):
    experiment_id: str = Field(description="The unique identifier for the chaos experiment.")
    hypothesis: SteadyStateHypothesis = Field(description="The baseline steady state hypothesis being tested.")
    faults: list[FaultInjectionProfile] = Field(
        description="The list of fault injection profiles defining the chaotic elements."
    )
    shocks: list[ExogenousEpistemicShock] = Field(
        default_factory=list,
        description="The declarative list of exogenous Black Swan events injected into the topology.",
    )
