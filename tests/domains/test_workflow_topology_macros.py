# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.oversight.governance import PredictionMarketPolicy, QuorumPolicy
from coreason_manifest.workflow.topologies import AdversarialMarketTopology, ConsensusFederationTopology


def test_adversarial_market_topology_compilation() -> None:
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_magnitude=100, convergence_delta_threshold=0.1
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
        staking_function="quadratic", min_liquidity_magnitude=100, convergence_delta_threshold=0.1
    )
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        AdversarialMarketTopology(
            blue_team_ids=["did:web:agent_a"],
            red_team_ids=["did:web:agent_a"],
            adjudicator_id="did:web:adj",
            market_rules=policy,
        )


def test_consensus_federation_topology_compilation() -> None:
    quorum = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    macro = ConsensusFederationTopology(
        participant_ids=["did:web:node1", "did:web:node2", "did:web:node3", "did:web:node4"],
        adjudicator_id="did:web:seq",
        quorum_rules=quorum,
    )
    compiled = macro.compile_to_base_topology()
    assert compiled.type == "council"
    assert compiled.adjudicator_id == "did:web:seq"
    assert "did:web:node1" in compiled.nodes
    assert compiled.consensus_policy is not None
    assert compiled.consensus_policy.strategy == "pbft"


def test_consensus_federation_topology_adjudicator_isolation() -> None:
    quorum = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        ConsensusFederationTopology(
            participant_ids=["did:web:node1", "did:web:seq", "did:web:node3", "did:web:node4"],
            adjudicator_id="did:web:seq",
            quorum_rules=quorum,
        )
