import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EpistemicEntropyState,
    SemanticDivergenceProfile,
    StochasticDebateLog,
    StochasticIdeationTopology,
    StochasticPhaseProfile,
    ThermodynamicIdeationBudget,
)


def test_thermodynamic_halting_circuit_breaker() -> None:
    budget = ThermodynamicIdeationBudget(
        max_heuristic_tokens=10000, max_debate_turns=10, minimum_entropy_delta_per_turn=0.1
    )
    divergence_monitor = SemanticDivergenceProfile(
        anchor_embedding_hash="a" * 64, current_cosine_drift=0.1, max_allowable_divergence=0.5
    )

    log1 = StochasticDebateLog(
        log_cid="did:log:1_abc",
        agent_role="generator",
        unstructured_content="Idea 1",
        entropy_state=EpistemicEntropyState(shannon_entropy_index=2.0, bayesian_surprise_score=0.5),
    )
    log2 = StochasticDebateLog(
        log_cid="did:log:2_abc",
        agent_role="critic",
        unstructured_content="Idea 2",
        entropy_state=EpistemicEntropyState(shannon_entropy_index=1.5, bayesian_surprise_score=0.4),
    )
    log3 = StochasticDebateLog(
        log_cid="did:log:3_abc",
        agent_role="generator",
        unstructured_content="Idea 3",
        entropy_state=EpistemicEntropyState(shannon_entropy_index=0.95, bayesian_surprise_score=0.3),
    )
    log4 = StochasticDebateLog(
        log_cid="did:log:4_abc",
        agent_role="critic",
        unstructured_content="Idea 4",
        entropy_state=EpistemicEntropyState(shannon_entropy_index=0.95, bayesian_surprise_score=0.2),
    )

    with pytest.raises(ValidationError, match="Thermodynamic halt"):
        StochasticIdeationTopology(
            topology_cid="did:topology:01_abc",
            phase=StochasticPhaseProfile.DIVERGENT_BRAINSTORMING,
            ideation_budget=budget,
            divergence_monitor=divergence_monitor,
            debate_graph=[log1, log2, log3, log4],
            superposition_state=None,
        )


def test_vram_protection_string_length() -> None:
    # 100000 characters limit
    content = "a" * 100001
    with pytest.raises(ValidationError, match="String should have at most 100000 characters"):
        StochasticDebateLog(
            log_cid="did:log:1_abc",
            agent_role="generator",
            unstructured_content=content,
            entropy_state=EpistemicEntropyState(shannon_entropy_index=2.0, bayesian_surprise_score=0.5),
        )
