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
    EmergenceInspectorNode,
    InspectorNode,
    Node,
    PlaceholderNode,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.visualizer import to_mermaid


def _get_metadata() -> FlowMetadata:
    return FlowMetadata(
        name="Test Flow",
        version="1.0.0",
        description="A test flow",
        tags=["test"],
    )


def test_visualizer_state_application() -> None:
    node = AgentNode(
        id="agent-1",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        type="agent",
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=_get_metadata(),
        steps=[node],
    )

    # Snapshot with state
    snapshot = ExecutionSnapshot(node_states={"agent-1": NodeState.FAILED}, active_path=["agent-1"])

    mermaid = to_mermaid(flow, snapshot)
    # New format: id[...]:::agent:::failed
    assert "agent_1" in mermaid
    assert ":::failed" in mermaid
    assert ":::agent" in mermaid

    # Snapshot without state for node
    snapshot_empty = ExecutionSnapshot(node_states={}, active_path=[])
    mermaid_empty = to_mermaid(flow, snapshot_empty)
    assert ":::failed" not in mermaid_empty


def test_visualizer_node_types_coverage() -> None:
    nodes: list[Node] = []

    # Planner
    planner = PlannerNode(id="plan", metadata={}, goal="g", optimizer=None, output_json_schema={}, type="planner")
    nodes.append(planner)

    # Inspector
    inspector = InspectorNode(
        id="inspect",
        metadata={},
        target_variable="t",
        criteria="c",
        pass_threshold=0.5,
        output_variable="o",
        optimizer=None,
        type="inspector",
    )
    nodes.append(inspector)

    # EmergenceInspectorNode
    emergence = EmergenceInspectorNode(
        id="emerge",
        metadata={},
        target_variable="t",
        criteria="c",
        output_variable="o",
        judge_model="gpt-4",
        optimizer=None,
        type="emergence_inspector",
    )
    nodes.append(emergence)

    # PlaceholderNode
    placeholder = PlaceholderNode(id="place", metadata={}, required_capabilities=[], type="placeholder")
    nodes.append(placeholder)

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=_get_metadata(),
        steps=nodes,  # type: ignore[arg-type]
    )

    mermaid = to_mermaid(flow)

    assert "plan" in mermaid
    assert "{{" in mermaid

    assert "inspect" in mermaid

    assert "place" in mermaid
    assert "(" in mermaid


def test_switch_edge_inference() -> None:
    # Setup graph with switch
    switch_node = SwitchNode(
        id="switch-1",
        metadata={},
        variable="var",
        cases={"case1": "target-1"},
        default="target-2",
        type="switch",
    )

    target_node_1 = AgentNode(
        id="target-1",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        type="agent",
    )

    target_node_2 = AgentNode(
        id="target-2",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        type="agent",
    )

    nodes: dict[str, Node] = {
        "switch-1": switch_node,
        "target-1": target_node_1,
        "target-2": target_node_2,
    }

    edges = [
        Edge(from_node="switch-1", to_node="target-1"),
        Edge(from_node="switch-1", to_node="target-2"),
    ]

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=_get_metadata(),
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=Graph(nodes=nodes, edges=edges, entry_point="switch-1"),  # type: ignore[arg-type]
    )

    mermaid = to_mermaid(flow)

    # Assertions
    assert "switch_1 -->|case1| target_1" in mermaid
    assert "switch_1 -->|default| target_2" in mermaid
