# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Targeted tests for the largest remaining uncovered code blocks."""

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveStateProfile,
    EpistemicAxiomState,
    EpistemicChainGraphState,
    EpistemicSOPManifest,
    MarketContract,
    NDimensionalTensorManifest,
    PredictionMarketState,
    TensorStructuralFormatProfile,
)

# ---------------------------------------------------------------------------
# PredictionMarketState — _clamp_market_probabilities_before (17 lines)
# ---------------------------------------------------------------------------


class TestPredictionMarketState:
    """Exercise LMSR market probability clamping."""

    def test_valid_market(self) -> None:
        obj = PredictionMarketState(
            market_cid="m-1",
            resolution_oracle_condition_cid="oracle-1",
            lmsr_b_parameter="100.0",
            order_book=[],
            current_market_probabilities={"h1": "0.6", "h2": "0.4"},
        )
        assert len(obj.current_market_probabilities) == 2

    def test_unnormalized_probabilities(self) -> None:
        obj = PredictionMarketState(
            market_cid="m-2",
            resolution_oracle_condition_cid="oracle-1",
            lmsr_b_parameter="100.0",
            order_book=[],
            current_market_probabilities={"h1": "0.3", "h2": "0.3"},
        )
        total = sum(float(v) for v in obj.current_market_probabilities.values())
        assert abs(total - 1.0) < 0.01

    def test_zero_probabilities(self) -> None:
        obj = PredictionMarketState(
            market_cid="m-3",
            resolution_oracle_condition_cid="oracle-1",
            lmsr_b_parameter="100.0",
            order_book=[],
            current_market_probabilities={"h1": "0", "h2": "0"},
        )
        total = sum(float(v) for v in obj.current_market_probabilities.values())
        assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# NDimensionalTensorManifest — _enforce_physics_engine (12 lines)
# ---------------------------------------------------------------------------


class TestNDimensionalTensorManifest:
    """Exercise tensor physics validation."""

    def test_valid_tensor(self) -> None:
        # float32 = 4 bytes per element, shape (2,3) = 6 elements = 24 bytes
        obj = NDimensionalTensorManifest(
            structural_format=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 3),
            vram_footprint_bytes=24,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor",
        )
        assert obj.vram_footprint_bytes == 24

    def test_mismatched_vram_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Topological mismatch"):
            NDimensionalTensorManifest(
                structural_format=TensorStructuralFormatProfile.FLOAT32,
                shape=(2, 3),
                vram_footprint_bytes=100,
                merkle_root="a" * 64,
                storage_uri="s3://bucket/tensor",
            )

    def test_zero_dim_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strictly positive"):
            NDimensionalTensorManifest(
                structural_format=TensorStructuralFormatProfile.FLOAT32,
                shape=(0, 3),
                vram_footprint_bytes=0,
                merkle_root="a" * 64,
                storage_uri="s3://bucket/tensor",
            )


# ---------------------------------------------------------------------------
# EpistemicSOPManifest — reject_ghost_nodes (lines 9476-9484)
# ---------------------------------------------------------------------------


class TestEpistemicSOPManifestGhostNodes:
    """Exercise ghost node rejection in SOP."""

    def _make_step(self) -> CognitiveStateProfile:
        return CognitiveStateProfile(urgency_index=0.5, caution_index=0.3, divergence_tolerance=0.2)

    def test_valid_sop(self) -> None:
        obj = EpistemicSOPManifest(
            sop_cid="sop-1",
            target_persona="persona1",
            cognitive_steps={
                "step1": self._make_step(),
                "step2": self._make_step(),
            },
            structural_grammar_hashes={"step1": "hash1"},
            chronological_flow_edges=[("step1", "step2")],
            prm_evaluations=[],
        )
        assert len(obj.cognitive_steps) == 2

    def test_ghost_source_in_edges(self) -> None:
        with pytest.raises(ValidationError, match="Ghost node"):
            EpistemicSOPManifest(
                sop_cid="sop-2",
                target_persona="persona1",
                cognitive_steps={"step1": self._make_step()},
                structural_grammar_hashes={},
                chronological_flow_edges=[("missing", "step1")],
                prm_evaluations=[],
            )

    def test_ghost_target_in_edges(self) -> None:
        with pytest.raises(ValidationError, match="Ghost node"):
            EpistemicSOPManifest(
                sop_cid="sop-3",
                target_persona="persona1",
                cognitive_steps={"step1": self._make_step()},
                structural_grammar_hashes={},
                chronological_flow_edges=[("step1", "missing")],
                prm_evaluations=[],
            )

    def test_ghost_grammar_hash(self) -> None:
        with pytest.raises(ValidationError, match="Ghost node"):
            EpistemicSOPManifest(
                sop_cid="sop-4",
                target_persona="persona1",
                cognitive_steps={"step1": self._make_step()},
                structural_grammar_hashes={"missing_step": "hash1"},
                chronological_flow_edges=[],
                prm_evaluations=[],
            )


# ---------------------------------------------------------------------------
# EpistemicChainGraphState — canonical sort (lines 13415-13425)
# ---------------------------------------------------------------------------


class TestEpistemicChainGraphState:
    """Exercise chain graph canonical sort."""

    def test_valid_chain_sorted(self) -> None:
        obj = EpistemicChainGraphState(
            chain_cid="chain-1",
            syntactic_roots=["root_b", "root_a"],
            semantic_leaves=[
                EpistemicAxiomState(
                    source_concept_cid="z_src",
                    directed_edge_class="is_a",
                    target_concept_cid="tgt1",
                ),
                EpistemicAxiomState(
                    source_concept_cid="a_src",
                    directed_edge_class="is_a",
                    target_concept_cid="tgt1",
                ),
            ],
        )
        # Verify canonical sort on syntactic_roots
        assert obj.syntactic_roots == ["root_a", "root_b"]
        # Verify canonical sort on semantic_leaves by source_concept_cid
        assert obj.semantic_leaves[0].source_concept_cid == "a_src"


# ---------------------------------------------------------------------------
# MarketContract — edge cases for _clamp_economic_escrow
# ---------------------------------------------------------------------------


class TestMarketContractRobust:
    """Exercise edge cases in escrow clamping."""

    def test_negative_collateral_clamped(self) -> None:
        obj = MarketContract(minimum_collateral=-10, slashing_penalty=0)
        assert obj.minimum_collateral >= 0

    def test_very_large_collateral(self) -> None:
        obj = MarketContract(minimum_collateral=18446744073709551615, slashing_penalty=0)
        assert obj.minimum_collateral == 18446744073709551615
