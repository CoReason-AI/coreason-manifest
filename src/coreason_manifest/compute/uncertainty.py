# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""
Schemas for state-of-the-art Epistemic Uncertainty tracking.

These models define rigorous structural representations for evidence-based
confidence, source attribution, and counterfactual decision justification
to support high-stakes clinical AI processing.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


class SyntaxTreeCitationAnchor(CoreasonModel):
    """
    Represents a W3C PROV-O aligned citation bound to a specific abstract syntax tree node.

    Provides strict provenance mapping back to literature sources.
    """

    pmcid: str | None = Field(default=None, description="The PubMed Central ID of the source document.")
    source_text_tokens: list[str] = Field(..., description="The exact quoted text tokens from the source.")
    retrieval_timestamp: datetime = Field(..., description="The datetime the source text was retrieved.")
    guideline_version: str = Field(..., description="The version of the guideline this citation belongs to.")


class EpistemicWeight(CoreasonModel):
    """
    Represents a Conformal Prediction structured confidence vector.

    Captures varying sources of doubt in AI reasoning, including random noise
    (aleatoric) and lack of knowledge (epistemic).
    """

    aleatoric_doubt: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data noise doubt level, represented as a float between 0.0 and 1.0.",
    )
    epistemic_doubt: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Lack of knowledge or consensus doubt level, represented as a float between 0.0 and 1.0.",
    )
    evidence_category: Literal[
        "DIRECT_LEXICAL_MATCH", "SEMANTIC_INFERENCE", "GUIDELINE_EXTRAPOLATION", "EXPERT_CONSENSUS"
    ] = Field(..., description="The category of clinical evidence supporting this weight.")


class CounterfactualJustification(CoreasonModel):
    """
    Represents the mandatory tracking of rejected alternatives.

    Essential for AI alignment in healthcare, providing transparency into
    why a particular path or conclusion was chosen over others.
    """

    accepted_logic_node_id: str = Field(..., description="The identifier of the accepted logic node.")
    rejected_alternatives: list[str] = Field(
        ..., description="List of OMOP Concept IDs or logic rules that were considered but discarded."
    )
    rejection_reason: str = Field(..., description="Explanation of the epistemic deficit of the alternatives.")
    epistemic_weight: EpistemicWeight = Field(
        ..., description="The EpistemicWeight object justifying the final decision."
    )
