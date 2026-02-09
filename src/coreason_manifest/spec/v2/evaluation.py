# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import ManifestBaseModel


class SuccessCriterion(ManifestBaseModel):
    """A specific criterion for evaluating agent success."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Unique identifier for the criterion.")
    description: str = Field(..., description="Human-readable explanation.")
    threshold: float = Field(..., description="Numerical success threshold, e.g., 0.95.")
    strict: bool = Field(True, description="Whether failure blocks deployment.")


class EvaluationProfile(ManifestBaseModel):
    """Metadata describing how an agent should be evaluated."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    expected_latency_ms: int | None = Field(None, description="SLA for response time.")
    golden_dataset_uri: str | None = Field(None, description="Reference to test data.")
    evaluator_model: str | None = Field(None, description="Model ID used for LLM-as-a-judge.")
    grading_rubric: list[SuccessCriterion] = Field(default_factory=list, description="List of criteria.")
