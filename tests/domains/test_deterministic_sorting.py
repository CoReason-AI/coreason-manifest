# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopology,
    DAGTopology,
    EpistemicPromotionEvent,
    InformationClassification,
    LatentScratchpadReceipt,
    MarketResolutionState,
    OntologicalHandshake,
    PredictionMarketPolicy,
    PredictionMarketState,
    SaeLatentPolicy,
    SecureSubSessionState,
    SwarmTopology,
    ThoughtBranch,
    WorkflowManifest,
)


def test_secure_sub_session_sorting_determinism() -> None:
    """Prove that injecting chaotic arrays yields a mathematically pristine, sorted hash state."""
    session = SecureSubSessionState(
        session_id="sess_1",
        allowed_vault_keys=["vault:zeta", "vault:alpha", "vault:gamma"],
        max_ttl_seconds=300,
        description="Audit test",
    )
    assert session.allowed_vault_keys == ["vault:alpha", "vault:gamma", "vault:zeta"]


def test_latent_scratchpad_trace_sorting_determinism() -> None:
    """Prove that object arrays are deterministically sorted by their specific lambda key."""
    b1 = ThoughtBranch(branch_id="branch_Z", latent_content_hash="a" * 64)
    b2 = ThoughtBranch(branch_id="branch_A", latent_content_hash="b" * 64)

    trace = LatentScratchpadReceipt(
        trace_id="trace_1",
        explored_branches=[b1, b2],
        discarded_branches=["branch_Z", "branch_A"],
        total_latent_tokens=100,
    )

    assert trace.discarded_branches == ["branch_A", "branch_Z"]
    assert trace.explored_branches[0].branch_id == "branch_A"
    assert trace.explored_branches[1].branch_id == "branch_Z"


def test_adversarial_market_sorting_determinism() -> None:
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_magnitude=100, convergence_delta_threshold=0.1
    )
    macro = AdversarialMarketTopology(
        blue_team_ids=["did:web:node_Z", "did:web:node_A"],
        red_team_ids=["did:web:node_X", "did:web:node_B"],
        adjudicator_id="did:web:adj",
        market_rules=policy,
    )
    assert macro.blue_team_ids == ["did:web:node_A", "did:web:node_Z"]
    assert macro.red_team_ids == ["did:web:node_B", "did:web:node_X"]


def test_workflow_manifest_sorting_determinism() -> None:
    manifest = WorkflowManifest(
        manifest_version="1.0.0",
        topology=DAGTopology(
            nodes={},
            edges=[],
            max_depth=10,
            max_fan_out=10
        ),
        allowed_information_classifications=[
            InformationClassification.RESTRICTED,
            InformationClassification.PUBLIC,
            InformationClassification.INTERNAL,
        ]
    )
    assert manifest.allowed_information_classifications == ["internal", "public", "restricted"]


def test_swarm_topology_sorting_determinism() -> None:
    p1 = PredictionMarketState(
        market_id="mkt_Z",
        resolution_oracle_condition_id="cond1",
        lmsr_b_parameter="1.0",
        order_book=[],
        current_market_probabilities={},
    )
    p2 = PredictionMarketState(
        market_id="mkt_A",
        resolution_oracle_condition_id="cond2",
        lmsr_b_parameter="1.0",
        order_book=[],
        current_market_probabilities={},
    )

    r1 = MarketResolutionState(
        market_id="mkt_Y", winning_hypothesis_id="hyp1", falsified_hypothesis_ids=[], payout_distribution={}
    )
    r2 = MarketResolutionState(
        market_id="mkt_B", winning_hypothesis_id="hyp2", falsified_hypothesis_ids=[], payout_distribution={}
    )

    topology = SwarmTopology(nodes={}, active_prediction_markets=[p1, p2], resolved_markets=[r1, r2])
    assert topology.active_prediction_markets[0].market_id == "mkt_A"
    assert topology.active_prediction_markets[1].market_id == "mkt_Z"
    assert topology.resolved_markets[0].market_id == "mkt_B"
    assert topology.resolved_markets[1].market_id == "mkt_Y"


def test_ontological_handshake_sorting_determinism() -> None:
    handshake = OntologicalHandshake(
        handshake_id="hs_1",
        participant_node_ids=["did:web:node_Z", "did:web:node_A"],
        measured_cosine_similarity=0.99,
        alignment_status="aligned",
    )
    assert handshake.participant_node_ids == ["did:web:node_A", "did:web:node_Z"]


def test_sae_latent_policy_sorting_determinism() -> None:
    policy = SaeLatentPolicy(
        target_feature_index=42,
        monitored_layers=[12, 1, 8, 4],
        max_activation_threshold=2.5,
        violation_action="clamp",
        clamp_value=0.0,
        sae_dictionary_hash="a" * 64,
    )
    assert policy.monitored_layers == [1, 4, 8, 12]


def test_epistemic_promotion_event_sorting_determinism() -> None:
    event = EpistemicPromotionEvent(
        event_id="promo_1",
        timestamp=12345.0,
        source_episodic_event_ids=["obs_Z", "obs_A", "obs_M"],
        crystallized_semantic_node_id="did:web:semantic_1",
        compression_ratio=10.0,
    )
    assert event.source_episodic_event_ids == ["obs_A", "obs_M", "obs_Z"]
