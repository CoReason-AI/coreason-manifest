from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import given
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopology,
    ConsensusPolicy,
    CouncilTopology,
    DAGTopology,
    PredictionMarketPolicy,
    QuorumPolicy,
    SystemNode,
)

valid_node_id_st = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)
node_st = st.builds(SystemNode, description=st.text())


@st.composite
def nodes_dict_st(draw: st.DrawFn) -> dict[str, Any]:
    return draw(st.dictionaries(keys=valid_node_id_st, values=node_st, min_size=1, max_size=10))


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_cycle_rejection(nodes: dict[str, Any], data: st.DataObject) -> None:
    """Prove DAGTopology raises ValidationError when cycles are explicitly formed and allow_cycles is False."""
    keys = list(nodes.keys())
    node_a = data.draw(st.sampled_from(keys))
    node_b = data.draw(st.sampled_from(keys))

    with pytest.raises(ValidationError, match="Graph contains cycles but allow_cycles is False"):
        DAGTopology(
            nodes=nodes, edges=[(node_a, node_b), (node_b, node_a)], allow_cycles=False, max_depth=10, max_fan_out=10
        )


def test_adversarial_market_disjoint_failure() -> None:
    """Prove Red/Blue team structural overlap triggers a topological contradiction."""
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_magnitude=100, convergence_delta_threshold=0.1
    )
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        AdversarialMarketTopology(
            blue_team_ids=["did:web:agent_a"],
            red_team_ids=["did:web:agent_a"],
            adjudicator_id="did:web:adj",
            market_rules=policy,
        )


def test_council_topology_byzantine_slash_requires_escrow() -> None:
    """Prove that CouncilTopology strictly requires a funded escrow when PBFT slashing is enabled."""
    nodes: dict[str, Any] = {"did:web:node_1": SystemNode(description="The Oracle")}
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )

    with pytest.raises(ValidationError, match="PBFT with slash_escrow requires a funded council_escrow"):
        CouncilTopology(
            nodes=nodes,
            adjudicator_id="did:web:node_1",
            consensus_policy=ConsensusPolicy(strategy="pbft", quorum_rules=quorum),
        )
