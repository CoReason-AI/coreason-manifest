from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.core.flow import (
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, PlaceholderNode, SwitchNode
from coreason_manifest.spec.core.resilience import EscalationStrategy
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.visualizer import to_mermaid, to_react_flow


def test_visualizer_linear_mermaid() -> None:
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[])
    flow = LinearFlow.model_construct(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description=""),
        definitions=None,
        steps=[node],
    )
    diagram = to_mermaid(flow)
    assert "graph TD" in diagram
    assert "a1" in diagram


def test_visualizer_graph_mermaid() -> None:
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[])
    graph = Graph(nodes={"a1": node}, edges=[], entry_point="a1")
    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description=""),
        interface=FlowInterface(),
        definitions=None,
        graph=graph,
    )
    diagram = to_mermaid(flow)
    assert "graph LR" in diagram
    assert "a1" in diagram


def test_visualizer_switch_node_labels() -> None:
    switch = SwitchNode(
        id="s1", metadata={}, type="switch", variable="x", cases={"true": "a1", "false": "a2"}, default="a3"
    )
    a1 = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[])
    a2 = AgentNode(id="a2", metadata={}, type="agent", profile="p", tools=[])
    a3 = AgentNode(id="a3", metadata={}, type="agent", profile="p", tools=[])

    graph = Graph(
        nodes={"s1": switch, "a1": a1, "a2": a2, "a3": a3},
        edges=[
            Edge(from_node="s1", to_node="a1"),
            Edge(from_node="s1", to_node="a2"),
            Edge(from_node="s1", to_node="a3"),
        ],
        entry_point="s1",
    )
    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description=""),
        interface=FlowInterface(),
        definitions=None,
        graph=graph,
    )

    diagram = to_mermaid(flow)
    assert "|true|" in diagram
    assert "|false|" in diagram
    assert "|default|" in diagram


def test_visualizer_react_flow() -> None:
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[])
    graph = Graph(nodes={"a1": node}, edges=[], entry_point="a1")
    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description=""),
        interface=FlowInterface(),
        definitions=None,
        graph=graph,
    )

    rf = to_react_flow(flow)
    assert len(rf["nodes"]) == 1
    assert rf["nodes"][0]["id"] == "a1"


def test_visualizer_human_options() -> None:
    human = HumanNode(
        id="h1",
        type="human",
        prompt="p",
        options=["yes", "no"],
        escalation=EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10),
    )
    flow = LinearFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0.0", description=""), steps=[human]
    )
    diagram = to_mermaid(flow)
    assert "[yes, no]" in diagram


def test_visualizer_groups() -> None:
    n1 = PlaceholderNode(
        id="n1",
        type="placeholder",
        required_capabilities=[],
        presentation=PresentationHints(group="g1", label="Node 1"),
    )
    n2 = PlaceholderNode(
        id="n2",
        type="placeholder",
        required_capabilities=[],
        presentation=PresentationHints(group="g1", label="Node 2"),
    )
    n3 = PlaceholderNode(
        id="n3", type="placeholder", required_capabilities=[], presentation=PresentationHints(group="g2")
    )

    flow = LinearFlow.model_construct(
        kind="LinearFlow", metadata=FlowMetadata(name="test", version="1.0.0", description=""), steps=[n1, n2, n3]
    )
    diagram = to_mermaid(flow)
    assert "subgraph g1" in diagram
    assert "subgraph g2" in diagram
    assert "Node 1" in diagram


def test_visualizer_layout_fallback() -> None:
    # Disconnected components to test layout engine fallback
    # And cycle to test unvisited nodes handling
    n1 = PlaceholderNode(id="n1", type="placeholder", required_capabilities=[])
    n2 = PlaceholderNode(id="n2", type="placeholder", required_capabilities=[])
    n3 = PlaceholderNode(id="n3", type="placeholder", required_capabilities=[])

    # n1 -> n2 -> n1 (cycle, no root)
    # n3 (disconnected)
    graph = Graph(
        nodes={"n1": n1, "n2": n2, "n3": n3},
        edges=[Edge(from_node="n1", to_node="n2"), Edge(from_node="n2", to_node="n1")],
        entry_point="n1",
    )
    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description=""),
        interface=FlowInterface(),
        graph=graph,
    )
    rf = to_react_flow(flow)
    assert len(rf["nodes"]) == 3


def test_visualizer_snapshot() -> None:
    # Test snapshot state injection
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[])
    flow = LinearFlow.model_construct(
        kind="LinearFlow", metadata=FlowMetadata(name="test", version="1.0.0", description=""), steps=[node]
    )

    # Mock snapshot with valid enum value (uppercase)
    # ExecutionSnapshot only has node_states and active_path
    snap = ExecutionSnapshot(node_states={"a1": NodeState.COMPLETED}, active_path=["a1"])

    diagram = to_mermaid(flow, snapshot=snap)
    assert ":::completed" in diagram

    rf = to_react_flow(flow, snapshot=snap)
    assert rf["nodes"][0]["data"]["state"] == "COMPLETED"


def test_visualizer_react_flow_conditional() -> None:
    n1 = PlaceholderNode(id="n1", type="placeholder", required_capabilities=[])
    n2 = PlaceholderNode(id="n2", type="placeholder", required_capabilities=[])

    graph = Graph(
        nodes={"n1": n1, "n2": n2}, edges=[Edge(from_node="n1", to_node="n2", condition="x>1")], entry_point="n1"
    )
    flow = GraphFlow.model_construct(kind="GraphFlow", metadata=FlowMetadata(name="t", version="1"), graph=graph)

    rf = to_react_flow(flow)
    assert rf["edges"][0]["label"] == "x>1"


def test_visualizer_layout_unreachable_cycle() -> None:
    # Root R
    r = PlaceholderNode(id="R", type="placeholder", required_capabilities=[])
    # Cycle A <-> B (disconnected from R)
    a = PlaceholderNode(id="A", type="placeholder", required_capabilities=[])
    b = PlaceholderNode(id="B", type="placeholder", required_capabilities=[])

    graph = Graph(
        nodes={"R": r, "A": a, "B": b},
        edges=[Edge(from_node="A", to_node="B"), Edge(from_node="B", to_node="A")],
        entry_point="R",
    )

    flow = GraphFlow.model_construct(kind="GraphFlow", metadata=FlowMetadata(name="t", version="1"), graph=graph)

    rf = to_react_flow(flow)

    r_pos = next(n["position"]["x"] for n in rf["nodes"] if n["id"] == "R")
    a_pos = next(n["position"]["x"] for n in rf["nodes"] if n["id"] == "A")
    b_pos = next(n["position"]["x"] for n in rf["nodes"] if n["id"] == "B")

    assert r_pos == 0
    # They should be pushed to a higher rank
    assert a_pos >= 300
    assert b_pos >= 300


def test_visualizer_unknown_flow_type(monkeypatch) -> None:
    class DummyFlow:
        pass

    # Mock get_unified_topology to return empty list/tuple
    monkeypatch.setattr("coreason_manifest.utils.visualizer.get_unified_topology", lambda x: ([], []))

    # ignore type checker
    res = to_mermaid(DummyFlow())  # type: ignore
    assert res == ""
