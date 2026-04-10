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
from hypothesis import HealthCheck, given, settings

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    AgentDebateLog,
    CognitiveSystemNodeProfile,
    CouncilTopologyManifest,
    EnsembleConsensus,
    IdeationPhase,
    IdeationTopology,
    PredictionMarketPolicy,
)

# W3C DID specification regex from NodeCIDState
did_strategy = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)


@st.composite
def valid_adversarial_topology(draw: st.DrawFn) -> dict[str, Any]:
    """Generates mathematically guaranteed disjoint topological sets to test compilation determinism."""
    # Generate an array of unique DIDs to prevent Pydantic disjoint overlap rejections
    all_dids = draw(st.lists(did_strategy, min_size=3, max_size=20, unique=True))

    adjudicator_cid = all_dids[0]

    # Split remaining DIDs into two non-empty sets for Red/Blue teams
    split_idx = draw(st.integers(min_value=1, max_value=len(all_dids) - 2))
    blue_team = all_dids[1 : split_idx + 1]
    red_team = all_dids[split_idx + 1 :]

    # Draw valid economic boundaries
    market_rules = PredictionMarketPolicy(
        staking_function=draw(st.sampled_from(["linear", "quadratic"])),
        min_liquidity_magnitude=draw(st.integers(min_value=0, max_value=10000)),
        convergence_delta_threshold=draw(st.floats(min_value=0.0, max_value=1.0)),
    )

    return {
        "adjudicator_cid": adjudicator_cid,
        "blue_team": blue_team,
        "red_team": red_team,
        "market_rules": market_rules,
    }


@given(topology_data=valid_adversarial_topology())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_adversarial_market_compile_fuzzing(topology_data: dict[str, Any]) -> None:
    """
    AGENT INSTRUCTION: Fuzz the topological compilation engine.
    Mathematically prove the zero-cost macro deterministically projects
    into a rigid CouncilTopologyManifest across infinite valid states.
    """
    manifest = AdversarialMarketTopologyManifest(
        adjudicator_cid=topology_data["adjudicator_cid"],
        blue_team_cids=topology_data["blue_team"],
        red_team_cids=topology_data["red_team"],
        market_rules=topology_data["market_rules"],
    )

    compiled = manifest.compile_to_base_topology()

    # Assert the structural bounds of the compiled projection
    assert isinstance(compiled, CouncilTopologyManifest)
    assert compiled.adjudicator_cid == topology_data["adjudicator_cid"]

    assert compiled.consensus_policy is not None
    assert compiled.consensus_policy.strategy == "prediction_market"
    assert compiled.consensus_policy.prediction_market_rules == topology_data["market_rules"]

    # Assert exact node mapping and ontological injection
    assert topology_data["adjudicator_cid"] in compiled.nodes
    assert isinstance(compiled.nodes[topology_data["adjudicator_cid"]], CognitiveSystemNodeProfile)
    assert compiled.nodes[topology_data["adjudicator_cid"]].description == "Synthesizing Adjudicator"

    for node_cid in topology_data["blue_team"]:
        assert node_cid in compiled.nodes
        assert compiled.nodes[node_cid].description == "Blue Team Member"

    for node_cid in topology_data["red_team"]:
        assert node_cid in compiled.nodes
        assert compiled.nodes[node_cid].description == "Red Team Member"

def test_red_team_blue_team_ideation() -> None:
    """
    Simulate a scenario where a Blue Team agent proposes a strategy and a Red Team
    agent heavily counters it. Populate EnsembleConsensus with multiple
    unresolved_frictions and a low confidence_score. Assert that Pydantic properly
    validates this schema, proving the manifest handles uncertainty and deep
    disagreement elegantly.
    """
    blue_generator = AgentDebateLog(
        agent_role="generator",
        unstructured_content="We should refactor the core execution loop for speed.",
        confidence_score=0.6,
    )

    red_critic = AgentDebateLog(
        agent_role="critic",
        unstructured_content="Refactoring now introduces too much risk and breaks backward compatibility. Absolutely not.",
        confidence_score=0.95,
        parent_node_id=blue_generator.node_id,
    )

    consensus = EnsembleConsensus(
        proposed_strategy="Implement a feature flag to slowly roll out the new loop alongside the old one.",
        confidence_score=0.15,
        unresolved_frictions=[
            "The team lacks bandwidth to maintain two execution loops.",
            "Feature flags might add latency that defeats the purpose of the refactor."
        ],
    )

    topology = IdeationTopology(
        topology_type="ideation_ensemble",
        phase=IdeationPhase.ADVERSARIAL_CRITIQUE,
        debate_graph=[blue_generator, red_critic],
        consensus=consensus,
    )

    # Assert successful validation and correct structure
    assert topology.topology_type == "ideation_ensemble"
    assert topology.phase == IdeationPhase.ADVERSARIAL_CRITIQUE
    assert len(topology.debate_graph) == 2
    assert topology.consensus is not None
    assert topology.consensus.confidence_score == 0.15
    assert len(topology.consensus.unresolved_frictions) == 2
