# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopology,
    LatentScratchpadReceipt,
    PredictionMarketPolicy,
    SecureSubSessionState,
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
