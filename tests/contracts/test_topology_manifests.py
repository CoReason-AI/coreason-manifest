import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ConsensusPolicy,
    CouncilTopologyManifest,
    DAGTopologyManifest,
    EscrowPolicy,
    MarketContract,
    MultimodalTokenAnchorState,
    QuorumPolicy,
    SystemNodeProfile,
    TaskAwardReceipt,
)


def test_council_topology_enforce_funded_byzantine_slashing():
    quorum_rules = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )
    consensus_policy = ConsensusPolicy(strategy="pbft", quorum_rules=quorum_rules)
    nodes = {
        "did:web:adj": SystemNodeProfile(description="Adjudicator Node"),
        "did:web:n1": SystemNodeProfile(description="Worker 1"),
        "did:web:n2": SystemNodeProfile(description="Worker 2"),
        "did:web:n3": SystemNodeProfile(description="Worker 3"),
        "did:web:n4": SystemNodeProfile(description="Worker 4"),
    }

    with pytest.raises(
        ValidationError,
        match=r"Topological Interlock Failed: PBFT with slash_escrow requires a funded council_escrow\.",
    ):
        CouncilTopologyManifest(adjudicator_id="did:web:adj", nodes=nodes, consensus_policy=consensus_policy)

    with pytest.raises(
        ValidationError,
        match=r"Topological Interlock Failed: PBFT with slash_escrow requires a funded council_escrow\.",
    ):
        CouncilTopologyManifest(
            adjudicator_id="did:web:adj",
            nodes=nodes,
            consensus_policy=consensus_policy,
            council_escrow=EscrowPolicy(
                escrow_locked_magnitude=0, release_condition_metric="pass", refund_target_node_id="did:web:user"
            ),
        )

    manifest = CouncilTopologyManifest(
        adjudicator_id="did:web:adj",
        nodes=nodes,
        consensus_policy=consensus_policy,
        council_escrow=EscrowPolicy(
            escrow_locked_magnitude=100, release_condition_metric="pass", refund_target_node_id="did:web:user"
        ),
    )
    assert manifest.adjudicator_id == "did:web:adj"


def test_council_topology_check_adjudicator_id():
    nodes = {
        "did:web:n1": SystemNodeProfile(description="Worker 1"),
    }
    with pytest.raises(ValidationError, match=r"Adjudicator ID 'did:web:adj' is not in nodes registry\."):
        CouncilTopologyManifest(adjudicator_id="did:web:adj", nodes=nodes)


def test_dag_topology_verify_edges_exist():
    nodes = {
        "did:web:n1": SystemNodeProfile(description="Worker 1"),
        "did:web:n2": SystemNodeProfile(description="Worker 2"),
        "did:web:n3": SystemNodeProfile(description="Worker 3"),
    }

    manifest = DAGTopologyManifest(
        nodes=nodes, edges=[("did:web:n1", "did:web:n2"), ("did:web:n2", "did:web:n3")], max_depth=10, max_fan_out=10
    )
    assert manifest.edges == sorted([("did:web:n1", "did:web:n2"), ("did:web:n2", "did:web:n3")])

    draft_manifest = DAGTopologyManifest(
        lifecycle_phase="draft", nodes=nodes, edges=[("did:web:n1", "did:web:missing")], max_depth=10, max_fan_out=10
    )
    assert len(draft_manifest.edges) == 1

    with pytest.raises(ValidationError, match=r"Edge source 'did:web:missing' does not exist in nodes registry\."):
        DAGTopologyManifest(nodes=nodes, edges=[("did:web:missing", "did:web:n2")], max_depth=10, max_fan_out=10)

    with pytest.raises(ValidationError, match=r"Edge target 'did:web:missing' does not exist in nodes registry\."):
        DAGTopologyManifest(nodes=nodes, edges=[("did:web:n1", "did:web:missing")], max_depth=10, max_fan_out=10)

    with pytest.raises(ValidationError, match=r"Graph contains cycles but allow_cycles is False\."):
        DAGTopologyManifest(
            nodes=nodes,
            edges=[("did:web:n1", "did:web:n2"), ("did:web:n2", "did:web:n3"), ("did:web:n3", "did:web:n1")],
            max_depth=10,
            max_fan_out=10,
        )

    with pytest.raises(ValidationError, match=r"Graph contains cycles but allow_cycles is False\."):
        DAGTopologyManifest(nodes=nodes, edges=[("did:web:n1", "did:web:n1")], max_depth=10, max_fan_out=10)

    manifest_cycles = DAGTopologyManifest(
        nodes=nodes,
        edges=[("did:web:n1", "did:web:n2"), ("did:web:n2", "did:web:n3"), ("did:web:n3", "did:web:n1")],
        max_depth=10,
        max_fan_out=10,
        allow_cycles=True,
    )
    assert len(manifest_cycles.edges) == 3


def test_task_award_receipt():
    with pytest.raises(ValidationError, match=r"Escrow locked amount cannot exceed the total cleared price\."):
        TaskAwardReceipt(
            task_id="task-1",
            awarded_syndicate={"did:web:n1": 100},
            cleared_price_magnitude=100,
            escrow=EscrowPolicy(
                escrow_locked_magnitude=200, release_condition_metric="pass", refund_target_node_id="did:web:user"
            ),
        )

    with pytest.raises(ValidationError, match="Syndicate allocation sum must exactly equal cleared_price_magnitude"):
        TaskAwardReceipt(
            task_id="task-1", awarded_syndicate={"did:web:n1": 50, "did:web:n2": 40}, cleared_price_magnitude=100
        )

    valid_receipt = TaskAwardReceipt(
        task_id="task-1",
        awarded_syndicate={"did:web:n1": 60, "did:web:n2": 40},
        cleared_price_magnitude=100,
        escrow=EscrowPolicy(
            escrow_locked_magnitude=50, release_condition_metric="pass", refund_target_node_id="did:web:user"
        ),
    )
    assert valid_receipt.cleared_price_magnitude == 100


def test_market_contract():
    with pytest.raises(
        ValidationError,
        match=r"ECONOMIC INVARIANT VIOLATION: slashing_penalty cannot exceed minimum_collateral\.",
    ):
        MarketContract(minimum_collateral=100.0, slashing_penalty=150.0)

    mc = MarketContract(minimum_collateral=100.0, slashing_penalty=50.0)
    assert mc.slashing_penalty == 50.0


def test_multimodal_token_anchor_state():
    with pytest.raises(ValidationError, match=r"If token_span_start is defined, token_span_end MUST be defined\."):
        MultimodalTokenAnchorState(token_span_start=10)

    with pytest.raises(ValidationError, match=r"token_span_end cannot be defined without a token_span_start\."):
        MultimodalTokenAnchorState(token_span_end=20)

    with pytest.raises(ValidationError, match=r"token_span_end MUST be strictly greater than token_span_start\."):
        MultimodalTokenAnchorState(token_span_start=10, token_span_end=10)

    with pytest.raises(ValidationError, match=r"Spatial invariant violated: min bounds .* exceed max bounds .*"):
        MultimodalTokenAnchorState(bounding_box=(0.8, 0.2, 0.5, 0.6))

    with pytest.raises(ValidationError, match=r"Spatial invariant violated: min bounds .* exceed max bounds .*"):
        MultimodalTokenAnchorState(bounding_box=(0.2, 0.8, 0.5, 0.6))

    valid = MultimodalTokenAnchorState(token_span_start=10, token_span_end=20, bounding_box=(0.1, 0.2, 0.5, 0.6))
    assert valid.token_span_end == 20
    assert valid.bounding_box == (0.1, 0.2, 0.5, 0.6)
