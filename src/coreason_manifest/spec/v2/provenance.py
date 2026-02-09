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
from enum import StrEnum

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class ProvenanceType(StrEnum):
    """Origin type of the workflow."""

    AI = "ai"
    HUMAN = "human"
    HYBRID = "hybrid"


class ProvenanceData(CoReasonBaseModel):
    """Captures workflow origin and modifications."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: ProvenanceType = Field(..., description="Origin type: ai, human, or hybrid.")
    generated_by: str | None = Field(None, description="The system or model ID that generated this.")
    generated_date: datetime | None = Field(None, description="Date of generation.")
    rationale: str | None = Field(None, description="Reasoning for generation.")
    original_intent: str | None = Field(None, description="The original user prompt or goal.")
    confidence_score: float | None = Field(None, ge=0.0, le=1.0, description="Confidence score.")
    methodology: str | None = Field(None, description="Methodology used.")
    derived_from: str | None = Field(None, description="The ID/URI of the parent recipe this was forked from.")
    modifications: list[str] = Field(default_factory=list, description="Human-readable log of changes.")
