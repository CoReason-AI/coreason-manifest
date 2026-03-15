# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AnyNodeProfile,
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


# --- 1. Market Contract Fuzzing ---
@given(collateral=st.floats(min_value=0.0, max_value=1e6), penalty=st.floats(min_value=0.0, max_value=1e6))
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_market_contract_bounds(collateral: float, penalty: float) -> None:
    """Mathematically prove the economic invariant: penalty <= collateral."""
    if penalty > collateral:
        with pytest.raises(ValidationError, match="slashing_penalty cannot exceed minimum_collateral"):
            MarketContract(minimum_collateral=collateral, slashing_penalty=penalty)
    else:
        contract = MarketContract(minimum_collateral=collateral, slashing_penalty=penalty)
        assert contract.slashing_penalty == penalty


# --- 2. Multimodal Anchor Fuzzing & Atomicity ---
@given(start=st.integers(min_value=0, max_value=10000), span_len=st.integers(min_value=1, max_value=1000))
def test_multimodal_anchor_1d_fuzz_valid(start: int, span_len: int) -> None:
    """Prove the 1D token bounds accept infinite valid mathematical spans."""
    anchor = MultimodalTokenAnchorState(token_span_start=start, token_span_end=start + span_len)
    assert anchor.token_span_end is not None
    assert anchor.token_span_end > start


@pytest.mark.parametrize(
    ("start", "end", "match_str"),
    [
        (10, None, r"token_span_end MUST be defined"),
        (None, 20, r"cannot be defined without a token_span_start"),
        (10, 10, r"MUST be strictly greater than"),
        (20, 10, r"MUST be strictly greater than"),
    ],
)
def test_multimodal_anchor_1d_atomic_invalid(start: int | None, end: int | None, match_str: str) -> None:
    """Prove invalid 1D geometries are structurally severed."""
    with pytest.raises(ValidationError, match=match_str):
        MultimodalTokenAnchorState(token_span_start=start, token_span_end=end)


@pytest.mark.parametrize(
    "box",
    [
        (0.8, 0.2, 0.5, 0.6),  # x_min > x_max
        (0.2, 0.8, 0.5, 0.6),  # y_min > y_max
    ],
)
def test_multimodal_anchor_2d_atomic_invalid(box: tuple[float, float, float, float]) -> None:
    """Prove mathematically impossible 2D spatial geometries are rejected."""
    from coreason_manifest.spec.ontology import SpatialBoundingBoxProfile
    with pytest.raises(ValidationError, match="cannot be strictly greater than"):
        MultimodalTokenAnchorState(bounding_box=SpatialBoundingBoxProfile(x_min=box[0], y_min=box[1], x_max=box[2], y_max=box[3]))


# --- 3. DAG Topology Atomicity ---
@pytest.mark.parametrize(
    ("edges", "match_str"),
    [
        ([("did:web:missing", "did:web:n2")], r"Edge source 'did:web:missing' does not exist"),
        ([("did:web:n1", "did:web:missing")], r"Edge target 'did:web:missing' does not exist"),
        (
            [("did:web:n1", "did:web:n2"), ("did:web:n2", "did:web:n3"), ("did:web:n3", "did:web:n1")],
            r"Graph contains cycles",
        ),
        ([("did:web:n1", "did:web:n1")], r"Graph contains cycles"),
    ],
)
def test_dag_topology_atomic_invalid_edges(edges: list[tuple[str, str]], match_str: str) -> None:
    """Prove specific ghost nodes and cyclic dependencies collapse the instantiation."""
    nodes: dict[str, AnyNodeProfile] = {
        "did:web:n1": SystemNodeProfile(description="W1"),
        "did:web:n2": SystemNodeProfile(description="W2"),
        "did:web:n3": SystemNodeProfile(description="W3"),
    }
    with pytest.raises(ValidationError, match=match_str):
        DAGTopologyManifest(nodes=nodes, edges=edges, max_depth=10, max_fan_out=10)


# --- 4. Council Topology Atomicity ---
def test_council_topology_missing_adjudicator() -> None:
    nodes: dict[str, AnyNodeProfile] = {"did:web:n1": SystemNodeProfile(description="W1")}
    with pytest.raises(ValidationError, match=r"Adjudicator ID 'did:web:adj' is not in nodes registry"):
        CouncilTopologyManifest(adjudicator_id="did:web:adj", nodes=nodes)


def test_council_topology_unfunded_slashing_none() -> None:
    nodes: dict[str, AnyNodeProfile] = {"did:web:adj": SystemNodeProfile(description="Adj")}
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )
    consensus = ConsensusPolicy(strategy="pbft", quorum_rules=quorum)

    with pytest.raises(ValidationError, match=r"PBFT with slash_escrow requires a funded council_escrow"):
        CouncilTopologyManifest(
            adjudicator_id="did:web:adj", nodes=nodes, consensus_policy=consensus, council_escrow=None
        )


def test_council_topology_unfunded_slashing_zero() -> None:
    nodes: dict[str, AnyNodeProfile] = {"did:web:adj": SystemNodeProfile(description="Adj")}
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )
    consensus = ConsensusPolicy(strategy="pbft", quorum_rules=quorum)
    escrow = EscrowPolicy(
        escrow_locked_magnitude=0, release_condition_metric="pass", refund_target_node_id="did:web:user"
    )

    with pytest.raises(ValidationError, match=r"PBFT with slash_escrow requires a funded council_escrow"):
        CouncilTopologyManifest(
            adjudicator_id="did:web:adj", nodes=nodes, consensus_policy=consensus, council_escrow=escrow
        )


# --- 5. Task Award Receipt Fuzzing ---
@given(
    cleared_price=st.integers(min_value=1, max_value=100000),
    locked_amount=st.integers(min_value=1, max_value=200000),
)
def test_task_award_escrow_bounds(cleared_price: int, locked_amount: int) -> None:
    """Mathematically prove the physical limit: escrow cannot exceed cleared price."""
    escrow = EscrowPolicy(
        escrow_locked_magnitude=locked_amount, release_condition_metric="pass", refund_target_node_id="did:web:user"
    )

    if locked_amount > cleared_price:
        with pytest.raises(ValidationError, match=r"Escrow locked amount cannot exceed the total cleared price"):
            TaskAwardReceipt(
                task_id="t1",
                awarded_syndicate={"did:web:n1": cleared_price},
                cleared_price_magnitude=cleared_price,
                escrow=escrow,
            )
    else:
        receipt = TaskAwardReceipt(
            task_id="t1",
            awarded_syndicate={"did:web:n1": cleared_price},
            cleared_price_magnitude=cleared_price,
            escrow=escrow,
        )
        assert receipt.cleared_price_magnitude == cleared_price
