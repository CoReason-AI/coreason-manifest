# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EpistemicAxiomState,
    EpistemicAxiomVerificationReceipt,
    EpistemicChainGraphState,
    EpistemicSeedInjectionPolicy,
)


def test_epistemic_chain_graph_state_sorting() -> None:
    axiom1 = EpistemicAxiomState(source_concept_id="B", directed_edge_type="has_part", target_concept_id="A")
    axiom2 = EpistemicAxiomState(source_concept_id="A", directed_edge_type="part_of", target_concept_id="C")
    axiom3 = EpistemicAxiomState(source_concept_id="A", directed_edge_type="has_part", target_concept_id="C")

    # Pass in a non-sorted list of axioms for semantic_leaves
    state = EpistemicChainGraphState(
        chain_id="chain-123",
        syntactic_roots=["root2", "root1", "root3"],
        semantic_leaves=[axiom1, axiom2, axiom3],
    )

    # Prove semantic_leaves is deterministically sorted by source, edge, then target
    assert state.semantic_leaves == [axiom3, axiom2, axiom1]

    # Prove syntactic_roots preserves order
    assert state.syntactic_roots == ["root2", "root1", "root3"]


def test_epistemic_axiom_verification_receipt_quarantine() -> None:
    # Successful instantiation
    receipt = EpistemicAxiomVerificationReceipt(
        event_id="evt-123",
        timestamp=1600000000.0,
        source_prediction_id="pred-123",
        sequence_similarity_score=0.9,
        fact_score_passed=True,
    )
    assert receipt.fact_score_passed is True

    # Failing instantiation raises ValueError (wrapped in ValidationError by Pydantic)
    with pytest.raises(ValidationError) as excinfo:
        EpistemicAxiomVerificationReceipt(
            event_id="evt-124",
            timestamp=1600000001.0,
            source_prediction_id="pred-124",
            sequence_similarity_score=0.9,
            fact_score_passed=False,
        )

    # Check that the specific ValueError message is part of the ValidationError
    assert "Epistemic Contagion Prevented: Axioms failing validation cannot be verified." in str(excinfo.value)


def test_epistemic_seed_injection_policy_alpha_bounds() -> None:
    # Valid alpha
    policy = EpistemicSeedInjectionPolicy(
        similarity_threshold_alpha=0.5,
        relation_diversity_bucket_size=10,
    )
    assert policy.similarity_threshold_alpha == 0.5

    # Alpha too low
    with pytest.raises(ValidationError):
        EpistemicSeedInjectionPolicy(
            similarity_threshold_alpha=-0.1,
            relation_diversity_bucket_size=10,
        )

    # Alpha too high
    with pytest.raises(ValidationError):
        EpistemicSeedInjectionPolicy(
            similarity_threshold_alpha=1.1,
            relation_diversity_bucket_size=10,
        )

    # Diversity bucket size too low
    with pytest.raises(ValidationError):
        EpistemicSeedInjectionPolicy(
            similarity_threshold_alpha=0.5,
            relation_diversity_bucket_size=0,
        )
