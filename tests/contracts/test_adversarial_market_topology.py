from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    CouncilTopologyManifest,
    PredictionMarketPolicy,
    SystemNodeProfile,
)


def test_compile_to_base_topology() -> None:
    adjudicator_id = "did:web:adjudicator"
    blue_team = ["did:web:blue1", "did:web:blue2"]
    red_team = ["did:web:red1", "did:web:red2"]

    market_rules = PredictionMarketPolicy(
        staking_function="linear", min_liquidity_magnitude=10, convergence_delta_threshold=0.01
    )

    manifest = AdversarialMarketTopologyManifest(
        adjudicator_id=adjudicator_id, blue_team_ids=blue_team, red_team_ids=red_team, market_rules=market_rules
    )

    compiled = manifest.compile_to_base_topology()

    assert isinstance(compiled, CouncilTopologyManifest)
    assert compiled.adjudicator_id == adjudicator_id
    assert compiled.consensus_policy is not None
    assert compiled.consensus_policy.strategy == "prediction_market"
    assert compiled.consensus_policy.prediction_market_rules == market_rules

    assert adjudicator_id in compiled.nodes
    adjudicator_node = compiled.nodes[adjudicator_id]
    assert isinstance(adjudicator_node, SystemNodeProfile)
    assert adjudicator_node.description == "Synthesizing Adjudicator"

    for node_id in blue_team:
        assert node_id in compiled.nodes
        blue_node = compiled.nodes[node_id]
        assert isinstance(blue_node, SystemNodeProfile)
        assert blue_node.description == "Blue Team Member"

    for node_id in red_team:
        assert node_id in compiled.nodes
        red_node = compiled.nodes[node_id]
        assert isinstance(red_node, SystemNodeProfile)
        assert red_node.description == "Red Team Member"
