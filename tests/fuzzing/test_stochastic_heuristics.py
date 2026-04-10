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
    _ = log1
    _ = log2
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


def test_thermodynamic_halting_edge_cases() -> None:
    import pytest

    from coreason_manifest.spec.ontology import StochasticIdeationTopology

    class DummyItem:
        def __init__(self, entropy_val: float) -> None:
            class DummyEntropy:
                shannon_entropy_index = entropy_val

            self.entropy_state = DummyEntropy()
            self.log_cid = "did:log:abc_123"
            self.agent_role = "generator"
            self.unstructured_content = "Idea 1"

    class DummyBudget:
        minimum_entropy_delta_per_turn = 0.5

    data = {
        "debate_graph": [
            DummyItem(2.0),
            DummyItem(1.5),
            DummyItem(1.2),
        ],
        "ideation_budget": DummyBudget(),
    }

    with pytest.raises(ValueError, match="Thermodynamic halt"):
        StochasticIdeationTopology.model_validate(
            {
                "topology_cid": "did:topology:01_abc",
                "phase": "divergent_brainstorming",
                "ideation_budget": data["ideation_budget"],
                "divergence_monitor": {
                    "anchor_embedding_hash": "a" * 64,
                    "current_cosine_drift": 0.1,
                    "max_allowable_divergence": 0.5,
                },
                "debate_graph": data["debate_graph"],
                "superposition_state": None,
            }
        )

    data2 = {
        "debate_graph": [
            {"entropy_state": {"shannon_entropy_index": 2.0}},
            {"entropy_state": {"shannon_entropy_index": 1.5}},
            {"entropy_state": type("obj", (object,), {"shannon_entropy_index": 1.2})()},
        ],
        "ideation_budget": {"minimum_entropy_delta_per_turn": 0.5},
    }

    with pytest.raises(ValueError, match="Thermodynamic halt"):
        StochasticIdeationTopology.model_validate(
            {
                "topology_cid": "did:topology:01_abc",
                "phase": "divergent_brainstorming",
                "ideation_budget": data2["ideation_budget"],
                "divergence_monitor": {
                    "anchor_embedding_hash": "a" * 64,
                    "current_cosine_drift": 0.1,
                    "max_allowable_divergence": 0.5,
                },
                "debate_graph": data2["debate_graph"],
                "superposition_state": None,
            }
        )


def test_sort_key_empty() -> None:
    import pytest
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import LatentScratchpadReceipt

    class MockBranch:
        topology_class = "unknown"

    data = {
        "trace_cid": "trace_123",
        "explored_branches": [MockBranch()],
        "discarded_branches": [],
        "total_latent_tokens": 100,
    }

    # model_validate processes sort_key under _enforce_canonical_sort
    with pytest.raises(ValidationError):
        LatentScratchpadReceipt.model_validate(data)
