from typing import Any

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.primitives.types import NodeID


class TestCase(CoreasonModel):
    mock_inputs: dict[str, Any] = Field(
        default_factory=dict, description="Variables to inject into the blackboard at start."
    )
    expected_traversal_path: list[NodeID] = Field(
        default_factory=list, description="List of Node IDs that MUST be hit in sequence."
    )
    assertions: dict[str, Any] = Field(default_factory=dict, description="JSON Schema validations on the final output.")


class FuzzingTarget(CoreasonModel):
    variables: list[str] = Field(default_factory=list, description="Input variables to fuzz.")
    mutators: list[str] = Field(
        default_factory=list,
        description="Mutator strategies to employ.",
        examples=["edge_cases", "adversarial"],
    )
    invariants: dict[str, Any] = Field(default_factory=dict, description="JSON Schema invariants that must hold true.")


class EvalsManifest(CoreasonModel):
    test_cases: list[TestCase] = Field(default_factory=list, description="List of test cases to execute.")
    fuzzing_targets: list[FuzzingTarget] = Field(default_factory=list, description="List of fuzzing targets.")
