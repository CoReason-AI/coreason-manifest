# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import uuid

from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.stochastic import (
    IdeationPhase,
    StochasticConsensus,
    StochasticStateNode,
    StochasticTopology,
)


@st.composite
def stochastic_state_node_strategy(draw):
    return StochasticStateNode(
        node_cid=draw(st.uuids()),
        parent_node_cid=None,  # Handled in higher level strategy
        agent_role=draw(st.sampled_from(["generator", "critic", "synthesizer"])),
        stochastic_tensor=draw(st.text()),
        epistemic_entropy=draw(st.floats(min_value=0.0, max_value=1.0)),
    )


@st.composite
def stochastic_graph_strategy(draw):
    nodes = draw(st.lists(stochastic_state_node_strategy(), min_size=1, max_size=10))
    # Give some nodes a valid parent_node_cid
    for i in range(1, len(nodes)):
        if draw(st.booleans()):
            # Pick a parent from earlier in the list to form a DAG
            parent_idx = draw(st.integers(min_value=0, max_value=i - 1))
            nodes[i].parent_node_cid = nodes[parent_idx].node_cid
    return nodes


@st.composite
def stochastic_consensus_strategy(draw):
    return StochasticConsensus(
        consensus_cid=draw(st.uuids()),
        proposed_manifold=draw(st.text()),
        convergence_confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
        residual_entropy_vectors=draw(st.lists(st.text())),
    )


@st.composite
def stochastic_topology_strategy(draw):
    return StochasticTopology(
        topology_cid=draw(st.uuids()),
        phase=draw(st.sampled_from(IdeationPhase)),
        stochastic_graph=draw(stochastic_graph_strategy()),
        consensus=draw(st.one_of(st.none(), stochastic_consensus_strategy())),
    )


@given(stochastic_topology_strategy())
def test_immutability_of_epistemic_status(topology: StochasticTopology):
    """
    Assertion 1: Mathematically prove that `epistemic_status` remains immutably
    "stochastically_unbounded" and cannot be mutated post-instantiation.
    """
    assert topology.epistemic_status == "stochastically_unbounded"

    # Attempt mutation and assert it fails due to validate_assignment=True on CoreasonBaseState
    # and Literal typing constraints
    try:
        topology.epistemic_status = "bounded"  # type: ignore
        raise AssertionError("Mutation should have raised a ValidationError")
    except ValidationError:
        pass


@given(stochastic_graph_strategy(), st.uuids())
def test_referential_integrity(valid_graph: list[StochasticStateNode], external_uuid: uuid.UUID):
    """
    Assertion 2: Prove that any populated `parent_node_cid` strictly maps to an existing
    `node_cid` within the `stochastic_graph`, or raise a modeled validation error.
    """
    # Create valid topology
    topology = StochasticTopology(
        phase=IdeationPhase.STOCHASTIC_DIFFUSION,
        stochastic_graph=valid_graph,
    )
    assert topology is not None

    # Tamper with the graph by introducing a dangling parent_node_cid
    invalid_graph = list(valid_graph)
    # Ensure external_uuid is definitely not in the graph
    node_cids = {n.node_cid for n in invalid_graph}
    if external_uuid in node_cids:
        return  # Skip if randomly generated uuid clashes

    invalid_node = StochasticStateNode(
        node_cid=uuid.uuid4(),
        parent_node_cid=external_uuid,
        agent_role="generator",
        stochastic_tensor="invalid",
        epistemic_entropy=0.5,
    )
    invalid_graph.append(invalid_node)

    try:
        StochasticTopology(
            phase=IdeationPhase.STOCHASTIC_DIFFUSION,
            stochastic_graph=invalid_graph,
        )
        raise AssertionError("Referential integrity validation should have failed")
    except ValidationError:
        pass


@given(stochastic_topology_strategy())
def test_serialization_isomorphism(topology: StochasticTopology):
    """
    Assertion 3: Prove zero-loss round-trip JSON serialization retaining all `_cid` lineages.
    """
    json_data = topology.model_dump_json()
    restored_topology = StochasticTopology.model_validate_json(json_data)

    assert topology.topology_cid == restored_topology.topology_cid
    assert topology.topology_type == restored_topology.topology_type
    assert topology.phase == restored_topology.phase
    assert topology.epistemic_status == restored_topology.epistemic_status

    # Check DAG nodes
    assert len(topology.stochastic_graph) == len(restored_topology.stochastic_graph)
    for orig_node, rest_node in zip(topology.stochastic_graph, restored_topology.stochastic_graph, strict=False):
        assert orig_node.node_cid == rest_node.node_cid
        assert orig_node.parent_node_cid == rest_node.parent_node_cid
        assert orig_node.agent_role == rest_node.agent_role
        assert orig_node.stochastic_tensor == rest_node.stochastic_tensor
        assert orig_node.epistemic_entropy == rest_node.epistemic_entropy

    # Check Consensus if present
    if topology.consensus:
        assert restored_topology.consensus is not None
        assert topology.consensus.consensus_cid == restored_topology.consensus.consensus_cid
        assert topology.consensus.proposed_manifold == restored_topology.consensus.proposed_manifold
        assert topology.consensus.convergence_confidence == restored_topology.consensus.convergence_confidence
        assert topology.consensus.residual_entropy_vectors == restored_topology.consensus.residual_entropy_vectors
    else:
        assert restored_topology.consensus is None

    # Full equality check
    assert topology == restored_topology
