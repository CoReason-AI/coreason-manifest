from coreason_manifest.builder import NewGraphFlow, NewLinearFlow
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    HumanNode,
    InspectorNode,
    Node,
    PlaceholderNode,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.visualizer import _get_state_class, _render_node_def, to_mermaid


def test_get_state_class_coverage() -> None:
    assert _get_state_class(NodeState.RUNNING) == "running"
    assert _get_state_class(NodeState.RETRYING) == "retrying"
    assert _get_state_class(NodeState.FAILED) == "failed"
    assert _get_state_class(NodeState.CANCELLED) == "failed"
    assert _get_state_class(NodeState.COMPLETED) == "completed"
    assert _get_state_class(NodeState.SKIPPED) == "skipped"
    assert _get_state_class(NodeState.PENDING) is None


def test_switch_edge_inference() -> None:
    # Setup graph with switch
    flow_builder = NewGraphFlow(name="switch-test", version="1.0")

    switch_node = SwitchNode(
        id="switch-1",
        metadata={},
        supervision=None,
        variable="var",
        cases={"case1": "target-1"},
        default="target-2",
        type="switch",
    )

    target_node_1 = AgentNode(
        id="target-1",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        type="agent",
    )

    target_node_2 = AgentNode(
        id="target-2",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        type="agent",
    )

    flow_builder.add_node(switch_node)
    flow_builder.add_node(target_node_1)
    flow_builder.add_node(target_node_2)

    # Connect implicitly via switch logic logic requires edges to be defined in graph
    flow_builder.connect("switch-1", "target-1")
    flow_builder.connect("switch-1", "target-2")

    flow = flow_builder.build()
    mermaid = to_mermaid(flow)

    # Assertions
    assert "switch_1 -->|case1| target_1" in mermaid
    assert "switch_1 -->|default| target_2" in mermaid


def test_visualizer_snapshot_state_application() -> None:
    node = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        type="agent",
    )

    # Snapshot with state
    snapshot = ExecutionSnapshot(node_states={"agent-1": NodeState.FAILED}, active_path=["agent-1"])

    render = _render_node_def(node, snapshot)
    assert ":::failed" in render

    # Snapshot without state for node
    snapshot_empty = ExecutionSnapshot(node_states={}, active_path=[])
    render_empty = _render_node_def(node, snapshot_empty)
    assert ":::failed" not in render_empty


def test_visualizer_linear_flow_styling_ids() -> None:
    # This targets the loop at the end of to_mermaid for linear flows
    flow_builder = NewLinearFlow(name="linear-test")

    human_node = HumanNode(id="human-lin", metadata={}, supervision=None, prompt="p", timeout_seconds=1, type="human")

    switch_node = SwitchNode(
        id="switch-lin", metadata={}, supervision=None, variable="var", cases={}, default="human-lin", type="switch"
    )

    flow_builder.add_step(switch_node)
    flow_builder.add_step(human_node)

    flow = flow_builder.build()
    mermaid = to_mermaid(flow)

    assert "class switch_lin switch;" in mermaid
    assert "class human_lin human;" in mermaid


def test_visualizer_node_types_coverage() -> None:
    # Planner
    planner = PlannerNode(
        id="plan", metadata={}, supervision=None, goal="g", optimizer=None, output_schema={}, type="planner"
    )
    render_planner = _render_node_def(planner)
    assert "(Planner)" in render_planner
    assert "{{" in render_planner

    # Inspector
    inspector = InspectorNode(
        id="inspect",
        metadata={},
        supervision=None,
        target_variable="t",
        criteria="c",
        pass_threshold=0.5,
        output_variable="o",
        optimizer=None,
        type="inspector",
    )
    render_inspector = _render_node_def(inspector)
    assert "(Inspector)" in render_inspector
    assert ":::inspector" in render_inspector

    # PlaceholderNode
    placeholder = PlaceholderNode(id="place", metadata={}, supervision=None, required_capabilities=[], type="placeholder")
    render_place = _render_node_def(placeholder)
    assert "(PlaceholderNode)" in render_place
    assert "(" in render_place

    # Unknown/Fallback
    class CustomNode(Node):
        type: str = "custom"

    custom = CustomNode(id="cust", metadata={}, supervision=None, type="custom")
    render_custom = _render_node_def(custom)
    assert "(custom)" in render_custom
    assert "[" in render_custom
