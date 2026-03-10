# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved

import json

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopology,
    EnsembleTopologySpec,
    EvictionPolicy,
    LatentScratchpadReceipt,
    MigrationContract,
    PeftAdapterContract,
    BypassReceipt,
    DAGTopology,
    DynamicRoutingManifest,
    EpistemicPromotionEvent,
    ExecutionNodeReceipt,
    GlobalSemanticProfile,
    GrammarPanel,
    InformationClassification,
    InsightCard,
    LatentScratchpadReceipt,
    MacroGridProfile,
    MarketResolutionState,
    OntologicalHandshake,
    PredictionMarketPolicy,
    PredictionMarketState,
    SaeLatentPolicy,
    SecureSubSessionState,
    StatisticalChartExtractionState,
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


def test_peft_adapter_contract_sorting_determinism() -> None:
    contract = PeftAdapterContract(
        adapter_id="adapter_1",
        safetensors_hash="a" * 64,
        base_model_hash="b" * 64,
        adapter_rank=16,
        target_modules=["v_proj", "q_proj", "k_proj"],
    )
    assert contract.target_modules == ["k_proj", "q_proj", "v_proj"]


def test_ensemble_topology_spec_sorting_determinism() -> None:
    spec = EnsembleTopologySpec(
        concurrent_branch_ids=["did:web:node_Z", "did:web:node_A", "did:web:node_M"],
        fusion_function="weighted_consensus",
    )
    assert spec.concurrent_branch_ids == ["did:web:node_A", "did:web:node_M", "did:web:node_Z"]


def test_eviction_policy_sorting_determinism() -> None:
    policy = EvictionPolicy(
        strategy="fifo",
        max_retained_tokens=1000,
        protected_event_ids=["event_Z", "event_A", "event_M"],
    )
    assert policy.protected_event_ids == ["event_A", "event_M", "event_Z"]


def test_migration_contract_sorting_determinism() -> None:
    contract = MigrationContract(
        contract_id="contract_1",
        source_version="1.0.0",
        target_version="1.1.0",
        path_transformations={},
        dropped_paths=["/z_path", "/a_path", "/m_path"],
    )
    assert contract.dropped_paths == ["/a_path", "/m_path", "/z_path"]
def test_workflow_manifest_sorting_determinism() -> None:
    manifest = WorkflowManifest(
        manifest_version="1.0.0",
        topology=DAGTopology(nodes={}, edges=[], max_depth=10, max_fan_out=10),
        allowed_information_classifications=[
            InformationClassification.RESTRICTED,
            InformationClassification.PUBLIC,
            InformationClassification.INTERNAL,
        ],
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


def test_execution_node_receipt_sorting_determinism() -> None:
    hashes = ["z_hash", "a_hash", "m_hash"]
    node = ExecutionNodeReceipt(request_id="req_1", inputs="input", outputs="output", parent_hashes=hashes)
    assert node.parent_hashes == ["a_hash", "m_hash", "z_hash"]


def test_dynamic_routing_manifest_sorting_determinism() -> None:
    profile = GlobalSemanticProfile(artifact_event_id="art_1", detected_modalities=["text"], token_density=10)
    b1 = BypassReceipt(
        artifact_event_id="art_1",
        bypassed_node_id="did:web:node_Z",
        justification="modality_mismatch",
        cryptographic_null_hash="0" * 64,
    )
    b2 = BypassReceipt(
        artifact_event_id="art_1",
        bypassed_node_id="did:web:node_A",
        justification="sla_timeout",
        cryptographic_null_hash="0" * 64,
    )

    manifest = DynamicRoutingManifest(
        manifest_id="man_1",
        artifact_profile=profile,
        active_subgraphs={"text": ["did:web:Z", "did:web:A"]},
        bypassed_steps=[b1, b2],
        branch_budgets_magnitude={"did:web:A": 10},
    )
    assert manifest.active_subgraphs["text"] == ["did:web:A", "did:web:Z"]
    assert manifest.bypassed_steps[0].bypassed_node_id == "did:web:node_A"
    assert manifest.bypassed_steps[1].bypassed_node_id == "did:web:node_Z"


def test_macro_grid_profile_sorting_determinism() -> None:
    p1 = InsightCard(panel_id="panel_Z", title="Z", markdown_content="Z")
    p2 = GrammarPanel(panel_id="panel_A", title="A", data_source_id="d1", mark="point", encodings=[])

    grid = MacroGridProfile(layout_matrix=[["panel_A", "panel_Z"]], panels=[p1, p2])
    assert grid.panels[0].panel_id == "panel_A"
    assert grid.panels[1].panel_id == "panel_Z"


def test_statistical_chart_extraction_sorting_determinism() -> None:
    data: list[dict[str, float | str]] = [{"x": 10.0, "y": "Z"}, {"x": 5.0, "y": "A"}]
    # "x": 10 vs "x": 5 json string sorting:
    # '{"x": 10, "y": "Z"}' vs '{"x": 5, "y": "A"}'
    # '{"x": 10' comes before '{"x": 5' algebraically in string sorts.

    state = StatisticalChartExtractionState(axes={}, data_series=data)
    expected_order = sorted(data, key=lambda x: json.dumps(x, sort_keys=True))
    assert state.data_series == expected_order
