import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.workflow.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.workflow.nodes.system import PlaceholderNode


def create_mock_agent_node(node_id: str) -> PlaceholderNode:
    return PlaceholderNode(id=node_id, required_capabilities=["dummy_cap"])


def test_edge_is_feedback_retained() -> None:
    """Test 4: Visualization Metadata"""
    edge = Edge(from_node="A", to_node="B", is_feedback=True)
    assert edge.is_feedback is True

    edge_default = Edge(from_node="A", to_node="B")
    assert edge_default.is_feedback is False


def test_default_dag_enforced() -> None:
    """Test 1: Default DAG Enforced"""
    node_a = create_mock_agent_node("A")
    node_b = create_mock_agent_node("B")

    # Creating a cycle: A -> B -> A
    edges = [
        Edge(from_node="A", to_node="B"),
        Edge(from_node="B", to_node="A", is_feedback=True),
    ]

    with pytest.raises(ManifestError) as exc_info:
        Graph(nodes={"A": node_a, "B": node_b}, edges=edges, allow_cycles=False)

    assert exc_info.value.fault.error_code == ManifestErrorCode.VAL_TOPOLOGY_CYCLE


def test_unsafe_dcg_blocked() -> None:
    """Test 2: Unsafe DCG Blocked"""
    node_a = create_mock_agent_node("A")
    node_b = create_mock_agent_node("B")

    # Cycle allowed at graph level
    graph = Graph(
        nodes={"A": node_a, "B": node_b},
        edges=[
            Edge(from_node="A", to_node="B"),
            Edge(from_node="B", to_node="A", is_feedback=True),
        ],
        allow_cycles=True,
    )

    metadata = FlowMetadata(name="Test Flow", version="1.0.0")

    # Missing max_iterations
    with pytest.raises(ValidationError) as exc_info:
        GraphFlow(metadata=metadata, interface=FlowInterface(), graph=graph)

    assert "A GraphFlow with 'allow_cycles=True' must define a valid 'max_iterations' circuit breaker." in str(
        exc_info.value
    )

    # max_iterations = 0
    with pytest.raises(ValidationError) as exc_info_zero:
        GraphFlow(metadata=metadata, interface=FlowInterface(), graph=graph, max_iterations=0)

    assert "A GraphFlow with 'allow_cycles=True' must define a valid 'max_iterations' circuit breaker." in str(
        exc_info_zero.value
    )


def test_bounded_dcg_allowed() -> None:
    """Test 3: Bounded DCG Allowed"""
    node_a = create_mock_agent_node("A")
    node_b = create_mock_agent_node("B")

    graph = Graph(
        nodes={"A": node_a, "B": node_b},
        edges=[
            Edge(from_node="A", to_node="B"),
            Edge(from_node="B", to_node="A", is_feedback=True),
        ],
        allow_cycles=True,
    )

    metadata = FlowMetadata(name="Test Flow", version="1.0.0")

    flow = GraphFlow(
        metadata=metadata,
        interface=FlowInterface(),
        graph=graph,
        max_iterations=5,
    )

    assert flow.max_iterations == 5
    assert flow.graph.allow_cycles is True
