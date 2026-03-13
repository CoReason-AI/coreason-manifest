import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EpistemicAxiomState,
    EpistemicAxiomVerificationReceipt,
    EpistemicChainGraphState,
    EpistemicSeedInjectionPolicy,
)


def test_epistemic_chain_graph_state_determinism() -> None:
    """
    Prove EpistemicChainGraphState sorts its semantic_leaves deterministically
    upon instantiation but preserves the order of syntactic_roots.
    """
    axiom1 = EpistemicAxiomState(source_concept_id="cid_A", directed_edge_type="causes", target_concept_id="cid_B")
    axiom2 = EpistemicAxiomState(source_concept_id="cid_B", directed_edge_type="leads_to", target_concept_id="cid_C")
    axiom3 = EpistemicAxiomState(source_concept_id="cid_A", directed_edge_type="inhibits", target_concept_id="cid_C")

    # Initialize with unsorted semantic leaves and specifically ordered syntactic roots
    graph = EpistemicChainGraphState(
        chain_id="chain_1",
        syntactic_roots=["root_Z", "root_A", "root_M"],
        semantic_leaves=[axiom2, axiom3, axiom1],
    )

    # syntactic_roots should NOT be sorted
    assert graph.syntactic_roots == ["root_Z", "root_A", "root_M"]

    # semantic_leaves SHOULD be sorted deterministically
    # Sort order: source_concept_id, then directed_edge_type, then target_concept_id
    # axiom1: cid_A, causes, cid_B
    # axiom3: cid_A, inhibits, cid_C
    # axiom2: cid_B, leads_to, cid_C
    assert graph.semantic_leaves == [axiom1, axiom3, axiom2]


def test_epistemic_axiom_verification_receipt_fact_score() -> None:
    """
    Prove EpistemicAxiomVerificationReceipt successfully raises a ValueError
    when fact_score_passed=False.
    """
    import re

    with pytest.raises(
        ValueError, match=re.escape("Epistemic Contagion Prevented: Axioms failing validation cannot be verified.")
    ):
        EpistemicAxiomVerificationReceipt(
            verification_id="verif_1",
            source_prediction_id="pred_1",
            sequence_similarity_score=0.9,
            fact_score_passed=False,
        )

    # Should pass when fact_score_passed is True
    receipt = EpistemicAxiomVerificationReceipt(
        verification_id="verif_2",
        source_prediction_id="pred_2",
        sequence_similarity_score=0.9,
        fact_score_passed=True,
    )
    assert receipt.fact_score_passed is True


def test_epistemic_seed_injection_policy_alpha_bounds() -> None:
    """
    Prove EpistemicSeedInjectionPolicy rejects alpha values > 1.0 or < 0.0.
    """
    # Should reject alpha < 0.0
    with pytest.raises(ValidationError) as exc_info:
        EpistemicSeedInjectionPolicy(
            similarity_threshold_alpha=-0.1,
            relation_diversity_bucket_size=5,
        )
    assert "Input should be greater than or equal to 0" in str(exc_info.value)

    # Should reject alpha > 1.0
    with pytest.raises(ValidationError) as exc_info2:
        EpistemicSeedInjectionPolicy(
            similarity_threshold_alpha=1.1,
            relation_diversity_bucket_size=5,
        )
    assert "Input should be less than or equal to 1" in str(exc_info2.value)

    # Should accept alpha between 0.0 and 1.0
    policy = EpistemicSeedInjectionPolicy(
        similarity_threshold_alpha=0.5,
        relation_diversity_bucket_size=5,
    )
    assert policy.similarity_threshold_alpha == 0.5
