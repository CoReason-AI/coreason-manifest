# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import LatentScratchpadReceipt, ThoughtBranchState


# 1. Fuzzing Array Sorting Determinism
@st.composite
def valid_scratchpad_strategy(draw: st.DrawFn) -> dict[str, Any]:
    """Generates mathematically guaranteed valid branch matrices to test sorting determinism."""
    # Generate chaotic, unsorted branch IDs
    branch_ids = draw(
        st.lists(st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True), min_size=2, max_size=15, unique=True)
    )

    explored = [
        ThoughtBranchState(branch_cid=b_cid, latent_content_hash="a" * 64, prm_score=0.9) for b_cid in branch_ids
    ]

    discarded = draw(st.lists(st.sampled_from(branch_ids), max_size=len(branch_ids), unique=True))
    resolution_cid = draw(st.one_of(st.none(), st.sampled_from(branch_ids)))

    return {"explored_branches": explored, "discarded_branches": discarded, "resolution_branch_cid": resolution_cid}


@given(data=valid_scratchpad_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_latent_scratchpad_receipt_fuzz_sorting_determinism(data: dict[str, Any]) -> None:
    """
    AGENT INSTRUCTION: Prove that explored and discarded branches are mathematically
    sorted regardless of input order, guaranteeing canonical hashing determinism.
    """
    receipt = LatentScratchpadReceipt(
        trace_cid="trace_fuzz_1",
        explored_branches=data["explored_branches"],
        discarded_branches=data["discarded_branches"],
        resolution_branch_cid=data["resolution_branch_cid"],
        total_latent_tokens=100,
    )

    # Assert deterministic sorting
    actual_cids = [
        b.branch_cid if hasattr(b, "branch_cid") else getattr(b, "topology_cid", "") for b in receipt.explored_branches
    ]
    expected_cids = sorted([b.branch_cid for b in data["explored_branches"]])
    assert actual_cids == expected_cids

    assert receipt.discarded_branches == sorted(data["discarded_branches"])


# 2. Atomic Error Tests for Referential Integrity
def test_latent_scratchpad_receipt_resolution_branch_missing() -> None:
    """Prove that the orchestrator rejects resolution branches not found in the explored matrix."""
    branch_1 = ThoughtBranchState(branch_cid="branch_1", latent_content_hash="a" * 64, prm_score=0.9)

    with pytest.raises(ValidationError, match="resolution_branch_cid 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_cid="trace_123",
            explored_branches=[branch_1],
            discarded_branches=[],
            resolution_branch_cid="branch_invalid",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_discarded_branch_missing() -> None:
    """Prove that the orchestrator rejects discarded branches not found in the explored matrix."""
    branch_1 = ThoughtBranchState(branch_cid="branch_1", latent_content_hash="a" * 64, prm_score=0.9)

    with pytest.raises(ValidationError, match="discarded branch 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_cid="trace_123",
            explored_branches=[branch_1],
            discarded_branches=["branch_invalid"],
            resolution_branch_cid=None,
            total_latent_tokens=100,
        )


def test_stochastic_ideation_serialization() -> None:
    from coreason_manifest.spec.ontology import (
        EpistemicEntropyState,
        EpistemicStatusProfile,
        HypothesisSuperposition,
        SemanticDivergenceProfile,
        StochasticDebateLog,
        StochasticIdeationTopology,
        StochasticPhaseProfile,
        ThermodynamicIdeationBudget,
        UnverifiedHypothesis,
    )

    budget = ThermodynamicIdeationBudget(
        max_heuristic_tokens=10000, max_debate_turns=10, minimum_entropy_delta_per_turn=0.1
    )
    divergence_monitor = SemanticDivergenceProfile(
        anchor_embedding_hash="a" * 64, current_cosine_drift=0.1, max_allowable_divergence=0.5
    )

    log1 = StochasticDebateLog(
        log_cid="did:log:01_abc",
        agent_role="generator",
        unstructured_content="Idea 1",
        entropy_state=EpistemicEntropyState(shannon_entropy_index=2.0, bayesian_surprise_score=0.5),
    )
    log2 = StochasticDebateLog(
        log_cid="did:log:02_abc",
        agent_role="critic",
        unstructured_content="Idea 1 is bad",
        entropy_state=EpistemicEntropyState(shannon_entropy_index=1.8, bayesian_surprise_score=0.4),
        parent_log_cid="did:log:01_abc",
    )

    hypothesis = UnverifiedHypothesis(
        hypothesis_cid="did:hypo:01_abc",
        proposed_strategy="Use Idea 1",
        epistemic_entropy=EpistemicEntropyState(shannon_entropy_index=1.0, bayesian_surprise_score=0.1),
        unresolved_frictions=["Friction B", "Friction A"],
    )

    superposition = HypothesisSuperposition(competing_strategies=[hypothesis], wave_collapse_function="lowest_entropy")

    topology = StochasticIdeationTopology(
        topology_cid="did:topology:01_abc",
        phase=StochasticPhaseProfile.DIVERGENT_BRAINSTORMING,
        ideation_budget=budget,
        divergence_monitor=divergence_monitor,
        debate_graph=[log2, log1],  # Test sorting
        superposition_state=superposition,
    )

    from coreason_manifest.spec.ontology import LatentScratchpadReceipt

    receipt = LatentScratchpadReceipt(
        trace_cid="trace_123",
        explored_branches=[topology],
        discarded_branches=[],
        resolution_branch_cid=None,
        total_latent_tokens=100,
    )

    stoch_top = receipt.explored_branches[0]
    assert stoch_top.topology_class == "stochastic_ideation"
    assert stoch_top.epistemic_status == EpistemicStatusProfile.UNVERIFIED_STOCHASTIC
    assert stoch_top.debate_graph[0].log_cid == "did:log:01_abc"
    if stoch_top.superposition_state is not None:
        assert stoch_top.superposition_state.competing_strategies[0].unresolved_frictions == [
            "Friction A",
            "Friction B",
        ]

    dump = receipt.model_dump_canonical()
    assert b"unverified_stochastic" in dump
