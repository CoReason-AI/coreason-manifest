import math
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import DataObject
from pydantic import ValidationError

from coreason_manifest.workflow.nodes import (
    AgentNode,
    EpistemicScanner,
    HumanNode,
    SelfCorrectionPolicy,
    System1Reflex,
    SystemNode,
)
from coreason_manifest.workflow.topologies import CouncilTopology, DAGTopology

# Strategy for valid NodeIDs (alphanumeric, underscores, hyphens)
# Also must have a minimum length of 1 based on core primitives.
valid_node_id_st = st.from_regex(r"^[a-zA-Z0-9_-]+$", fullmatch=True).filter(lambda x: len(x) > 0)

# Strategy for BaseNode attributes
base_node_attrs = {
    "description": st.text(),
}

# Strategies for nodes
agent_node_st = st.builds(AgentNode, **base_node_attrs)
human_node_st = st.builds(HumanNode, **base_node_attrs)
system_node_st = st.builds(SystemNode, **base_node_attrs)

# Strategy for any valid node
any_node_st = st.one_of(agent_node_st, human_node_st, system_node_st)


# Strategy for a valid nodes dictionary
@st.composite
def nodes_dict_st(draw: Any) -> Any:
    return draw(st.dictionaries(keys=valid_node_id_st, values=any_node_st, min_size=1, max_size=10))


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_referential_integrity_success(nodes: dict[str, Any], data: DataObject) -> None:
    """Prove DAGTopology instantiated with edges connecting valid nodes never fails."""
    keys = list(nodes.keys())
    edges = data.draw(st.lists(st.tuples(st.sampled_from(keys), st.sampled_from(keys)), min_size=0, max_size=20))

    topology = DAGTopology(nodes=nodes, edges=edges)
    assert topology.edges == edges


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_referential_integrity_adversarial(nodes: dict[str, Any], data: DataObject) -> None:
    """Prove that injecting a ghost node into an edge tuple always raises a ValidationError."""
    ghost_node = "ghost_node_123"
    if ghost_node in nodes:
        del nodes[ghost_node]
        if not nodes:
            return

    keys = list(nodes.keys())
    valid_id_str = data.draw(st.sampled_from(keys))

    # Generate some valid edges, then inject a bad one
    valid_edges = data.draw(st.lists(st.tuples(st.sampled_from(keys), st.sampled_from(keys)), min_size=0, max_size=5))

    with pytest.raises(ValidationError) as exc_info:
        DAGTopology(nodes=nodes, edges=[*valid_edges, (valid_id_str, ghost_node)])
    assert "does not exist in nodes registry" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        DAGTopology(nodes=nodes, edges=[*valid_edges, (ghost_node, valid_id_str)])
    assert "does not exist in nodes registry" in str(exc_info.value)


@given(nodes=nodes_dict_st(), adjudicator_id=st.data())
def test_council_topology_referential_integrity_success(nodes: dict[str, Any], adjudicator_id: DataObject) -> None:
    """Test 1: Prove CouncilTopology instantiated with adjudicator_id from nodes dictionary never fails."""
    # Draw a valid key from the generated nodes
    valid_id_str = adjudicator_id.draw(st.sampled_from(list(nodes.keys())))

    topology = CouncilTopology(nodes=nodes, adjudicator_id=valid_id_str)
    assert topology.adjudicator_id == valid_id_str


@given(nodes=nodes_dict_st())
def test_council_topology_referential_integrity_adversarial(nodes: dict[str, Any]) -> None:
    """Test 2: Prove that injecting a guaranteed dangling pointer always raises a ValidationError."""
    rogue_id = "rogue_ghost_node"
    # Ensure it's strictly not in the nodes dictionary
    if rogue_id in nodes:
        del nodes[rogue_id]
        if not nodes:
            return  # Skip if nodes becomes empty

    with pytest.raises(ValidationError) as exc_info:
        CouncilTopology(nodes=nodes, adjudicator_id=rogue_id)

    assert "Adjudicator ID" in str(exc_info.value) or "Value error" in str(exc_info.value)


@given(confidence_threshold=st.floats(max_value=-0.000001) | st.floats(min_value=1.000001))
def test_system1_reflex_mathematical_bounds(confidence_threshold: float) -> None:
    """Test 3: Prove System1Reflex decisively rejects values outside [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        System1Reflex(confidence_threshold=confidence_threshold, allowed_read_only_tools=["tool_a"])


@given(dissonance_threshold=st.floats(max_value=-0.000001) | st.floats(min_value=1.000001))
def test_epistemic_scanner_mathematical_bounds(dissonance_threshold: float) -> None:
    """Test 4: Prove EpistemicScanner decisively rejects values outside [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        EpistemicScanner(active=True, dissonance_threshold=dissonance_threshold, action_on_gap="probe")


@given(max_loops=st.integers(max_value=-1) | st.integers(min_value=51))
def test_self_correction_policy_extreme_bounds(max_loops: int) -> None:
    """Prove SelfCorrectionPolicy decisively rejects extreme out-of-bounds loops."""
    with pytest.raises(ValidationError):
        SelfCorrectionPolicy(max_loops=max_loops, rollback_on_failure=True)


@given(confidence_threshold=st.sampled_from([math.nan, math.inf, -math.inf]))
def test_system1_reflex_toxic_floats(confidence_threshold: float) -> None:
    """Prove System1Reflex decisively rejects toxic floats (NaN, Inf, -Inf)."""
    with pytest.raises(ValidationError):
        System1Reflex(confidence_threshold=confidence_threshold, allowed_read_only_tools=["tool_a"])
