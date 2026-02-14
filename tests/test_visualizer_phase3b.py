from typing import Any

from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    HumanNode,
    Node,
    PlaceholderNode,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.visualizer import to_mermaid, to_react_flow


def _get_metadata() -> FlowMetadata:
    return FlowMetadata(
        name="Test Flow",
        version="1.0.0",
        description="A test flow",
        tags=["test"],
    )


def _get_agent_node(node_id: str) -> AgentNode:
    return AgentNode(
        id=node_id,
        metadata={},
        supervision=None,
        profile=CognitiveProfile(
            role="assistant",
            persona="helpful",
            reasoning=None,
            fast_path=None,
        ),
        tools=[],
    )


def _get_switch_node(node_id: str, cases: dict[str, str], default: str) -> SwitchNode:
    return SwitchNode(
        id=node_id,
        metadata={},
        supervision=None,
        variable="status",
        cases=cases,
        default=default,
    )


def _get_human_node(node_id: str) -> HumanNode:
    return HumanNode(
        id=node_id,
        metadata={},
        supervision=None,
        prompt="Please approve",
        timeout_seconds=3600,
    )


def _get_planner_node(node_id: str) -> PlannerNode:
    return PlannerNode(
        id=node_id,
        metadata={},
        supervision=None,
        goal="Solve problems",
        optimizer=None,
        output_schema={"type": "object"},
    )


def _get_placeholder_node(node_id: str) -> PlaceholderNode:
    return PlaceholderNode(
        id=node_id,
        metadata={},
        supervision=None,
        required_capabilities=["coding"],
    )


def test_linear_flow_to_mermaid() -> None:
    nodes: list[Any] = [
        _get_agent_node("start"),
        _get_human_node("review"),
        _get_planner_node("plan"),
        _get_placeholder_node("end"),
    ]

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=_get_metadata(),
        sequence=nodes,
    )

    mermaid_code = to_mermaid(flow)

    print(mermaid_code)

    assert "graph TD" in mermaid_code
    # Updated output check for start node
    assert "start" in mermaid_code

    # Edges
    assert "start --> review" in mermaid_code
    assert "review --> plan" in mermaid_code
    assert "plan --> end" in mermaid_code

    # Styling
    assert ":::human" in mermaid_code


def test_graph_flow_to_mermaid() -> None:
    nodes: dict[str, Any] = {
        "start": _get_agent_node("start"),
        "decision": _get_switch_node("decision", cases={"success": "end", "retry": "start"}, default="end"),
        "end": _get_placeholder_node("end"),
    }

    edges = [
        Edge(source="start", target="decision"),
        Edge(source="decision", target="end"),  # Case: success (implicit via switch logic)
        Edge(source="decision", target="start"),  # Case: retry (implicit via switch logic)
    ]

    graph = Graph(nodes=nodes, edges=edges)

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    mermaid_code = to_mermaid(flow)

    print(mermaid_code)

    assert "graph LR" in mermaid_code

    # Check edges
    assert "start --> decision" in mermaid_code
    # Check switch logic labels
    assert "decision -->|success| end" in mermaid_code
    assert "decision -->|retry| start" in mermaid_code

    # Check styling
    assert ":::switch" in mermaid_code


def test_switch_default_path() -> None:
    nodes: dict[str, Any] = {
        "decision": _get_switch_node("decision", cases={"success": "end"}, default="fallback"),
        "end": _get_placeholder_node("end"),
        "fallback": _get_placeholder_node("fallback"),
    }

    edges = [
        Edge(source="decision", target="end"),  # Case: success
        Edge(source="decision", target="fallback"),  # Case: default
    ]

    graph = Graph(nodes=nodes, edges=edges)
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    mermaid_code = to_mermaid(flow)
    assert "decision -->|success| end" in mermaid_code
    assert "decision -->|default| fallback" in mermaid_code


def test_explicit_edge_labels() -> None:
    nodes: dict[str, Any] = {
        "A": _get_agent_node("A"),
        "B": _get_agent_node("B"),
    }
    edges = [
        Edge(source="A", target="B", condition="explicit_cond"),
    ]
    graph = Graph(nodes=nodes, edges=edges)
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    mermaid_code = to_mermaid(flow)
    assert "A -->|explicit_cond| B" in mermaid_code


