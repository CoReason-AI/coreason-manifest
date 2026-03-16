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
    CognitiveFormatContract,
    ConstrainedDecodingPolicy,
    EpistemicFlowStateReceipt,
    EpistemicRewardModelPolicy,
    TopologicalRewardContract,
)


def test_topological_reward_contract_bounds() -> None:
    # Test valid bounds
    contract = TopologicalRewardContract(
        min_link_criticality_score=0.5, min_semantic_relevance_score=0.5, aggregation_method="attention_gat"
    )
    assert contract.min_link_criticality_score == 0.5
    assert contract.min_semantic_relevance_score == 0.5

    # Test invalid upper bounds
    with pytest.raises(ValidationError):
        TopologicalRewardContract(
            min_link_criticality_score=1.1, min_semantic_relevance_score=0.5, aggregation_method="attention_gat"
        )

    with pytest.raises(ValidationError):
        TopologicalRewardContract(
            min_link_criticality_score=0.5, min_semantic_relevance_score=1.1, aggregation_method="attention_gat"
        )

    # Test invalid lower bounds
    with pytest.raises(ValidationError):
        TopologicalRewardContract(
            min_link_criticality_score=-0.1, min_semantic_relevance_score=0.5, aggregation_method="attention_gat"
        )

    with pytest.raises(ValidationError):
        TopologicalRewardContract(
            min_link_criticality_score=0.5, min_semantic_relevance_score=-0.1, aggregation_method="attention_gat"
        )


def test_epistemic_flow_state_receipt() -> None:
    receipt = EpistemicFlowStateReceipt(
        event_id="test_event_id",
        timestamp=1234567890.0,
        source_trajectory_id="traj_123",
        estimated_flow_value=1.5,
        terminal_reward_factorized=True,
    )
    # Check inheritance of event_id and timestamp
    assert receipt.event_id == "test_event_id"
    assert receipt.timestamp == 1234567890.0
    assert receipt.type == "epistemic_flow_state"


def test_epistemic_reward_model_policy() -> None:
    decoding_policy = ConstrainedDecodingPolicy(
        enforcement_strategy="fsm_logit_mask", compiler_backend="outlines", terminate_on_eos_leak=True
    )
    format_contract = CognitiveFormatContract(
        require_think_tags=True, final_answer_regex="^Final Answer: .*$", decoding_policy=decoding_policy
    )
    topological_contract = TopologicalRewardContract(
        min_link_criticality_score=0.8, min_semantic_relevance_score=0.9, aggregation_method="rwr_topological"
    )

    policy = EpistemicRewardModelPolicy(
        policy_id="policy_1",
        reference_graph_id="graph_1",
        format_contract=format_contract,
        beta_path_weight=0.5,
        topological_scoring=topological_contract,
    )

    assert policy.topological_scoring is not None
    assert policy.topological_scoring.min_link_criticality_score == 0.8
    assert policy.topological_scoring.aggregation_method == "rwr_topological"
