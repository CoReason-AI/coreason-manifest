from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import given
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    ConsensusPolicy,
    CouncilTopologyManifest,
    DAGTopologyManifest,
    EpistemicSOPManifest,
    GenerativeManifoldSLA,
    PredictionMarketPolicy,
    ByzantineFaultTolerancePolicy,
    SemanticDiscoveryIntent,
    SystemNodeProfile,
    VectorEmbeddingState,
)

valid_node_id_st = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)
node_st = st.builds(SystemNodeProfile, description=st.text())


@st.composite
def nodes_dict_st(draw: st.DrawFn) -> dict[str, Any]:
    return draw(st.dictionaries(keys=valid_node_id_st, values=node_st, min_size=1, max_size=10))


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_cycle_rejection(nodes: dict[str, Any], data: st.DataObject) -> None:
    """Prove DAGTopologyManifest raises ValidationError when cycles are explicitly formed and allow_cycles is False."""
    keys = list(nodes.keys())
    node_a = data.draw(st.sampled_from(keys))
    node_b = data.draw(st.sampled_from(keys))

    with pytest.raises(ValidationError, match="Graph contains cycles but allow_cycles is False"):
        DAGTopologyManifest(
            nodes=nodes, edges=[(node_a, node_b), (node_b, node_a)], allow_cycles=False, max_depth=10, max_fan_out=10
        )


def test_adversarial_market_disjoint_failure() -> None:
    """Prove Red/Blue team structural overlap triggers a topological contradiction."""
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_magnitude=100, convergence_delta_threshold=0.1
    )
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        AdversarialMarketTopologyManifest(
            blue_team_ids=["did:web:agent_a"],
            red_team_ids=["did:web:agent_a"],
            adjudicator_id="did:web:adj",
            market_rules=policy,
        )


def test_council_topology_byzantine_slash_requires_escrow() -> None:
    """Prove that CouncilTopologyManifest strictly requires a funded escrow when PBFT slashing is enabled."""
    nodes: dict[str, Any] = {"did:web:node_1": SystemNodeProfile(description="The Oracle")}
    quorum = ByzantineFaultTolerancePolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )

    with pytest.raises(ValidationError, match="PBFT with slash_escrow requires a funded council_escrow"):
        CouncilTopologyManifest(
            nodes=nodes,
            adjudicator_id="did:web:node_1",
            consensus_policy=ConsensusPolicy(strategy="pbft", quorum_rules=quorum),
        )


@given(depth=st.integers(min_value=1, max_value=10000), fanout=st.integers(min_value=1, max_value=10000))
def test_generative_manifold_geometric_explosion(depth: int, fanout: int) -> None:
    """Prove that GenerativeManifoldSLA mathematically rejects configurations that cause geometric explosion."""
    from hypothesis import assume

    assume(depth * fanout > 1000)

    with pytest.raises(ValidationError, match="Geometric explosion risk"):
        GenerativeManifoldSLA(max_topological_depth=depth, max_node_fanout=fanout, max_synthetic_tokens=1000)


@given(min_isometry_score=st.sampled_from([1.5, -2.0]))
def test_semantic_discovery_isometry_bounds(min_isometry_score: float) -> None:
    """Prove that SemanticDiscoveryIntent rejects out-of-bounds isometry scores."""
    vector = VectorEmbeddingState(vector_base64="aGVsbG8=", dimensionality=10, model_name="test-model")
    with pytest.raises(ValidationError):
        SemanticDiscoveryIntent(
            query_vector=vector, min_isometry_score=min_isometry_score, required_structural_types=["read_only"]
        )


@given(
    sop_id=st.text(min_size=1),
    target_persona=st.from_regex(r"^[a-zA-Z0-9_-]+$", fullmatch=True),
    ghost_source=st.text(min_size=1),
    ghost_target=st.text(min_size=1),
)
def test_epistemic_sop_ghost_node_rejection(
    sop_id: str, target_persona: str, ghost_source: str, ghost_target: str
) -> None:
    """Prove that EpistemicSOPManifest throws a ValidationError if an edge points to an undefined step."""
    # Build an empty cognitive_steps dictionary to easily test ghost nodes

    with pytest.raises(ValidationError, match="Ghost node referenced"):
        EpistemicSOPManifest(
            sop_id=sop_id,
            target_persona=target_persona,
            cognitive_steps={},
            structural_grammar_hashes={},
            chronological_flow_edges=[(ghost_source, ghost_target)],
            prm_evaluations=[],
        )
