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
    """Metadata tracking the creation or modification of the manifest.

    Supports both AI-generated (provenance) and human-authored workflows.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, frozen=True)

    # Core identification
    type: Literal["ai", "human", "hybrid"] = Field(..., description="The primary source of this manifest.")
    generated_by: str = Field(..., description="The system ID (AI) or user identifier (Human).")
    generated_date: datetime | None = Field(None, description="Timestamp of generation.")

    # Rationale & Intent (Generalized)
    rationale: str | None = Field(None, description="Reasoning behind the design choices.")
    original_intent: str | None = Field(None, description="The initial prompt (AI) or design goal (Human).")

    # AI Specifics
    confidence_score: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence score (0.0-1.0) for AI-generated content."
    )

    # Methodology (e.g., 'Chain-of-Thought', 'Manual Review', 'Peer Review')
    methodology: str | None = Field(None, description="The specific technique or process used.")
