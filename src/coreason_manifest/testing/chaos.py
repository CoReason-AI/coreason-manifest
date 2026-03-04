from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel

type FaultType = Literal[
    "context_overload",
    "incorrect_context",
    "format_corruption",
    "latency_spike",
    "token_throttle",
]


class FaultInjectionProfile(CoreasonBaseModel):
    fault_type: FaultType = Field(description="The specific type of fault to inject.")
    target_node_id: str | None = Field(default=None, description="The specific node to attack, or None for swarm-wide.")
    intensity: float = Field(description="The severity of the fault, represented from 0.0 to 1.0.")


class SteadyStateHypothesis(CoreasonBaseModel):
    expected_max_latency: float = Field(description="The expected maximum latency under normal conditions.")
    max_loops_allowed: int = Field(description="The maximum allowed loops for the swarm to reach a conclusion.")
    required_tool_usage: list[str] | None = Field(
        default=None, description="A list of required tools that must be utilized."
    )


class ChaosExperiment(CoreasonBaseModel):
    experiment_id: str = Field(description="The unique identifier for the chaos experiment.")
    hypothesis: SteadyStateHypothesis = Field(description="The baseline steady state hypothesis being tested.")
    faults: list[FaultInjectionProfile] = Field(
        description="The list of fault injection profiles defining the chaotic elements."
    )
