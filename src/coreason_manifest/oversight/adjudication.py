# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file maps the algorithmic adjudication schemas. This is a STRICTLY REGULATORY BOUNDARY.
These schemas define the Zero-Trust information flow constraints of the swarm.
DO NOT inject kinetic execution logic here.
All policies must be declarative, deterministic, and capable of severing memory access instantly.
"""

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class GradingCriteria(CoreasonBaseModel):
    """
    Defines criteria used for grading LLM behavior or output.
    """

    criterion_id: str = Field(description="Unique identifier for the grading criterion.")
    description: str = Field(description="Detailed description of what is being graded.")
    weight: float = Field(ge=0.0, description="Weight or significance of this criterion.")


class AdjudicationRubric(CoreasonBaseModel):
    """
    Rubric defining multiple criteria and passing threshold for algorithmic adjudication.
    """

    rubric_id: str = Field(description="Unique identifier for the rubric.")
    criteria: list[GradingCriteria] = Field(description="List of criteria used in the rubric.")
    passing_threshold: float = Field(ge=0.0, le=100.0, description="The minimum score required to pass.")

    @model_validator(mode="after")
    def _validate_positive_weight_sum(self) -> "AdjudicationRubric":
        """AGENT INSTRUCTION: Mathematically guarantee L1 norm > 0.0 to prevent downstream orchestrator panics."""
        total_weight = sum(c.weight for c in self.criteria)
        if total_weight <= 0.0:
            raise ValueError(
                "AdjudicationRubric rejected: The sum of all GradingCriteria weights "
                "must be strictly greater than 0.0 to prevent topological DoS (division "
                "by zero) in downstream consensus engines."
            )
        return self


class AdjudicationVerdict(CoreasonBaseModel):
    """
    Verdict resulting from grading an LLM behavior or output against a rubric.
    """

    rubric_id: str = Field(description="The ID of the rubric used for adjudication.")
    target_node_id: NodeID = Field(description="The ID of the node that was evaluated.")
    score: int = Field(ge=0, le=100, description="The final score assigned based on the rubric.")
    passed: bool = Field(description="Indicates whether the evaluation passed the threshold.")
    reasoning: str = Field(description="Explanation or reasoning for the verdict and score.")
