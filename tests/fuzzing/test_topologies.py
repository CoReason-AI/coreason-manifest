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
import pytest
from hypothesis import given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    CausalDirectedEdgeState,
    CognitiveSystemNodeProfile,
    ConsensusPolicy,
    CouncilTopologyManifest,
    DAGTopologyManifest,
    DefeasibleCascadeEvent,
    EpistemicLedgerState,
    EpistemicSOPManifest,
    EvidentiaryGroundingSLA,
    GenerativeManifoldSLA,
    ObservationEvent,
    PredictionMarketPolicy,
    QuorumPolicy,
    SE3TransformProfile,
    SemanticDiscoveryIntent,
    SwarmTopologyManifest,
    TraceContextState,
    VectorEmbeddingState,
)

valid_node_id_st = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)
node_st = st.builds(CognitiveSystemNodeProfile, description=st.text())


@st.composite
def nodes_dict_st(draw: st.DrawFn) -> dict[str, Any]:
    return draw(st.dictionaries(keys=valid_node_id_st, values=node_st, min_size=1, max_size=10))


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_cycle_rejection(nodes: dict[str, Any], data: st.DataObject) -> None:
    """Prove DAGTopologyManifest raises ValidationError when cycles are explicitly formed and allow_cycles is False."""
    keys = list(nodes.keys())
    node_a = data.draw(st.sampled_from(keys))
    node_b = data.draw(st.sampled_from(keys))

    with pytest.raises(ValidationError, match="Graph contains cycles"):
        DAGTopologyManifest(
            nodes=nodes, edges=[(node_a, node_b), (node_b, node_a)], allow_cycles=False, max_depth=10, max_fan_out=10
        )


def test_adversarial_market_disjoint_failure() -> None:
    """Prove Red/Blue team structural overlap triggers a topological contradiction."""
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_magnitude=100, convergence_delta_threshold=0.1
    )
    with pytest.raises(ValidationError, match="Topological Contradiction"):
        AdversarialMarketTopologyManifest(
            blue_team_cids=["did:web:agent_a"],
            red_team_cids=["did:web:agent_a"],
            adjudicator_cid="did:web:adj",
            market_rules=policy,
        )


def test_council_topology_byzantine_slash_requires_escrow() -> None:
    """Prove that CouncilTopologyManifest strictly requires a funded escrow when PBFT slashing is enabled."""
    nodes: dict[str, Any] = {"did:web:node_1": CognitiveSystemNodeProfile(description="The Oracle")}
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )

    with pytest.raises(ValidationError, match="PBFT with slash_escrow requires a funded council_escrow"):
        CouncilTopologyManifest(
            nodes=nodes,
            adjudicator_cid="did:web:node_1",
            consensus_policy=ConsensusPolicy(strategy="pbft", quorum_rules=quorum),
        )


@given(depth=st.integers(min_value=1, max_value=100), fanout=st.integers(min_value=1, max_value=100))
def test_generative_manifold_accepts_large_geometry(depth: int, fanout: int) -> None:
    """Prove that GenerativeManifoldSLA accepts all valid geometries under UAB (enforce_geometric_bounds deleted)."""
    sla = GenerativeManifoldSLA(max_topological_depth=depth, max_node_fanout=fanout, max_synthetic_tokens=1000)
    assert sla.max_topological_depth == depth
    assert sla.max_node_fanout == fanout


@given(min_isometry_score=st.sampled_from([1.5, -2.0]))
def test_semantic_discovery_isometry_bounds(min_isometry_score: float) -> None:
    """Prove that SemanticDiscoveryIntent rejects out-of-bounds isometry scores."""
    vector = VectorEmbeddingState(vector_base64="aGVsbG8=", dimensionality=10, foundation_matrix_name="test-model")
    with pytest.raises(ValidationError):
        SemanticDiscoveryIntent(
            query_vector=vector, min_isometry_score=min_isometry_score, required_structural_types=["read_only"]
        )


