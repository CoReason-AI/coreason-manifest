import pytest

from coreason_manifest.core.common.exceptions import ManifestError
from coreason_manifest.workflow.flow import (
    CouncilTopology,
    DAGTopology,
    DCGTopology,
    Edge,
    EventDrivenTopology,
    HierarchicalTopology,
    MapReduceTopology,
    SwarmTopology,
)
from coreason_manifest.workflow.nodes.agent import AgentNode


def test_dag_topology() -> None:
    node1 = AgentNode(id="n1", profile="p1", operational_policy=None)
    node2 = AgentNode(id="n2", profile="p2", operational_policy=None)
    edges = [Edge(from_node="n1", to_node="n2")]

    dag = DAGTopology(nodes={"n1": node1, "n2": node2}, edges=edges, entry_point="n1")
    assert dag.topology_type == "dag"
    assert "n1" in dag.nodes


def test_dag_topology_cycle_detection() -> None:
    node1 = AgentNode(id="n1", profile="p1", operational_policy=None)
    node2 = AgentNode(id="n2", profile="p2", operational_policy=None)
    edges = [Edge(from_node="n1", to_node="n2"), Edge(from_node="n2", to_node="n1")]

    with pytest.raises(ManifestError) as excinfo:
        DAGTopology(nodes={"n1": node1, "n2": node2}, edges=edges, entry_point="n1")
    assert "Cycle detected" in str(excinfo.value)


def test_explicit_graph_topology_empty() -> None:
    with pytest.raises(ManifestError) as excinfo:
        DAGTopology(nodes={}, edges=[])
    assert "Graph must contain at least one node" in str(excinfo.value)


def test_explicit_graph_topology_id_mismatch() -> None:
    node1 = AgentNode(id="n1", profile="p1", operational_policy=None)
    with pytest.raises(ManifestError) as excinfo:
        DAGTopology(nodes={"wrong_key": node1}, edges=[])
    assert "Routing contradiction" in str(excinfo.value)


def test_explicit_graph_topology_collision() -> None:
    # We can't actually trigger dictionary key collision in Python dict easily for same key
    # But we can test entry point check:
    node1 = AgentNode(id="n1", profile="p1", operational_policy=None)
    with pytest.raises(ManifestError) as excinfo:
        DAGTopology(nodes={"n1": node1}, edges=[], entry_point="nonexistent")
    assert "not found in nodes" in str(excinfo.value)


def test_explicit_graph_topology_dangling_edge() -> None:
    node1 = AgentNode(id="n1", profile="p1", operational_policy=None)
    with pytest.raises(ManifestError) as excinfo:
        DAGTopology(nodes={"n1": node1}, edges=[Edge(from_node="n1", to_node="nonexistent")])
    assert "not found in graph nodes" in str(excinfo.value)

    with pytest.raises(ManifestError) as excinfo:
        DAGTopology(nodes={"n1": node1}, edges=[Edge(from_node="nonexistent", to_node="n1")])
    assert "not found in graph nodes" in str(excinfo.value)


def test_dcg_topology() -> None:
    node1 = AgentNode(id="n1", profile="p1", operational_policy=None)
    edges = [Edge(from_node="n1", to_node="n1")]
    dcg = DCGTopology(nodes={"n1": node1}, edges=edges, entry_point="n1")
    assert dcg.topology_type == "dcg"
    assert dcg.max_iterations == 10


def test_map_reduce_topology() -> None:
    node1 = AgentNode(id="mapper", profile="p1", operational_policy=None)
    node2 = AgentNode(id="reducer", profile="p2", operational_policy=None)
    mr = MapReduceTopology(
        nodes={"mapper": node1, "reducer": node2},
        iterator_variable="items",
        mapper_node_id="mapper",
        reducer_node_id="reducer",
    )
    assert mr.topology_type == "map_reduce"


def test_council_topology() -> None:
    node1 = AgentNode(id="prop1", profile="p1", operational_policy=None)
    node2 = AgentNode(id="agg", profile="p2", operational_policy=None)
    moa = CouncilTopology(
        nodes={"prop1": node1, "agg": node2}, layers=[["prop1"]], aggregator_agent="agg", diversity_maximization=True
    )
    assert moa.topology_type == "moa"


def test_swarm_topology() -> None:
    node1 = AgentNode(id="agent1", profile="p1", operational_policy=None)
    swarm = SwarmTopology(
        nodes={"agent1": node1}, entry_point="agent1", allowed_handoffs={"agent1": []}, swarm_type="mesh"
    )
    assert swarm.topology_type == "swarm"


def test_hierarchical_topology() -> None:
    node1 = AgentNode(id="sup", profile="p1", operational_policy=None)

    # Create a minimal valid WorkflowEnvelope to test HierarchicalTopology sub_flows
    from coreason_manifest.workflow.flow import FlowInterface, FlowMetadata, WorkflowEnvelope

    sub_flow = WorkflowEnvelope(
        metadata=FlowMetadata(name="SubFlow", version="1.0"),
        interface=FlowInterface(),
        topology=EventDrivenTopology(nodes={"agent1": node1}, trigger_schemas={"agent1": ["var1"]}),
    )

    hier = HierarchicalTopology(nodes={"sup": node1}, entry_point="sup", sub_flows={"sup": sub_flow})
    assert hier.topology_type == "hierarchical"


def test_event_driven_topology() -> None:
    node1 = AgentNode(id="agent1", profile="p1", operational_policy=None)
    ed = EventDrivenTopology(nodes={"agent1": node1}, trigger_schemas={"agent1": ["var1"]})
    assert ed.topology_type == "event_driven"
