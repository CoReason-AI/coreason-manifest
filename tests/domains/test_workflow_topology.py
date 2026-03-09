import math
from typing import Any

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from hypothesis.strategies import DataObject
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.oversight.governance import ConsensusPolicy, QuorumPolicy
from coreason_manifest.workflow.auctions import EscrowPolicy
from coreason_manifest.workflow.nodes import (
    AgentNode,
    EpistemicScanner,
    HumanNode,
    SelfCorrectionPolicy,
    System1Reflex,
    SystemNode,
)
from coreason_manifest.workflow.topologies import (
    AnyTopology,
    CouncilTopology,
    DAGTopology,
    DigitalTwinTopology,
    DynamicalSystemsTopology,
    EvaluatorOptimizerTopology,
    ODEGradientBounds,
    OntologicalAlignmentPolicy,
    SimulationConvergenceSLA,
)

# Strategy for valid NodeIDs (alphanumeric, underscores, hyphens)
# Also must have a minimum length of 1 based on core primitives.
valid_node_id_st = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)

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

    topology = DAGTopology(nodes=nodes, edges=edges, allow_cycles=True)
    assert topology.edges == edges


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_cycle_adversarial(nodes: dict[str, Any], data: DataObject) -> None:
    """Prove DAGTopology raises ValidationError when cycles are explicitly formed and allow_cycles is False."""
    keys = list(nodes.keys())
    node_a = data.draw(st.sampled_from(keys))
    node_b = data.draw(st.sampled_from(keys))

    with pytest.raises(ValidationError) as exc_info:
        DAGTopology(nodes=nodes, edges=[(node_a, node_b), (node_b, node_a)], allow_cycles=False)
    assert "Graph contains cycles but allow_cycles is False" in str(exc_info.value)


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_cycle_success(nodes: dict[str, Any], data: DataObject) -> None:
    """Prove DAGTopology instantiates successfully with explicitly formed cycles when allow_cycles is True."""
    keys = list(nodes.keys())
    node_a = data.draw(st.sampled_from(keys))
    node_b = data.draw(st.sampled_from(keys))

    topology = DAGTopology(nodes=nodes, edges=[(node_a, node_b), (node_b, node_a)], allow_cycles=True)
    assert topology.edges == [(node_a, node_b), (node_b, node_a)]


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_referential_integrity_adversarial(nodes: dict[str, Any], data: DataObject) -> None:
    """Prove that injecting a ghost node into an edge tuple always raises a ValidationError."""
    ghost_node = "did:web:ghost_node_123"
    assume(ghost_node not in nodes)

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
    rogue_id = "did:web:rogue_ghost_node"
    assume(rogue_id not in nodes)

    with pytest.raises(ValidationError) as exc_info:
        CouncilTopology(nodes=nodes, adjudicator_id=rogue_id)

    assert "Adjudicator ID" in str(exc_info.value) or "Value error" in str(exc_info.value)


