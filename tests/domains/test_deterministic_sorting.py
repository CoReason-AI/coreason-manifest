# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved

import json

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopology,
    BypassReceipt,
    DynamicRoutingManifest,
    ExecutionNodeReceipt,
    GlobalSemanticProfile,
    GrammarPanel,
    InsightCard,
    LatentScratchpadReceipt,
    MacroGridProfile,
    PredictionMarketPolicy,
    SecureSubSessionState,
    StatisticalChartExtractionState,
    ThoughtBranch,
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
