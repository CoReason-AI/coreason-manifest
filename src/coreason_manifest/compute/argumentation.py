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
Schemas for formal multi-agent Defeasible Logic representation.

These models allow storing multi-agent debates over phenotype definitions
as rigorous mathematical state graphs (Argumentation DAGs) and capture the
complex interaction between proposals and their critiques.
"""

from typing import Literal

from pydantic import Field, model_validator

from coreason_manifest.compute.uncertainty import SyntaxTreeCitationAnchor
from coreason_manifest.core.common.base import CoreasonModel


class DefeasibleClaim(CoreasonModel):
    """
    Represents a single node in a multi-agent debate regarding a clinical rule.

    Captures individual proposals, rebuttals, or undercutting arguments
    and grounds them in empirical evidence mapping.
    """

    claim_id: str = Field(..., description="Unique UUID string identifying this particular claim node.")
    agent_id: str = Field(..., description="Identifier for the AI or Human submitting the claim.")
    claim_type: Literal["PROPOSAL", "REBUTTAL", "UNDERCUT"] = Field(
        ..., description="The type of the claim in relation to the debate graph."
    )
    target_claim_id: str | None = Field(
        default=None,
        description="UUID string pointing to a parent claim, required if this claim is a Rebuttal or Undercut.",
    )
    semantic_reasoning: str = Field(..., description="The clinical argument explaining the logic of the claim.")
    citation_anchors: list[SyntaxTreeCitationAnchor] = Field(
        ..., description="List of source-level anchors proving provenance for this claim."
    )

    @model_validator(mode="after")
    def validate_target_claim(self) -> "DefeasibleClaim":
        """Enforce that Rebuttals and Undercuts must point to a target claim."""
        if self.claim_type in {"REBUTTAL", "UNDERCUT"} and not self.target_claim_id:
            raise ValueError(f"Validation Error: A claim of type '{self.claim_type}' MUST have a target_claim_id.")
        return self


class ArgumentationDAG(CoreasonModel):
    """
    Represents the holistic state of a clinical disagreement.

    A Directed Acyclic Graph connecting DefeasibleClaims mapped to an overarching
    phenotype resolution path.
    """

    graph_id: str = Field(..., description="Unique UUID string identifying the full DAG state.")
    target_phenotype_id: str = Field(..., description="Target overarching phenotype this graph seeks to define.")
    claims: dict[str, DefeasibleClaim] = Field(
        ..., description="Map of `claim_id` strings to nodes, forming the debate network."
    )
    resolution_status: Literal["UNRESOLVED", "CONSENSUS_REACHED", "OVERRIDDEN_BY_HUMAN"] = Field(
        ..., description="The final consensus state of this multi-agent argumentation process."
    )
