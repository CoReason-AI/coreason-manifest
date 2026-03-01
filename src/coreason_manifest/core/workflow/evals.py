from typing import Any

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.primitives.types import NodeID


class ChaosConfig(CoreasonModel, frozen=True):
    latency_ms: int = Field(
        default=0, ge=0, description="Artificial latency to inject into node execution.", examples=[150]
    )
    error_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of forcing a node failure (0.0 to 1.0).", examples=[0.05]
    )
    token_throttle: bool = Field(default=False, description="Simulate a constricted context window.", examples=[True])


class AdversaryProfile(CoreasonModel, frozen=True):
    goal: str = Field(..., description="The adversary's objective.", examples=["Extract PII data."])
    attack_strategy: str = Field(..., description="Methodology.", examples=["Prompt injection via SQL payload."])


class TestCase(CoreasonModel):
    """
    A deterministic test case for an agent graph.
    """

    mock_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Variables to inject into the blackboard at start.",
        examples=[{"user_id": 42}],
    )
    expected_traversal_path: list[NodeID] = Field(
        default_factory=list,
        description="List of Node IDs that MUST be hit in sequence.",
        examples=[["auth_node", "db_node", "response_node"]],
    )
    assertions: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema validations on the final output.", examples=[{"type": "object"}]
    )
    chaos_config: ChaosConfig | None = Field(
        default=None,
        description="Infrastructure faults to apply during this test.",
        examples=[{"latency_ms": 100, "error_rate": 0.0, "token_throttle": False}],
    )
    adversary: AdversaryProfile | None = Field(
        default=None,
        description="Red-team configuration for semantic fuzzing.",
        examples=[{"goal": "Bypass filters.", "attack_strategy": "roleplay"}],
    )


class FuzzingTarget(CoreasonModel):
    """
    Definition of a fuzzing target for automated adversarial probing.
    """

    variables: list[str] = Field(
        default_factory=list, description="Input variables to fuzz.", examples=[["user_prompt"]]
    )
    mutators: list[str] = Field(
        default_factory=list,
        description="Mutator strategies to employ (e.g. 'edge_cases', 'adversarial').",
        examples=[["adversarial"]],
    )
    invariants: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema invariants that must hold true.", examples=[{"type": "object"}]
    )
    adversary: AdversaryProfile | None = Field(
        default=None,
        description="Red-team configuration for stochastic semantic fuzzing.",
        examples=[{"goal": "Leak secrets.", "attack_strategy": "obfuscation"}],
    )


class EvalsManifest(CoreasonModel):
    """
    Manifest defining how an agent graph is deterministically tested.
    """

    test_cases: list[TestCase] = Field(
        default_factory=list,
        description="List of test cases to execute.",
        examples=[[{"mock_inputs": {}, "expected_traversal_path": [], "assertions": {}}]],
    )
    fuzzing_targets: list[FuzzingTarget] = Field(
        default_factory=list,
        description="List of fuzzing targets.",
        examples=[[{"variables": ["input"], "mutators": ["edge_cases"], "invariants": {}}]],
    )
