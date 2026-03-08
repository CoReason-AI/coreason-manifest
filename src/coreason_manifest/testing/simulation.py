# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file defines the strict topological gas limits for synthetic data generation and fuzzing.
This is a STRICTLY ADVERSARIAL BOUNDARY. These schemas dictate the absolute physical limits
of cyclic/fractal graph expansion during test-time compute and red-teaming. DO NOT introduce
active recursive loops here.
"""

from typing import Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class GenerativeManifoldSLA(CoreasonBaseModel):
    """Mathematical governor for fractal/cyclic graph synthesis."""

    max_topological_depth: int = Field(
        ge=1, description="The absolute physical depth limit for recursive encapsulation."
    )
    max_node_fanout: int = Field(
        ge=1, description="The maximum number of horizontally connected nodes per topology tier."
    )
    max_synthetic_tokens: int = Field(ge=1, description="The economic constraint on the entire generated mock payload.")

    @model_validator(mode="after")
    def enforce_geometric_bounds(self) -> Self:
        """Mathematically guarantees the configuration cannot authorize an OOM explosion."""
        if self.max_topological_depth * self.max_node_fanout > 1000:
            raise ValueError("Geometric explosion risk: max_topological_depth * max_node_fanout must be <= 1000.")
        return self


class SyntheticGenerationProfile(CoreasonBaseModel):
    """Authoritative blueprint for external fuzzing and simulation engines."""

    profile_id: str = Field(min_length=1, description="Unique identifier for this simulation profile.")
    manifold_sla: GenerativeManifoldSLA = Field(description="The structural topological gas limit.")
    target_schema_ref: str = Field(min_length=1, description="The string name of the Pydantic class to synthesize.")