@given(confidence_threshold=st.floats(max_value=-0.000001) | st.floats(min_value=1.000001))
def test_system1_reflex_mathematical_bounds(confidence_threshold: float) -> None:
    """Test 3: Prove System1Reflex decisively rejects values outside [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        System1Reflex(confidence_threshold=confidence_threshold, allowed_read_only_tools=["tool_a"])


def test_evaluator_optimizer_rejects_missing_nodes() -> None:
    nodes = {"did:web:node_a": SystemNode(description="A"), "did:web:node_b": SystemNode(description="B")}

    with pytest.raises(ValidationError, match="not found in topology nodes"):
        EvaluatorOptimizerTopology(
            nodes=nodes,  # type: ignore
            generator_node_id="did:web:node_a",
            evaluator_node_id="did:web:rogue_node_c",
            max_revision_loops=5,
        )


def test_evaluator_optimizer_rejects_self_evaluation() -> None:
    nodes = {"did:web:node_a": SystemNode(description="A")}

    with pytest.raises(ValidationError, match="Generator and Evaluator cannot be the same node"):
        EvaluatorOptimizerTopology(
            nodes=nodes,  # type: ignore
            generator_node_id="did:web:node_a",
            evaluator_node_id="did:web:node_a",
            max_revision_loops=5,
        )


def test_evaluator_optimizer_rejects_invalid_loops() -> None:
    nodes = {"did:web:node_a": SystemNode(description="A"), "did:web:node_b": SystemNode(description="B")}

    with pytest.raises(ValidationError, match="Input should be greater than or equal to 1"):
        EvaluatorOptimizerTopology(
            nodes=nodes,  # type: ignore
            generator_node_id="did:web:node_a",
            evaluator_node_id="did:web:node_b",
            max_revision_loops=0,
        )


@given(min_cosine_similarity=st.floats(max_value=-1.000001) | st.floats(min_value=1.000001))
def test_ontological_alignment_policy_mathematical_bounds(min_cosine_similarity: float) -> None:
    """Test: Prove OntologicalAlignmentPolicy decisively rejects values outside [-1.0, 1.0]."""
    with pytest.raises(ValidationError):
        OntologicalAlignmentPolicy(min_cosine_similarity=min_cosine_similarity, require_isometry_proof=True)


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


@given(max_monte_carlo_rollouts=st.integers(max_value=0))
def test_simulation_convergence_sla_rejects_zero_or_negative_rollouts(max_monte_carlo_rollouts: int) -> None:
    """Prove SimulationConvergenceSLA strictly rejects max_monte_carlo_rollouts equal to or less than 0."""
    with pytest.raises(ValidationError):
        SimulationConvergenceSLA(max_monte_carlo_rollouts=max_monte_carlo_rollouts, variance_tolerance=0.5)


@given(variance_tolerance=st.floats(max_value=-0.000001) | st.floats(min_value=1.000001))
def test_simulation_convergence_sla_rejects_out_of_bounds_variance_tolerance(variance_tolerance: float) -> None:
    """Prove SimulationConvergenceSLA strictly rejects a variance_tolerance outside the [0.0, 1.0] bound."""
    with pytest.raises(ValidationError):
        SimulationConvergenceSLA(max_monte_carlo_rollouts=100, variance_tolerance=variance_tolerance)


def test_digital_twin_topology_routes_through_discriminator() -> None:
    """Prove DigitalTwinTopology correctly routes through the AnyTopology discriminator."""
    payload = {
        "type": "digital_twin",
        "target_topology_id": "did:web:target_topology_123",
        "nodes": {"did:web:node_1": {"type": "system", "description": "Test node"}},
        "convergence_sla": {
            "max_monte_carlo_rollouts": 100,
            "variance_tolerance": 0.5,
        },
        "enforce_no_side_effects": True,
    }

    adapter: TypeAdapter[AnyTopology] = TypeAdapter(AnyTopology)
    topology = adapter.validate_python(payload)

    assert isinstance(topology, DigitalTwinTopology)
    assert topology.type == "digital_twin"
    assert topology.target_topology_id == "did:web:target_topology_123"
    assert topology.convergence_sla.max_monte_carlo_rollouts == 100
    assert topology.convergence_sla.variance_tolerance == 0.5
    assert topology.enforce_no_side_effects is True


def test_council_topology_byzantine_slash_requires_escrow() -> None:
    """Prove that CouncilTopology strictly requires a funded escrow when PBFT slashing is enabled."""
    nodes = {"did:web:node_1": SystemNode(description="The Oracle")}
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="slash_escrow",
    )
    consensus = ConsensusPolicy(strategy="pbft", quorum_rules=quorum)

    # 1. Unfunded - Must Fail
    with pytest.raises(
        ValidationError, match="Topological Interlock Failed: PBFT with slash_escrow requires a funded council_escrow"
    ):
        CouncilTopology(
            nodes=nodes,  # type: ignore
            adjudicator_id="did:web:node_1",
            consensus_policy=consensus,
        )

    # 2. Funded - Must Succeed
    escrow = EscrowPolicy(
        escrow_locked_microcents=5000, release_condition_metric="slash_on_fault", refund_target_node_id="did:web:node_1"
    )
    topology = CouncilTopology(
        nodes=nodes,  # type: ignore
        adjudicator_id="did:web:node_1",
        consensus_policy=consensus,
        council_escrow=escrow,
    )
    assert topology.council_escrow is not None
    assert topology.council_escrow.escrow_locked_microcents == 5000


@given(nodes=nodes_dict_st(), data=st.data())
def test_dag_topology_draft_superposition(nodes: dict[str, Any], data: DataObject) -> None:
    """Prove that 'draft' lifecycle_phase perfectly bypasses validation for incomplete or cyclical graphs."""
    ghost_node = "did:web:ghost_node_123"
    assume(ghost_node not in nodes)

    keys = list(nodes.keys())
    node_a = data.draw(st.sampled_from(keys))

    # Inject a dangling pointer AND a cycle, but declare it as a draft
    topology = DAGTopology(
        nodes=nodes, edges=[(node_a, ghost_node), (ghost_node, node_a)], allow_cycles=False, lifecycle_phase="draft"
    )

    assert topology.lifecycle_phase == "draft"
    assert len(topology.edges) == 2


def test_dynamical_systems_temporal_bounds() -> None:
    valid_gradients = ODEGradientBounds(max_drift_rate=1.0, decay_coefficient_min=0.1, decay_coefficient_max=0.5)

    # Test valid instantiation
    topology = DynamicalSystemsTopology(
        nodes={},
        continuous_time_gradients=valid_gradients,
        max_temporal_backpropagation_ms=5000,
        environmental_phase_shift_triggers=["0x1234567890abcdef1234567890abcdef12345678"]
    )
    assert topology.max_temporal_backpropagation_ms == 5000

    # Test causality escrow breach (> 1 hour)
    with pytest.raises(ValidationError):
        DynamicalSystemsTopology(
            nodes={},
            continuous_time_gradients=valid_gradients,
            max_temporal_backpropagation_ms=4000000,
            environmental_phase_shift_triggers=["did:example:123"]
        )

def test_dynamical_systems_cryptographic_triggers() -> None:
    valid_gradients = ODEGradientBounds(max_drift_rate=1.0, decay_coefficient_min=0.1, decay_coefficient_max=0.5)

    # Test invalid string hallucination
    with pytest.raises(ValidationError):
        DynamicalSystemsTopology(
            nodes={},
            continuous_time_gradients=valid_gradients,
            max_temporal_backpropagation_ms=5000,
            environmental_phase_shift_triggers=["wait_for_weather_api"]
        )

def test_ode_gradient_bounds() -> None:
    # Test mathematical inversion
    with pytest.raises(ValidationError):
        ODEGradientBounds(max_drift_rate=1.0, decay_coefficient_min=0.9, decay_coefficient_max=0.1)
