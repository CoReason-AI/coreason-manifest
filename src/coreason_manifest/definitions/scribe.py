# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import List

from pydantic import Field

from .base import CoReasonBaseModel


class TraceabilityMatrix(CoReasonBaseModel):
    """Links Requirements to Test Results."""

    req_id: str
    test_ids: List[str]
    coverage_status: str  # COVERED, GAP


class DocumentationManifest(CoReasonBaseModel):
    """The master index for the Audit Package."""

    agent_version: str
    bom_hash: str
    matrix: List[TraceabilityMatrix]


class ReviewPacket(CoReasonBaseModel):
    """
    Data object sent to UI for human sign-off.
    Contains the 'Before vs After' for semantic comparison.
    """

    packet_id: str
    agent_name: str
    original_content: str
    generated_content: str
    diff_summary: str  # Natural language summary of changes
    risk_score: float = Field(..., ge=0.0, le=1.0)
