import pytest
from pydantic import ValidationError

from coreason_manifest.oversight.governance import PredictionMarketPolicy
from coreason_manifest.workflow.topologies import AdversarialMarketTopology


def test_adversarial_market_topology_compilation() -> None:
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_microcents=100, convergence_delta_threshold=0.1
    )
    macro = AdversarialMarketTopology(
        blue_team_ids=["did:web:blue_1"],
        red_team_ids=["did:web:red_1"],
        adjudicator_id="did:web:adj",
        market_rules=policy,
    )
    compiled = macro.compile_to_base_topology()
    assert compiled.type == "council"
    assert compiled.adjudicator_id == "did:web:adj"
    assert "did:web:blue_1" in compiled.nodes
    assert compiled.consensus_policy is not None
    assert compiled.consensus_policy.strategy == "prediction_market"


def test_adversarial_market_topology_disjoint_failure() -> None:
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_microcents=100, convergence_delta_threshold=0.1
    )
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        AdversarialMarketTopology(
            blue_team_ids=["did:web:agent_a"],
            red_team_ids=["did:web:agent_a"],
            adjudicator_id="did:web:adj",
            market_rules=policy,
        )
