# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.ontology import (
    CognitiveFormatContract,
    CognitiveRewardEvaluationReceipt,
    ConstrainedDecodingPolicy,
    EpistemicAxiomState,
    EpistemicRewardModelPolicy,
)


def test_cognitive_reward_evaluation_receipt_sorting() -> None:
    # Prove CognitiveRewardEvaluationReceipt mathematically sorts the extracted_axioms list
    # regardless of the order they are passed in during instantiation.
    axiom1 = EpistemicAxiomState(source_concept_id="B", directed_edge_type="has_part", target_concept_id="A")
    axiom2 = EpistemicAxiomState(source_concept_id="A", directed_edge_type="has_part", target_concept_id="C")
    axiom3 = EpistemicAxiomState(source_concept_id="A", directed_edge_type="part_of", target_concept_id="B")

    receipt = CognitiveRewardEvaluationReceipt(
        event_id="test_event_id",
        timestamp=100.0,
        source_generation_id="gen_id",
        calculated_r_path=0.5,
        total_advantage_score=1.2,
        extracted_axioms=[axiom1, axiom2, axiom3],
    )

    assert receipt.extracted_axioms == [axiom2, axiom3, axiom1]


def test_cognitive_reward_evaluation_receipt_inherits_base_state_event() -> None:
    # Prove CognitiveRewardEvaluationReceipt correctly inherits from BaseStateEvent
    # by successfully instantiating it with a timestamp and event_id.
    receipt = CognitiveRewardEvaluationReceipt(
        event_id="test_event_id",
        timestamp=100.0,
        source_generation_id="gen_id",
        calculated_r_path=0.5,
        total_advantage_score=1.2,
    )

    assert receipt.event_id == "test_event_id"
    assert receipt.timestamp == 100.0
    assert receipt.type == "cognitive_reward_evaluation"


def test_epistemic_reward_model_policy_initialization() -> None:
    # Prove EpistemicRewardModelPolicy initializes successfully and properly nests the CognitiveFormatContract.
    decoding_policy = ConstrainedDecodingPolicy(
        enforcement_strategy="fsm_logit_mask", compiler_backend="outlines", terminate_on_eos_leak=True
    )
    format_contract = CognitiveFormatContract(
        require_think_tags=True, final_answer_regex="^Final Answer: .*$", decoding_policy=decoding_policy
    )

    policy = EpistemicRewardModelPolicy(
        policy_id="test_policy", reference_graph_id="ref_graph", format_contract=format_contract, beta_path_weight=0.5
    )

    assert policy.policy_id == "test_policy"
    assert policy.reference_graph_id == "ref_graph"
    assert policy.format_contract.require_think_tags is True
    assert policy.format_contract.final_answer_regex == "^Final Answer: .*$"
    assert policy.beta_path_weight == 0.5
