import pytest
from coreason_manifest.spec.core.flow import FlowSpec, Graph, EdgeSpec, FlowMetadata, FlowInterface
from coreason_manifest.spec.core.contracts import ActionNode, SkillConfig
from coreason_manifest.utils.topology import validate_topology, TopologyValidationError

def create_flow(nodes_list, edges_list, entry_point=None):
    nodes = {n.id: n for n in nodes_list}
    graph = Graph(nodes=nodes, edges=edges_list, entry_point=entry_point)
    return FlowSpec(
        metadata=FlowMetadata(name="test", version="1.0.0"),
        graph=graph,
        interface=FlowInterface()
    )

def _create_node(id):
    return ActionNode(id=id, skill=SkillConfig(capabilities=[]))

def test_valid_topology():
    n1 = _create_node("n1")
    n2 = _create_node("n2")
    edges = [EdgeSpec(from_node="n1", to_node="n2")]
    flow = create_flow([n1, n2], edges, entry_point="n1")
    validate_topology(flow)

def test_invalid_edge_target():
    n1 = _create_node("n1")
    edges = [EdgeSpec(from_node="n1", to_node="n2")]
    flow = create_flow([n1], edges, entry_point="n1")
    with pytest.raises(TopologyValidationError) as exc:
        validate_topology(flow)
    assert "Edge target 'n2' does not exist" in str(exc.value)

def test_unreachable_node():
    n1 = _create_node("n1")
    n2 = _create_node("n2")
    edges = []
    flow = create_flow([n1, n2], edges, entry_point="n1")
    with pytest.raises(TopologyValidationError) as exc:
        validate_topology(flow)
    assert "Unreachable nodes detected" in str(exc.value)
    assert "n2" in str(exc.value)

def test_cycle_detection_unbounded():
    n1 = _create_node("n1")
    n2 = _create_node("n2")
    edges = [
        EdgeSpec(from_node="n1", to_node="n2"),
        EdgeSpec(from_node="n2", to_node="n1") # Back edge, no limit
    ]
    flow = create_flow([n1, n2], edges, entry_point="n1")
    with pytest.raises(TopologyValidationError) as exc:
        validate_topology(flow)
    assert "Unbounded infinite loop detected" in str(exc.value)

def test_cycle_detection_bounded():
    n1 = _create_node("n1")
    n2 = _create_node("n2")
    edges = [
        EdgeSpec(from_node="n1", to_node="n2"),
        EdgeSpec(from_node="n2", to_node="n1", max_iterations=10) # Back edge, bounded
    ]
    flow = create_flow([n1, n2], edges, entry_point="n1")
    # Should not raise
    validate_topology(flow)

def test_self_cycle_unbounded():
    n1 = _create_node("n1")
    edges = [EdgeSpec(from_node="n1", to_node="n1")]
    flow = create_flow([n1], edges, entry_point="n1")
    with pytest.raises(TopologyValidationError) as exc:
        validate_topology(flow)
    assert "Unbounded infinite loop detected" in str(exc.value)

def test_self_cycle_bounded():
    n1 = _create_node("n1")
    edges = [EdgeSpec(from_node="n1", to_node="n1", timeout=100)]
    flow = create_flow([n1], edges, entry_point="n1")
    validate_topology(flow)

def test_invalid_edge_source():
    n1 = _create_node("n1")
    edges = [EdgeSpec(from_node="n2", to_node="n1")]
    flow = create_flow([n1], edges, entry_point="n1")
    with pytest.raises(TopologyValidationError) as exc:
        validate_topology(flow)
    assert "Edge source 'n2' does not exist" in str(exc.value)
