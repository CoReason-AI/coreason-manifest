# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class ProvenanceData(CoReasonBaseModel):
    """Metadata tracking the origin and authorship of the workflow."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["ai", "human", "hybrid"] = Field(
        ..., description="The type of entity that created this workflow."
    )
    generated_by: str | None = Field(
        None, description="The specific model or system ID that generated this manifest."
    )
    generated_date: datetime | None = Field(
        None, description="The timestamp when this manifest was generated."
    )
    rationale: str | None = Field(
        None, description="Reasoning behind the creation or selection of this workflow."
    )
    original_intent: str | None = Field(
        None, description="The original user prompt or goal that resulted in this workflow."
    )
    confidence_score: float | None = Field(
        None, ge=0.0, le=1.0, description="A score (0.0 - 1.0) indicating system confidence."
    )
    methodology: str | None = Field(
        None, description="Description of the method or strategy used to generate this."
    )
