# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopology,
    EnsembleTopologyProfile,
    EvictionPolicy,
    LatentScratchpadReceipt,
    MigrationContract,
    PeftAdapterContract,
    PredictionMarketPolicy,
    SecureSubSessionState,
    ThoughtBranchState,
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
    b1 = ThoughtBranchState(branch_id="branch_Z", latent_content_hash="a" * 64)
    b2 = ThoughtBranchState(branch_id="branch_A", latent_content_hash="b" * 64)

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
    spec = EnsembleTopologyProfile(
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
