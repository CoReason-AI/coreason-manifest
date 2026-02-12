from typing import Any

from coreason_manifest.spec.core.flow import (
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
from coreason_manifest.utils.visualizer import _render_node_def, to_mermaid


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
    assert 'start["start<br/>(Agent)"]' in mermaid_code
    assert 'review[/"review<br/>(Human)"/]' in mermaid_code
    assert 'plan{{"plan<br/>(Planner)"}}' in mermaid_code
    assert 'end("end<br/>(PlaceholderNode)")' in mermaid_code

    assert "start --> review" in mermaid_code
    assert "review --> plan" in mermaid_code
    assert "plan --> end" in mermaid_code

    # Check styling
    assert "classDef human" in mermaid_code
    assert "class review human;" in mermaid_code


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
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
    )

    mermaid_code = to_mermaid(flow)

    print(mermaid_code)

    assert "graph LR" in mermaid_code
    assert 'decision{"decision<br/>(Switch)"}' in mermaid_code

    # Check edges
    assert "start --> decision" in mermaid_code
    # Check switch logic labels
    assert "decision -->|success| end" in mermaid_code
    assert "decision -->|retry| start" in mermaid_code

    # Check styling
    assert "classDef switch" in mermaid_code
    assert "class decision switch;" in mermaid_code


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
        interface=FlowInterface(inputs={}, outputs={}),
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
        interface=FlowInterface(inputs={}, outputs={}),
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

    # Expected IDs after sanitization:
    # "agent 1" -> "agent_1"
    # 'agent"2"' -> 'agent"2"' (only spaces and hyphens are replaced per spec, alphanumeric check might still fail?)
    # Wait, the spec was: replace "-" and " " with "_".
    # What about quotes? "agent"2"" -> "agent"2""
    # If the ID is 'agent"2"', replace does nothing.
    # The output format for definition: ID["Original ID<br/>..."]

    # agent 1 -> agent_1["agent 1<br/>..."]
    assert 'agent_1["agent 1<br/>(Agent)"]' in mermaid_code

    # agent"2" -> agent"2"["agent&quot;2&quot;<br/>..."] ?
    # If "agent"2"" is the ID, it's not alphanumeric.
    # But we are using the new logic: replace spaces and hyphens.
    # So "agent"2"" remains "agent"2"".
    # Mermaid might not like quotes in the ID part.
    # However, I must follow the prompt instructions which said:
    # "Sanitizes strings to be valid Mermaid IDs (alphanumeric only).
    # ... return id_str.replace("-", "_").replace(" ", "_")"
    # It says "alphanumeric only" but the code example only replaces spaces and hyphens.
    # I will stick to the code example provided in the feedback.

    # For 'agent"2"', label escaping happens: &quot;
    assert 'agent"2"["agent&quot;2&quot;<br/>(Agent)"]' in mermaid_code

    # agent-3 -> agent_3
    assert 'agent_3["agent-3<br/>(Agent)"]' in mermaid_code

    # Check implicit edges
    # agent 1 -> agent"2" => agent_1 --> agent"2"
    # agent"2" -> agent-3 => agent"2" --> agent_3

    assert 'agent_1 --> agent"2"' in mermaid_code
    assert 'agent"2" --> agent_3' in mermaid_code


def test_unknown_node_type() -> None:
    class CustomNode(Node):
        type: str = "custom"

    node = CustomNode(id="custom1", metadata={}, supervision=None, type="custom")

    result = _render_node_def(node)
    assert 'custom1["custom1<br/>(custom)"]' in result


if __name__ == "__main__":
    test_linear_flow_to_mermaid()
    test_graph_flow_to_mermaid()
    test_switch_default_path()
    test_explicit_edge_labels()
    test_special_characters_escaping()
    test_unknown_node_type()
