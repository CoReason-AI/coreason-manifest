import pytest

from coreason_manifest.core.domains.epistemic import (
    ClinicalProposition,
    ProvenanceSpan,
    ReifiedEntity,
    SemanticMilestone,
    StructuralMilestone,
)


def test_valid_clinical_proposition_with_p_value() -> None:
    """Test that a valid ClinicalProposition with statistical grounding passes validation."""
    provenance = ProvenanceSpan(
        source_document_hash="abc123hash",
        page_number=42,
        bounding_box=(10.0, 20.0, 30.0, 40.0),
        raw_text_crop="Drug X cures Disease Y.",
    )

    subject = ReifiedEntity(entity_string="Drug X", global_id="OMOP:12345")
    obj = ReifiedEntity(entity_string="Disease Y", global_id="SNOMED:67890")

    proposition = ClinicalProposition(
        subject=subject,
        relation="cures",
        object=obj,
        p_value=0.04,
        provenance=provenance,
    )

    assert proposition.relation == "cures"
    assert proposition.p_value == 0.04


def test_invalid_clinical_proposition_missing_grounding() -> None:
    """Test that a ClinicalProposition implying efficacy without statistical markers fails validation."""
    provenance = ProvenanceSpan(
        source_document_hash="abc123hash",
        page_number=42,
        bounding_box=(10.0, 20.0, 30.0, 40.0),
        raw_text_crop="Drug X treats Disease Y.",
    )

    subject = ReifiedEntity(entity_string="Drug X", global_id="OMOP:12345")
    obj = ReifiedEntity(entity_string="Disease Y", global_id="SNOMED:67890")

    with pytest.raises(ValueError, match="Statistical Grounding Error"):
        ClinicalProposition(
            subject=subject,
            relation="treats",
            object=obj,
            provenance=provenance,
        )


def test_valid_clinical_proposition_non_efficacy() -> None:
    """Test that non-efficacy relations do not strictly require statistical grounding."""
    provenance = ProvenanceSpan(
        source_document_hash="abc123hash",
        page_number=42,
        bounding_box=(10.0, 20.0, 30.0, 40.0),
        raw_text_crop="Drug X interacts with Drug Z.",
    )

    subject = ReifiedEntity(entity_string="Drug X", global_id="OMOP:12345")
    obj = ReifiedEntity(entity_string="Drug Z", global_id="OMOP:54321")

    proposition = ClinicalProposition(
        subject=subject,
        relation="interacts with",
        object=obj,
        provenance=provenance,
    )

    assert proposition.relation == "interacts with"
    assert proposition.p_value is None


def test_structural_and_semantic_milestones() -> None:
    """Test instantiation of StructuralMilestone and SemanticMilestone."""
    structural = StructuralMilestone(
        layout_blocks=["block1"],
        math_tokens=["E=mc^2"],
        hierarchical_tables=["table1"],
    )
    assert "E=mc^2" in structural.math_tokens

    semantic = SemanticMilestone(
        discourse_roles=["conclusion"],
        entities=["Disease Y"],
    )
    assert "conclusion" in semantic.discourse_roles