@given(
    sop_cid=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
    target_persona=st.from_regex(r"^[a-zA-Z0-9_-]+$", fullmatch=True),
    ghost_source=st.text(min_size=1),
    ghost_target=st.text(min_size=1),
)
def test_epistemic_sop_ghost_node_rejection(
    sop_cid: str, target_persona: str, ghost_source: str, ghost_target: str
) -> None:
    """Prove that EpistemicSOPManifest throws a ValidationError if an edge points to an undefined step."""
    # Build an empty cognitive_steps dictionary to easily test ghost nodes

    with pytest.raises(ValidationError, match="Ghost node referenced"):
        EpistemicSOPManifest(
            sop_cid=sop_cid,
            target_persona=target_persona,
            cognitive_steps={},
            structural_grammar_hashes={},
            chronological_flow_edges=[(ghost_source, ghost_target)],
            prm_evaluations=[],
        )


# ==============================================================================
# Fuzzing tests added for CAUSAL cDAG & TOPOS FUZZER Agent Task
# ==============================================================================


@settings(max_examples=250, deadline=None)
@given(
    edges=st.lists(
        st.tuples(st.text(min_size=7, alphabet="abcdefg01234_-"), st.text(min_size=7, alphabet="abcdefg01234_-")),
        min_size=1,
        max_size=50,
    )
)
def test_dag_topology_cycles_and_bounds_fuzz(edges: list[tuple[str, str]]) -> None:
    edges_formatted = [("did:core:" + e[0], "did:core:" + e[1]) for e in edges]
    nodes: Any = {e[0]: {"topology_class": "agent", "description": "desc"} for e in edges_formatted} | {
        e[1]: {"topology_class": "agent", "description": "desc"} for e in edges_formatted
    }

    # We enforce constraints to trigger specific ValueErrors if they breach the limit.
    # Otherwise, it should instantiate without error.
    try:
        DAGTopologyManifest(
            topology_class="dag", nodes=nodes, edges=edges_formatted, max_depth=5, max_fan_out=5, allow_cycles=False
        )
        # If it succeeds, it must be valid.
    except ValueError as e:
        err_str = str(e).lower()
        if (
            "graph depth" in err_str
            or "graph contains cycles" in err_str
            or "exceeds max_fan_out" in err_str
            or "does not exist in nodes" in err_str
        ):
            pass  # Expected
        else:
            pytest.fail(f"Unexpected ValueError: {e}")


@settings(max_examples=250, deadline=None)
@given(
    nodes_dict=st.dictionaries(
        keys=st.text(min_size=7, alphabet="abcdefg01234_-").map(lambda x: "did:core:" + x),
        values=st.just({"topology_class": "agent", "description": "desc"}),
        min_size=1,
        max_size=50,
    ),
    spawning_threshold=st.integers(min_value=1, max_value=200),
    max_concurrent_agents=st.integers(min_value=1, max_value=100),
)
def test_swarm_topology_constraints_fuzz(
    nodes_dict: dict[str, Any], spawning_threshold: int, max_concurrent_agents: int
) -> None:
    try:
        SwarmTopologyManifest(
            topology_class="swarm",
            nodes=nodes_dict,
            spawning_threshold=spawning_threshold,
            max_concurrent_agents=max_concurrent_agents,
        )
        if spawning_threshold > max_concurrent_agents:
            pytest.fail("SwarmTopologyManifest failed to reject spawning_threshold > max_concurrent_agents")
    except ValueError as e:
        err_str = str(e).lower()
        if "spawning_threshold cannot exceed max_concurrent_agents" in err_str:
            pass  # Expected
        elif "validation error" in err_str:
            pass  # Expected (e.g. less_than_equal constraint from pydantic itself)
        else:
            pytest.fail(f"Unexpected ValueError: {e}")