def test_special_characters_escaping() -> None:
    nodes: list[Any] = [
        _get_agent_node("agent 1"),  # Space in ID
        _get_agent_node('agent"2"'),  # Quote in ID
        _get_agent_node("agent-3"),  # Hyphen in ID
    ]

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=_get_metadata(),
        sequence=nodes,
    )

    mermaid_code = to_mermaid(flow)

    # agent 1 -> agent_1
    assert "agent_1" in mermaid_code

    # agent"2" -> escaped label
    assert "&quot;" in mermaid_code

    # agent-3 -> agent_3
    assert "agent_3" in mermaid_code

    assert 'agent_1 --> agent"2"' in mermaid_code
    assert 'agent"2" --> agent_3' in mermaid_code


def test_react_flow_output() -> None:
    # Explicitly type as dict[str, AnyNode] or Node if compatible, but Node is safer for generic visualizer tests
    nodes: dict[str, Node] = {
        "start": _get_agent_node("start"),
        "end": _get_placeholder_node("end"),
    }
    edges: list[Edge] = [
        Edge(source="start", target="end"),
    ]
    # The Graph model expects AnyNode which is a union of specific node types.
    # Casting to Any or explicitly using the union might be needed if MyPy complains about covariance.
    # For now, let's try casting the dict values to Any to bypass strict invariance check on the Union type
    graph = Graph(nodes=nodes, edges=edges)  # type: ignore[arg-type]
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    rf = to_react_flow(flow)
    assert "nodes" in rf
    assert "edges" in rf
    assert len(rf["nodes"]) == 2
    assert len(rf["edges"]) == 1

    # Check node structure
    start_node = next(n for n in rf["nodes"] if n["id"] == "start")
    assert start_node["type"] == "agent"
    assert "position" in start_node
    assert "data" in start_node
    assert start_node["data"]["label"] == "start"

    # Check layout (basic check for DAG layout)
    end_node = next(n for n in rf["nodes"] if n["id"] == "end")
    start_pos = start_node["position"]
    end_pos = end_node["position"]

    # Start should be at rank 0 (x=0), End at rank 1 (x=300)
    assert start_pos["x"] == 0
    assert end_pos["x"] > 0
    assert start_pos["x"] != end_pos["x"]


def test_react_flow_linear() -> None:
    nodes: list[Node] = [
        _get_agent_node("start"),
        _get_placeholder_node("end"),
    ]
    # LinearFlow sequence expects AnyNode.
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=_get_metadata(),
        sequence=nodes,  # type: ignore[arg-type]
    )

    rf = to_react_flow(flow)
    assert len(rf["nodes"]) == 2
    assert len(rf["edges"]) == 1
    assert rf["edges"][0]["source"] == "start"
    assert rf["edges"][0]["target"] == "end"


def test_visualizer_coverage_extras() -> None:
    # Coverage for presentation, snapshot, edge labels in to_react_flow

    # 1. Setup Node with Presentation
    agent = _get_agent_node("agent-cov")
    agent = agent.model_copy(update={"presentation": PresentationHints(label="Custom Label", icon="icon")})

    # 2. Setup Flow
    nodes = {"agent-cov": agent, "end": _get_placeholder_node("end")}
    edges = [Edge(source="agent-cov", target="end", condition="go")]

    graph = Graph(nodes=nodes, edges=edges)  # type: ignore[arg-type]
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    # 3. Snapshot
    snapshot = ExecutionSnapshot(node_states={"agent-cov": NodeState.COMPLETED}, active_path=["agent-cov"])

    # 4. Call to_mermaid (cover _get_node_label with presentation)
    mermaid = to_mermaid(flow, snapshot)
    assert "Custom Label" in mermaid

    # 5. Call to_react_flow
    rf = to_react_flow(flow, snapshot)

    agent_rf = next(n for n in rf["nodes"] if n["id"] == "agent-cov")
    assert agent_rf["data"]["presentation"]["label"] == "Custom Label"
    assert agent_rf["data"]["label"] == "Custom Label"
    assert agent_rf["data"]["state"] == "COMPLETED"

    edge_rf = rf["edges"][0]
    assert edge_rf["label"] == "go"


def test_visualizer_grouping() -> None:
    # Coverage for subgraph grouping

    agent = _get_agent_node("agent-group")
    agent = agent.model_copy(update={"presentation": PresentationHints(group="My Group")})

    other = _get_agent_node("other")  # No group

    nodes = {"agent-group": agent, "other": other}
    edges: list[Edge] = []

    graph = Graph(nodes=nodes, edges=edges)  # type: ignore[arg-type]
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    mermaid = to_mermaid(flow)
    assert "subgraph My_Group" in mermaid
    assert "My Group" in mermaid
    assert "agent-group" in mermaid
