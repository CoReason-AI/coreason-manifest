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
Neuro-Symbolic Data Contracts for Epistemic Logic.

These schemas enforce Ontological Reification, Absolute Provenance,
and Statistical Grounding before any AI data is allowed into the system memory.
"""

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.validation import EpistemicValidator


class ProvenanceSpan(CoreasonModel):
    """
    Absolute Provenance representation.

    An AI reasoning agent cannot trust a fact unless it knows exactly where it came from.
    """

    source_document_hash: str = Field(..., description="Hash of the source document the fact was extracted from.")
    page_number: int = Field(..., description="Page number of the extraction.")
    bounding_box: tuple[float, float, float, float] = Field(
        ...,
        description="Tuple of 4 floats mapping to MinerU coordinates.",
    )
    raw_text_crop: str = Field(..., description="The exact text snippet that justifies this fact.")


class StructuralMilestone(CoreasonModel):
    """
    Intermediate representation for structural milestones.

    Represents MinerU's output (layout blocks, math tokens, hierarchical tables).
    """

    layout_blocks: list[str] = Field(default_factory=list, description="Extracted layout blocks.")
    math_tokens: list[str] = Field(default_factory=list, description="Extracted math formulas/tokens.")
    hierarchical_tables: list[str] = Field(default_factory=list, description="Extracted hierarchical tables.")


class SemanticMilestone(CoreasonModel):
    """
    Intermediate representation for semantic milestones.

    Represents the NLP swarm's output (Discourse roles, entities).
    """

    discourse_roles: list[str] = Field(default_factory=list, description="Discourse roles.")
    entities: list[str] = Field(default_factory=list, description="Entities identified by the NLP swarm.")


class ReifiedEntity(CoreasonModel):
    """
    Ontological Reification mapping.

    Every extracted entity string MUST be mapped to a global ID (e.g., OMOP Concept ID, SNOMED-CT).
    """

    entity_string: str = Field(..., description="The raw string of the extracted entity.")
    global_id: str = Field(..., description="The global ontology identifier (e.g., OMOP Concept ID).")


class ClinicalProposition(CoreasonModel):
    """
    Epistemic Logic Routing: Clinical Proposition.

    Represents a relationship (Subject -> Relation -> Object) with rigorous
    statistical grounding.
    """

    subject: ReifiedEntity = Field(..., description="The subject of the proposition.")
    relation: str = Field(..., description="The relation connecting subject and object.")
    object: ReifiedEntity = Field(..., description="The object of the proposition.")
    p_value: float | None = Field(default=None, description="P-value supporting the relation, if applicable.")
    confidence_interval: str | None = Field(default=None, description="Confidence interval, if applicable.")
    provenance: ProvenanceSpan = Field(..., description="Absolute provenance of this claim.")

    @model_validator(mode="after")
    def validate_statistical_grounding(self) -> "ClinicalProposition":
        """
        Enforce statistical grounding.

        If a claim's relation implies efficacy, the schema must check if a statistical marker
        is present in the payload. If not, it raises a structured ValueError.
        """
        has_p_value = self.p_value is not None
        has_ci = self.confidence_interval is not None

        is_grounded = EpistemicValidator.validate_statistical_grounding(
            relation=self.relation,
            has_p_value=has_p_value,
            has_confidence_interval=has_ci,
        )

        if not is_grounded:
            raise ValueError(
                f"Statistical Grounding Error: The relation '{self.relation}' implies efficacy "
                "but lacks statistical markers (`p_value` or `confidence_interval`). "
                "Epistemic constraints reject this claim."
            )

        return self
