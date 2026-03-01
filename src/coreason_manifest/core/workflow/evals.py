from typing import Any

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.primitives.types import NodeID


class ChaosConfig(CoreasonModel, frozen=True):
    latency_ms: int = Field(default=0, description="Artificial latency to inject into node execution.")
    error_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of forcing a node failure (0.0 to 1.0)."
    )
    token_throttle: bool = Field(default=False, description="Simulate a constricted context window.")


class AdversaryProfile(CoreasonModel, frozen=True):
    goal: str = Field(..., description="The adversary's objective.")
    attack_strategy: str = Field(..., description="Methodology.")


class TestCase(CoreasonModel):
    """
    A deterministic test case for an agent graph.
    """

    mock_inputs: dict[str, Any] = Field(
        default_factory=dict, description="Variables to inject into the blackboard at start."
    )
    expected_traversal_path: list[NodeID] = Field(
        default_factory=list, description="List of Node IDs that MUST be hit in sequence."
    )
    assertions: dict[str, Any] = Field(default_factory=dict, description="JSON Schema validations on the final output.")
    chaos_config: ChaosConfig | None = Field(
        default=None, description="Infrastructure faults to apply during this test."
    )
    adversary: AdversaryProfile | None = Field(default=None, description="Red-team configuration for semantic fuzzing.")


class FuzzingTarget(CoreasonModel):
    """
    Definition of a fuzzing target for automated adversarial probing.
    """

    variables: list[str] = Field(default_factory=list, description="Input variables to fuzz.")
    mutators: list[str] = Field(
        default_factory=list, description="Mutator strategies to employ (e.g. 'edge_cases', 'adversarial')."
    )
    invariants: dict[str, Any] = Field(default_factory=dict, description="JSON Schema invariants that must hold true.")


class EvalsManifest(CoreasonModel):
    """
    Manifest defining how an agent graph is deterministically tested.
    """

    test_cases: list[TestCase] = Field(default_factory=list, description="List of test cases to execute.")
    fuzzing_targets: list[FuzzingTarget] = Field(default_factory=list, description="List of fuzzing targets.")
