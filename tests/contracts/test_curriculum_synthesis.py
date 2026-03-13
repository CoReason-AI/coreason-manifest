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


def test_cognitive_dual_verification_receipt_identical_verifiers() -> None:
    """
    Prove CognitiveDualVerificationReceipt successfully raises a ValueError
    when initialized with identical verifier IDs.
    """
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Topological Contradiction: Dual verification requires two distinct and independent evaluator nodes."
        ),
    ):
        CognitiveDualVerificationReceipt(
            primary_verifier_id="did:node:verifier1",
            secondary_verifier_id="did:node:verifier1",
            trace_factual_alignment=True,
        )

    # Should succeed with distinct verifiers
    receipt = CognitiveDualVerificationReceipt(
        primary_verifier_id="did:node:verifier1",
        secondary_verifier_id="did:node:verifier2",
        trace_factual_alignment=True,
    )
    assert receipt.primary_verifier_id != receipt.secondary_verifier_id


def test_epistemic_curriculum_manifest_deterministic_sorting() -> None:
    """
    Prove EpistemicCurriculumManifest deterministically sorts its tasks array
    upon instantiation.
    """
    axiom = EpistemicAxiomState(source_concept_id="cid_1", directed_edge_type="leads_to", target_concept_id="cid_2")
    proof = EpistemicTopologicalProofManifest(proof_id="proof_1", axiomatic_chain=[axiom])
    trace = CognitiveReasoningTraceState(
        trace_id="trace_1", source_proof_id="proof_1", token_length=100, trace_payload="payload"
    )
    verification = CognitiveDualVerificationReceipt(
        primary_verifier_id="did:node:verifier1",
        secondary_verifier_id="did:node:verifier2",
        trace_factual_alignment=True,
    )

    task_c = EpistemicGroundedTaskManifest(
        task_id="task_C",
        topological_proof=proof,
        vignette_payload="vignette_c",
        thinking_trace=trace,
        verification_lock=verification,
    )
    task_a = EpistemicGroundedTaskManifest(
        task_id="task_A",
        topological_proof=proof,
        vignette_payload="vignette_a",
        thinking_trace=trace,
        verification_lock=verification,
    )
    task_b = EpistemicGroundedTaskManifest(
        task_id="task_B",
        topological_proof=proof,
        vignette_payload="vignette_b",
        thinking_trace=trace,
        verification_lock=verification,
    )

    curriculum = EpistemicCurriculumManifest(curriculum_id="curr_1", tasks=[task_c, task_a, task_b])

    assert [task.task_id for task in curriculum.tasks] == ["task_A", "task_B", "task_C"]


def test_epistemic_topological_proof_manifest_order_preservation() -> None:
    """
    Prove EpistemicTopologicalProofManifest preserves the sequential order
    of its axiomatic_chain.
    """
    axiom1 = EpistemicAxiomState(source_concept_id="cid_B", directed_edge_type="causes", target_concept_id="cid_C")
    axiom2 = EpistemicAxiomState(source_concept_id="cid_A", directed_edge_type="leads_to", target_concept_id="cid_B")

    # Initialize with out-of-alphanumeric-order elements
    proof = EpistemicTopologicalProofManifest(proof_id="proof_1", axiomatic_chain=[axiom1, axiom2])

    # Sequence should remain exactly as inserted [axiom1, axiom2] and not be sorted
    assert proof.axiomatic_chain == [axiom1, axiom2]
    assert proof.axiomatic_chain[0].source_concept_id == "cid_B"
    assert proof.axiomatic_chain[1].source_concept_id == "cid_A"
