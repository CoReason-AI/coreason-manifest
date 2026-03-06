# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

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


class AdjudicationVerdict(CoreasonBaseModel):
    """
    Verdict resulting from grading an LLM behavior or output against a rubric.
    """

    rubric_id: str = Field(description="The ID of the rubric used for adjudication.")
    target_node_id: NodeID = Field(description="The ID of the node that was evaluated.")
    score: int = Field(ge=0, le=100, description="The final score assigned based on the rubric.")
    passed: bool = Field(description="Indicates whether the evaluation passed the threshold.")
    reasoning: str = Field(description="Explanation or reasoning for the verdict and score.")
