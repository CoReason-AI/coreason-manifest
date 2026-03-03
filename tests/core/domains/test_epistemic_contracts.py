import pytest

from coreason_manifest.core.domains.epistemic import (
    ClinicalProposition,
    MathToken,
    ProvenanceSpan,
    ReifiedEntity,
    SemanticMilestone,
    StructuralMilestone,
    TabularSerialization,
)


def test_reified_entity_rejects_invalid_ontology() -> None:
    """Test that ReifiedEntity rejects an invalid global_id."""
    with pytest.raises(ValueError, match="Ontology Error"):
        ReifiedEntity(entity_string="Fake Entity", global_id="FAKE:999")


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
        intent_label="proven_efficacy",
        p_value=0.04,
        provenance=provenance,
    )

    assert proposition.relation == "cures"
    assert proposition.p_value == 0.04
    assert proposition.intent_label == "proven_efficacy"


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
            intent_label="proven_efficacy",
            provenance=provenance,
        )


def test_invalid_clinical_proposition_p_value_threshold() -> None:
    """Test that a ClinicalProposition rejects a p_value > 0.05 when intent_label='proven_efficacy'."""
    provenance = ProvenanceSpan(
        source_document_hash="abc123hash",
        page_number=42,
        bounding_box=(10.0, 20.0, 30.0, 40.0),
        raw_text_crop="Drug X treats Disease Y but not significantly.",
    )

    subject = ReifiedEntity(entity_string="Drug X", global_id="OMOP:12345")
    obj = ReifiedEntity(entity_string="Disease Y", global_id="SNOMED:67890")

    with pytest.raises(ValueError, match="Epistemic Failure: Claim is not statistically significant"):
        ClinicalProposition(
            subject=subject,
            relation="treats",
            object=obj,
            intent_label="proven_efficacy",
            p_value=0.15,
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
    obj = ReifiedEntity(entity_string="Drug Z", global_id="RXNORM:1191")

    proposition = ClinicalProposition(
        subject=subject,
        relation="interacts with",
        object=obj,
        intent_label="observation",
        p_value=0.15,  # Ignored because it's an observation
        provenance=provenance,
    )

    assert proposition.relation == "interacts with"
    assert proposition.p_value == 0.15
    assert proposition.intent_label == "observation"


def test_structural_and_semantic_milestones() -> None:
    """Test instantiation of StructuralMilestone and SemanticMilestone."""
    math_token = MathToken(latex_content="E=mc^2", is_block=True)
    table_serialization = TabularSerialization(html_grid="<table></table>", omop_mapped=True)

    structural = StructuralMilestone(
        layout_blocks=["block1"],
        math_tokens=[math_token],
        hierarchical_tables=[table_serialization],
    )
    assert structural.math_tokens[0].latex_content == "E=mc^2"
    assert structural.hierarchical_tables[0].html_grid == "<table></table>"

    semantic = SemanticMilestone(
        discourse_roles=["conclusion"],
        entities=["Disease Y"],
    )
    assert "conclusion" in semantic.discourse_roles
