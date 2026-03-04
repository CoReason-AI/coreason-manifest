from datetime import UTC, datetime

import pytest

from coreason_manifest.compute.uncertainty import CounterfactualJustification, EpistemicWeight, SyntaxTreeCitationAnchor


def test_syntax_tree_citation_anchor() -> None:
    anchor = SyntaxTreeCitationAnchor(
        pmcid="PMC12345",
        source_text_tokens=["patient", "has", "hypertension"],
        retrieval_timestamp=datetime.now(UTC),
        guideline_version="1.0",
    )
    assert anchor.pmcid == "PMC12345"
    assert len(anchor.source_text_tokens) == 3


def test_epistemic_weight() -> None:
    weight = EpistemicWeight(aleatoric_doubt=0.1, epistemic_doubt=0.2, evidence_category="DIRECT_LEXICAL_MATCH")
    assert weight.aleatoric_doubt == 0.1
    assert weight.epistemic_doubt == 0.2

    with pytest.raises(ValueError, match="1 validation error for"):
        EpistemicWeight(aleatoric_doubt=1.5, epistemic_doubt=0.2, evidence_category="DIRECT_LEXICAL_MATCH")

    with pytest.raises(ValueError, match="1 validation error for"):
        EpistemicWeight(
            aleatoric_doubt=0.1,
            epistemic_doubt=0.2,
            evidence_category="INVALID_CATEGORY",  # type: ignore
        )


def test_counterfactual_justification() -> None:
    weight = EpistemicWeight(aleatoric_doubt=0.1, epistemic_doubt=0.2, evidence_category="EXPERT_CONSENSUS")
    justification = CounterfactualJustification(
        accepted_logic_node_id="node_1",
        rejected_alternatives=["node_2", "node_3"],
        rejection_reason="Lack of clinical evidence.",
        epistemic_weight=weight,
    )
    assert justification.accepted_logic_node_id == "node_1"
    assert justification.epistemic_weight.evidence_category == "EXPERT_CONSENSUS"
