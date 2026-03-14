# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re

import pytest

from coreason_manifest.spec.ontology import (
    CognitiveDualVerificationReceipt,
    CognitiveReasoningTraceState,
    EpistemicAxiomState,
    EpistemicCurriculumManifest,
    EpistemicGroundedTaskManifest,
    EpistemicTopologicalProofManifest,
)


def test_dual_verification_requires_distinct_evaluators() -> None:
    """Prove dual verification receipt raises error for identical verifiers."""

    # Should work fine
    valid_receipt = CognitiveDualVerificationReceipt(
        primary_verifier_id="did:coreason:evaluator-1",
        secondary_verifier_id="did:coreason:evaluator-2",
        trace_factual_alignment=True,
    )

    assert valid_receipt.primary_verifier_id == "did:coreason:evaluator-1"
    assert valid_receipt.secondary_verifier_id == "did:coreason:evaluator-2"

    # Should raise error
    error_msg = "Topological Contradiction: Dual verification requires two distinct and independent evaluator nodes."
    with pytest.raises(
        ValueError,
        match=re.escape(error_msg),
    ):
        CognitiveDualVerificationReceipt(
            primary_verifier_id="did:coreason:same-evaluator",
            secondary_verifier_id="did:coreason:same-evaluator",
            trace_factual_alignment=True,
        )


def test_epistemic_curriculum_manifest_sorts_tasks() -> None:
    """Prove EpistemicCurriculumManifest deterministically sorts its tasks array by task_id upon instantiation."""

    proof = EpistemicTopologicalProofManifest(
        proof_id="cid-proof-1",
        axiomatic_chain=[
            EpistemicAxiomState(source_concept_id="cid-1", directed_edge_type="causes", target_concept_id="cid-2")
        ],
    )

    trace = CognitiveReasoningTraceState(
        trace_id="cid-trace-1", source_proof_id="cid-proof-1", token_length=100, trace_payload="Thinking..."
    )

    lock = CognitiveDualVerificationReceipt(
        primary_verifier_id="did:coreason:evaluator-1",
        secondary_verifier_id="did:coreason:evaluator-2",
        trace_factual_alignment=True,
    )

    task_2 = EpistemicGroundedTaskManifest(
        task_id="task-b",
        topological_proof=proof,
        vignette_payload="Scenario B",
        thinking_trace=trace,
        verification_lock=lock,
    )

    task_1 = EpistemicGroundedTaskManifest(
        task_id="task-a",
        topological_proof=proof,
        vignette_payload="Scenario A",
        thinking_trace=trace,
        verification_lock=lock,
    )

    # Pass in reverse alphabetical order
    manifest = EpistemicCurriculumManifest(curriculum_id="cid-curriculum-1", tasks=[task_2, task_1])

    # Assert they are sorted
    assert manifest.tasks[0].task_id == "task-a"
    assert manifest.tasks[1].task_id == "task-b"


def test_epistemic_topological_proof_manifest_preserves_order() -> None:
    """Prove EpistemicTopologicalProofManifest preserves the sequential order of its axiomatic_chain."""

    axiom_1 = EpistemicAxiomState(source_concept_id="cid-a", directed_edge_type="causes", target_concept_id="cid-b")
    axiom_2 = EpistemicAxiomState(source_concept_id="cid-b", directed_edge_type="causes", target_concept_id="cid-c")
    axiom_3 = EpistemicAxiomState(source_concept_id="cid-c", directed_edge_type="causes", target_concept_id="cid-d")

    # Pass in a specific order (not alphabetical or sorted by any standard)
    axioms = [axiom_2, axiom_1, axiom_3]

    proof = EpistemicTopologicalProofManifest(proof_id="cid-proof-order-test", axiomatic_chain=axioms)

    # Assert they remain in that exact order
    assert proof.axiomatic_chain[0] == axiom_2
    assert proof.axiomatic_chain[1] == axiom_1
    assert proof.axiomatic_chain[2] == axiom_3
