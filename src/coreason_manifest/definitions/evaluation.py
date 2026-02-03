# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import List, Optional

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.base import CoReasonBaseModel


class SuccessCriterion(CoReasonBaseModel):
    """A model defining a single condition for success.

    Attributes:
        name: Name of the criterion (e.g., "json_schema_validity").
        description: Description of the criterion.
        threshold: Threshold for success (e.g., 0.95 for semantic similarity).
        strict: Whether the criterion is strict.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Name of the criterion (e.g., 'json_schema_validity')")
    description: Optional[str] = Field(None, description="Description of the criterion")
    threshold: Optional[float] = Field(None, description="Threshold for success (e.g., 0.95 for semantic similarity)")
    strict: bool = Field(default=True, description="Whether the criterion is strict")


class EvaluationProfile(CoReasonBaseModel):
    """The main container for evaluation configuration.

    Attributes:
        expected_latency_ms: SLA for response time in milliseconds.
        golden_dataset_uri: URI to a reference dataset.
        grading_rubric: List of criteria for grading.
        evaluator_model: Model to use for evaluation (e.g., "gpt-4-turbo").
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_latency_ms: Optional[int] = Field(None, description="SLA for response time in milliseconds")
    golden_dataset_uri: Optional[str] = Field(None, description="URI to a reference dataset")
    grading_rubric: Optional[List[SuccessCriterion]] = Field(None, description="List of criteria for grading")
    evaluator_model: Optional[str] = Field(None, description="Model to use for evaluation (e.g., 'gpt-4-turbo')")
