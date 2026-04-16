# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for PredictionMarketPolicy, QuorumPolicy, ConsensusPolicy, and market economics."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ConsensusPolicy,
    PredictionMarketPolicy,
    QuorumPolicy,
)

# ---------------------------------------------------------------------------
# QuorumPolicy — BFT math
# ---------------------------------------------------------------------------


class TestQuorumPolicy:
    """Exercise enforce_bft_math: N >= 3f + 1."""

    def test_valid_bft(self) -> None:
        qp = QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=4,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )
        assert qp.min_quorum_size >= 3 * qp.max_tolerable_faults + 1

    def test_bft_violation(self) -> None:
        with pytest.raises(ValidationError, match="Byzantine Fault Tolerance"):
            QuorumPolicy(
                max_tolerable_faults=2,
                min_quorum_size=5,  # Needs >= 7
                state_validation_metric="zk_proof",
                byzantine_action="ignore",
            )

    def test_zero_faults_needs_one_quorum(self) -> None:
        qp = QuorumPolicy(
            max_tolerable_faults=0,
            min_quorum_size=1,
            state_validation_metric="semantic_embedding",
            byzantine_action="slash_escrow",
        )
        assert qp.min_quorum_size == 1

    @given(
        f=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=20, deadline=None)
    def test_satisfying_bft_invariant(self, f: int) -> None:
        n = 3 * f + 1
        qp = QuorumPolicy(
            max_tolerable_faults=f,
            min_quorum_size=n,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )
        assert qp.min_quorum_size >= 3 * qp.max_tolerable_faults + 1

    @given(f=st.integers(min_value=1, max_value=50))
    @settings(max_examples=15, deadline=None)
    def test_violating_bft_invariant(self, f: int) -> None:
        n = 3 * f  # Always < 3f + 1
        with pytest.raises(ValidationError, match="Byzantine Fault Tolerance"):
            QuorumPolicy(
                max_tolerable_faults=f,
                min_quorum_size=n,
                state_validation_metric="ledger_hash",
                byzantine_action="quarantine",
            )


# ---------------------------------------------------------------------------
# ConsensusPolicy
# ---------------------------------------------------------------------------


class TestConsensusPolicy:
    """Exercise validate_pbft_requirements."""

    def test_majority_no_quorum_valid(self) -> None:
        cp = ConsensusPolicy(strategy="majority")
        assert cp.quorum_rules is None

    def test_pbft_without_quorum_rejected(self) -> None:
        with pytest.raises(ValidationError, match="quorum_rules must be provided"):
            ConsensusPolicy(strategy="pbft")

    def test_pbft_with_quorum_valid(self) -> None:
        qr = QuorumPolicy(
            max_tolerable_faults=0,
            min_quorum_size=1,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )
        cp = ConsensusPolicy(strategy="pbft", quorum_rules=qr)
        assert cp.quorum_rules is not None

    def test_prediction_market_with_rules(self) -> None:
        pmr = PredictionMarketPolicy(
            staking_function="quadratic",
            min_liquidity_magnitude=100,
            convergence_delta_threshold=0.05,
        )
        cp = ConsensusPolicy(strategy="prediction_market", prediction_market_rules=pmr)
        assert cp.prediction_market_rules is not None

    @given(
        strategy=st.sampled_from(["unanimous", "majority", "debate_rounds", "prediction_market"]),
    )
    @settings(max_examples=10, deadline=None)
    def test_non_pbft_strategies_no_quorum_ok(self, strategy: str) -> None:
        cp = ConsensusPolicy(strategy=strategy)  # type: ignore[arg-type]
        assert cp.strategy == strategy


# ---------------------------------------------------------------------------
# PredictionMarketPolicy
# ---------------------------------------------------------------------------


class TestPredictionMarketPolicy:
    """Exercise boundary values."""

    @given(
        stake=st.sampled_from(["linear", "quadratic"]),
        liq=st.integers(min_value=0, max_value=1000),
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=15, deadline=None)
    def test_valid_market_policy(self, stake: str, liq: int, threshold: float) -> None:
        pm = PredictionMarketPolicy(
            staking_function=stake,  # type: ignore[arg-type]
            min_liquidity_magnitude=liq,
            convergence_delta_threshold=threshold,
        )
        assert pm.min_liquidity_magnitude >= 0
        assert 0.0 <= pm.convergence_delta_threshold <= 1.0
