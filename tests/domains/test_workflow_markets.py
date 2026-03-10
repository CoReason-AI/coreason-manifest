# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import HypothesisStake, PredictionMarketState


def test_hypothesis_stake_rejects_zero_or_negative_magnitude() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HypothesisStake(
            agent_id="did:web:agent-1", target_hypothesis_id="hyp-1", staked_magnitude=0, implied_probability=0.5
        )
    assert "gt" in str(exc_info.value) or "greater than" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        HypothesisStake(
            agent_id="did:web:agent-1", target_hypothesis_id="hyp-1", staked_magnitude=-10, implied_probability=0.5
        )
    assert "gt" in str(exc_info2.value) or "greater than" in str(exc_info2.value)


def test_hypothesis_stake_valid() -> None:
    stake = HypothesisStake(
        agent_id="did:web:agent-1", target_hypothesis_id="hyp-1", staked_magnitude=100, implied_probability=0.75
    )
    assert stake.staked_magnitude == 100
    assert stake.implied_probability == 0.75


def test_prediction_market_state_rejects_invalid_lmsr_b_parameter() -> None:
    with pytest.raises(ValidationError) as exc_info:
        PredictionMarketState(
            market_id="mkt-1",
            resolution_oracle_condition_id="cond-1",
            lmsr_b_parameter="0",
            order_book=[],
            current_market_probabilities={"hyp-1": "0.5"},
        )
    assert "pattern" in str(exc_info.value) or "string does not match regex" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        PredictionMarketState(
            market_id="mkt-1",
            resolution_oracle_condition_id="cond-1",
            lmsr_b_parameter="-1.5",
            order_book=[],
            current_market_probabilities={"hyp-1": "0.5"},
        )
    assert "pattern" in str(exc_info2.value) or "string does not match regex" in str(exc_info2.value)


def test_prediction_market_state_valid() -> None:
    state = PredictionMarketState(
        market_id="mkt-1",
        resolution_oracle_condition_id="cond-1",
        lmsr_b_parameter="100.0",
        order_book=[],
        current_market_probabilities={"hyp-1": "0.5"},
    )
    assert state.lmsr_b_parameter == "100.0"
