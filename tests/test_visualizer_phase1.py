import sys

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
    Brain,
    HumanNode,
    Node,
    Placeholder,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.visualizer import _get_state_class, _render_node_def, to_mermaid


def test_visualizer() -> None:
    # Common Metadata
    metadata = FlowMetadata(
        name="Test Flow",
        version="0.1.0",
        description="A test flow",
        tags=["test"],
    )

    # Nodes
    agent_node = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        brain=Brain(role="Test Agent", persona="Tester", reasoning=None, reflex=None),
        tools=[],
    )

    switch_node = SwitchNode(
        id="switch-1",
        metadata={},
        supervision=None,
        type="switch",
        variable="var1",
        cases={"case1": "agent-1"},
        default="agent-2",
    )

    planner_node = PlannerNode(
        id="planner-1",
        metadata={},
        supervision=None,
        type="planner",
        goal="Plan stuff",
        optimizer=None,
        output_schema={},
    )

    human_node = HumanNode(
        id="human-1",
        metadata={},
        supervision=None,
        type="human",
        prompt="Approve?",
        timeout_seconds=60,
    )

    placeholder_node = Placeholder(
        id="placeholder-1",
        metadata={},
        supervision=None,
        type="placeholder",
        required_capabilities=[],
    )

    # 1. Test LinearFlow with None snapshot and multiple node types
    linear_flow = LinearFlow(
        kind="LinearFlow",
        metadata=metadata,
        sequence=[agent_node, planner_node, human_node, placeholder_node],
    )

    print("Testing LinearFlow with None snapshot...")
    mermaid_linear = to_mermaid(linear_flow, None)
    assert "graph TD" in mermaid_linear
    assert "agent_1" in mermaid_linear
    assert "planner_1" in mermaid_linear
    assert "human_1" in mermaid_linear
    assert "placeholder_1" in mermaid_linear
    # Check shapes
    assert "{{" in mermaid_linear  # Planner
    assert "[/" in mermaid_linear  # Human
    assert "(" in mermaid_linear  # Placeholder
    print("LinearFlow OK.")

    # 2. Test GraphFlow with Snapshot and Switch logic inference
    # Switch cases: case1 -> agent-1 (implicit label test)
    # Switch default: -> agent-2 (implicit label test)

    agent_2 = agent_node.model_copy(update={"id": "agent-2"})

    graph_flow = GraphFlow(
        kind="GraphFlow",
        metadata=metadata,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=Graph(
            nodes={
                "agent-1": agent_node,
                "switch-1": switch_node,
                "agent-2": agent_2,
                "planner-1": planner_node,  # skipped
            },
            edges=[
                Edge(source="agent-1", target="switch-1"),
                # Implicit label "case1"
                Edge(source="switch-1", target="agent-1"),
                # Implicit label "default" (default is agent-2)
                Edge(source="switch-1", target="agent-2"),
                # Explicit label
                Edge(source="agent-2", target="planner-1", condition="next"),
            ],
        ),
    )

    snapshot = ExecutionSnapshot(
        node_states={
            "agent-1": NodeState.COMPLETED,
            "switch-1": NodeState.RUNNING,
            "agent-2": NodeState.FAILED,
            "planner-1": NodeState.RETRYING,
        },
        active_path=["agent-1", "switch-1"],
    )

    print("Testing GraphFlow with Snapshot...")
    mermaid_graph = to_mermaid(graph_flow, snapshot)
    assert "graph LR" in mermaid_graph

    # Check implicit labels
    assert "|case1|" in mermaid_graph
    assert "|default|" in mermaid_graph
    assert "|next|" in mermaid_graph

    # Check styling classes
    assert ":::completed" in mermaid_graph
    assert ":::running" in mermaid_graph
    assert ":::failed" in mermaid_graph
    assert ":::retrying" in mermaid_graph
    assert "classDef retrying" in mermaid_graph
    assert "stroke-dasharray: 5 5" in mermaid_graph # Check pulse effect

    print("GraphFlow OK.")

    # 3. Check for legacy references
    with open("src/coreason_manifest/utils/visualizer.py") as f:
        content = f.read()
        assert "ManifestV2" not in content
        assert "RuntimeStateSnapshot" not in content
    print("Legacy check OK.")

    # 4. Test coverage for fallback cases
    # Test unknown state (PENDING -> None)
    assert _get_state_class(NodeState.PENDING) is None
    # Test RETRYING state
    assert _get_state_class(NodeState.RETRYING) == "retrying"

    # Test unknown node type
    class CustomNode(Node):
        type: str = "custom"

    custom_node = CustomNode(id="custom-1", metadata={}, supervision=None, type="custom")
    rendered = _render_node_def(custom_node, None)
    assert "(custom)" in rendered
    print("Coverage check OK.")


if __name__ == "__main__":
    try:
        test_visualizer()
        print("All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