@settings(max_examples=250, deadline=None)
@given(
    cascade_cid=st.text(min_size=7, alphabet="abcdefg01234_-"),
    root=st.text(min_size=7, alphabet="abcdefg01234_-"),
    quarantined=st.lists(st.text(min_size=7, alphabet="abcdefg01234_-"), min_size=1, max_size=20),
    decay=st.floats(min_value=-1.0, max_value=2.0),
)
def test_defeasible_cascade_logic_fuzz(cascade_cid: str, root: str, quarantined: list[str], decay: float) -> None:
    try:
        DefeasibleCascadeEvent(
            cascade_cid=cascade_cid,
            root_falsified_event_cid=root,
            propagated_decay_factor=decay,
            quarantined_event_cids=quarantined,
        )
        if root in quarantined:
            pytest.fail("DefeasibleCascadeEvent failed to reject root_falsified_event_cid in quarantined_event_cids")
        if decay < 0.0 or decay > 1.0:
            pytest.fail("DefeasibleCascadeEvent failed to reject out-of-bounds decay factor")
    except ValueError as e:
        err_str = str(e).lower()
        if (
            "root_falsified_event_cid cannot be in quarantined_event_cids" in err_str
            or "propagated_decay_factor" in err_str
        ):
            pass  # Expected
        elif "validation error" in err_str:
            pass  # pydantic validation
        else:
            pytest.fail(f"Unexpected ValueError: {e}")


@settings(max_examples=250, deadline=None)
@given(
    source=st.text(min_size=1, max_size=100),
    target=st.text(min_size=1, max_size=100),
    topology_class=st.sampled_from(["direct_cause", "confounder", "collider", "mediator"]),
)
def test_causal_directed_edge_state_fuzz(source: str, target: str, topology_class: Any) -> None:
    try:
        CausalDirectedEdgeState(
            source_variable=source,
            target_variable=target,
            edge_class=topology_class,
            predicate_curie="test:pred",
            grounding_sla=EvidentiaryGroundingSLA(
                minimum_nli_entailment_score=0.5,
                require_independent_sources=1,
                ungrounded_link_action="sever_edge",
                allowed_evidence_domains=["test"],
            ),
        )
        if source == target:
            pytest.fail("CausalDirectedEdgeState failed to reject self-referential edge")
    except ValueError as e:
        if "source_variable cannot equal target_variable" in str(e):
            pass  # Expected
        elif "validation error" in str(e).lower():
            pass
        else:
            pytest.fail(f"Unexpected ValueError: {e}")


@settings(max_examples=50, deadline=None)
@given(
    history=st.lists(
        st.builds(
            ObservationEvent,
            event_cid=st.text(min_size=1, max_size=128, alphabet="abcdefg01234_-"),
            timestamp=st.floats(min_value=0.0, max_value=253402300799.0),
            payload=st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=20), max_size=5),
        ),
        max_size=5,
    )
)
def test_epistemic_ledger_history_fuzz(history: Any) -> None:
    try:
        EpistemicLedgerState(history=history)
        # Should always succeed instantiation, but we sort the history
    except ValueError as e:
        if "Epistemic paradox" in str(e) or "validation error" in str(e).lower():
            pass
        else:
            pytest.fail(f"Unexpected ValueError: {e}")


# --- TraceContextState ---


@given(cid=st.from_regex(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", fullmatch=True))
def test_trace_context_span_topology_violation(cid: str) -> None:
    """Test that span_cid cannot equal parent_span_cid."""
    with pytest.raises(ValidationError) as exc_info:
        TraceContextState(trace_cid=cid, span_cid=cid, parent_span_cid=cid, causal_clock=0)
    assert "span_cid cannot equal parent_span_cid" in str(exc_info.value)


# --- SE3TransformProfile ---


def test_se3_transform_zero_quaternion() -> None:
    """Test that zero quaternion triggers ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SE3TransformProfile(reference_frame_cid="frame-xyz", x=0.0, y=0.0, z=0.0, qx=0.0, qy=0.0, qz=0.0, qw=0.0)
    assert "Quaternion cannot be a zero vector" in str(exc_info.value)
