# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Comprehensive validator coverage tests targeting canonical sort, clamping, and integrity validators."""

import base64
import time

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AgentBidIntent,
    AnchoringPolicy,
    AsymptoticComplexityReceipt,
    BudgetExhaustionEvent,
    CognitivePredictionReceipt,
    CognitiveRewardEvaluationReceipt,
    MarketContract,
    SecureSubSessionState,
    VectorEmbeddingState,
)


class TestMarketContract:
    """Exercise _clamp_economic_escrow_invariant."""

    def test_valid_contract(self) -> None:
        obj = MarketContract(minimum_collateral=100, slashing_penalty=50)
        assert obj.slashing_penalty <= obj.minimum_collateral

    def test_penalty_exceeds_collateral_rejected(self) -> None:
        with pytest.raises(ValidationError, match="slashing_penalty"):
            MarketContract(minimum_collateral=50, slashing_penalty=100)

    def test_zero_values(self) -> None:
        obj = MarketContract(minimum_collateral=0, slashing_penalty=0)
        assert obj.minimum_collateral == 0


class TestSecureSubSessionState:
    """Exercise session validation."""

    def test_basic_session(self) -> None:
        obj = SecureSubSessionState(
            session_cid="sess-1",
            allowed_vault_keys=["key1"],
            max_ttl_seconds=3600,
            description="test session",
        )
        assert obj.session_cid == "sess-1"


class TestVectorEmbeddingState:
    """Exercise vector embedding."""

    def test_basic_vector(self) -> None:
        vec_data = base64.b64encode(b"\x00" * 64).decode()
        obj = VectorEmbeddingState(
            vector_base64=vec_data,
            dimensionality=16,
            foundation_matrix_name="test-model",
        )
        assert obj.dimensionality == 16


class TestAnchoringPolicy:
    """Exercise anchoring policy."""

    def test_basic_anchoring(self) -> None:
        obj = AnchoringPolicy(
            anchor_prompt_hash="a" * 64,
            max_semantic_drift=0.1,
        )
        assert obj.max_semantic_drift == 0.1


class TestAsymptoticComplexityReceipt:
    """Exercise complexity receipt."""

    def test_basic_complexity(self) -> None:
        obj = AsymptoticComplexityReceipt(
            capability_cid="cap-1",
            time_complexity_class="O(n log n)",
            space_complexity_class="O(n)",
            peak_vram_bytes=4_000_000_000,
            simulated_cpu_cycles=1_000_000,
        )
        assert obj.time_complexity_class == "O(n log n)"


class TestAgentBidIntent:
    """Exercise agent bid."""

    def test_basic_bid(self) -> None:
        obj = AgentBidIntent(
            agent_cid="did:z:agent1",
            estimated_cost_magnitude=100,
            estimated_latency_ms=50,
            estimated_carbon_gco2eq=0.1,
            confidence_score=0.9,
        )
        assert obj.confidence_score == 0.9


class TestCognitivePredictionReceipt:
    """Exercise prediction receipt."""

    def test_basic_prediction(self) -> None:
        obj = CognitivePredictionReceipt(
            event_cid="cp-1",
            timestamp=time.time(),
            source_chain_cid="chain-1",
            target_source_concept="entity_x",
            predicted_top_k_tokens=["token_a", "token_b"],
        )
        assert len(obj.predicted_top_k_tokens) == 2


class TestCognitiveRewardEvaluationReceipt:
    """Exercise reward evaluation receipt."""

    def test_basic_reward(self) -> None:
        obj = CognitiveRewardEvaluationReceipt(
            event_cid="cr-1",
            timestamp=time.time(),
            source_generation_cid="gen-1",
            calculated_r_path=0.85,
            total_advantage_score=0.7,
        )
        assert obj.calculated_r_path == 0.85


class TestBudgetExhaustionEvent:
    """Exercise budget exhaustion."""

    def test_basic_budget_exhaustion(self) -> None:
        obj = BudgetExhaustionEvent(
            event_cid="be-1",
            timestamp=time.time(),
            exhausted_escrow_cid="escrow-1",
            final_burn_receipt_cid="burn-1",
        )
        assert obj.exhausted_escrow_cid == "escrow-1"
