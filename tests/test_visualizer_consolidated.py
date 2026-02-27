# tests/test_visualizer_consolidated.py

from typing import cast
from coreason_manifest.spec.core.flow import (
    GraphFlow,
    FlowMetadata,
    FlowInterface,
    Graph,
    Edge,
    LinearFlow
)
from coreason_manifest.spec.core.nodes import (
    PlaceholderNode,
    SwitchNode,
    AgentNode,
    CognitiveProfile,
    HumanNode,
    SteeringConfig
)
from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState
from coreason_manifest.utils.visualizer import to_mermaid, to_react_flow

def test_visualizer_complex_graph_with_grouping_and_snapshot() -> None:
    """
    Test a complex graph flow with:
    - Grouped nodes (subgraphs)
    - Mixed node types (Agent, Switch, Human) to verify shapes
    - Cycle to verify layout handling
    - ExecutionSnapshot to verify state styling
    """

    # Define Nodes
    n_start = AgentNode(
        id="start",
        type="agent",
        profile="default",
        presentation=PresentationHints(label="Start Agent", group="GroupA")
    )
    n_switch = SwitchNode(
        id="router",
        type="switch",
        variable="var1",
        cases={"case1": "human_step"},
        default="end",
        presentation=PresentationHints(group="GroupA")
    )
    n_human = HumanNode(
        id="human_step",
        type="human",
        prompt="Review?",
        escalation="default",
        presentation=PresentationHints(group="GroupB"),
        steering_config=SteeringConfig(allow_variable_mutation=True)
    )
    n_end = PlaceholderNode(id="end", type="placeholder", required_capabilities=[])

    # Graph with cycle: human -> router
    graph = Graph(
        nodes={
            "start": n_start,
            "router": n_switch,
            "human_step": n_human,
            "end": n_end
        },
        edges=[
            Edge(from_node="start", to_node="router"),
            Edge(from_node="router", to_node="human_step", condition="case1"),
            Edge(from_node="router", to_node="end", condition=None), # default
            Edge(from_node="human_step", to_node="router", condition="retry") # Cycle
        ],
        entry_point="start"
    )

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="Complex Viz", version="1.0"),
        interface=FlowInterface(),
        graph=graph
    )

    # Create Snapshot
    snapshot = ExecutionSnapshot(
        request_id="req1",
        status="running",
        node_states={
            "start": NodeState.COMPLETED,
            "router": NodeState.COMPLETED,
            "human_step": NodeState.RUNNING
        },
        trace=[],
        blackboard={}
    )

    # 1. Verify Mermaid Generation
    mermaid = to_mermaid(flow, snapshot)

    # Assertions for Structure
    assert "graph LR" in mermaid
    assert "subgraph GroupA" in mermaid
    assert "subgraph GroupB" in mermaid
    assert "start --> router" in mermaid
    assert "human_step -->|retry| router" in mermaid # Cycle edge

    # Assertions for Shapes & Labels
    assert 'start["Start Agent"]' in mermaid # Label override
    assert 'router{"router"}' in mermaid # Switch shape
    assert 'human_step[/"human_step<br/>(Human)"/]' in mermaid # Human shape + fallback label logic

    # Assertions for State Classes
    assert "classDef completed" in mermaid
    # The visualizer joins classes with ::: but checks node type first then state.
    # We need to be careful with order or just check existence.
    # The code: definition += ":::" + ":::".join(classes)
    # classes = [node.type] + [state.lower()]
    assert "start:::agent:::completed" in mermaid
    assert "human_step:::human:::running" in mermaid

    # 2. Verify React Flow Generation (Layout & Data)
    rf = to_react_flow(flow, snapshot)

    # Basic Checks
    assert len(rf["nodes"]) == 4
    assert len(rf["edges"]) == 4

    # Check Layout Rank Logic (Start should be rank 0, Router rank 1, etc.)
    # Since we have a cycle, exact positions depend on heuristics, but checking x/y exist is key
    start_node = next(n for n in rf["nodes"] if n["id"] == "start")
    assert start_node["position"]["x"] == 0 # Root

    # Check Data Injection
    human_rf_node = next(n for n in rf["nodes"] if n["id"] == "human_step")
    # NodeState enum might be serialized as string or enum member. The code converts via .value usually?
    # Actually code says: node_data["state"] = snapshot.node_states[node.id] which is the Enum member.
    # So assertions should match the Enum or its value.
    assert human_rf_node["data"]["state"] == NodeState.RUNNING
    assert human_rf_node["data"]["presentation"]["group"] == "GroupB"


def test_visualizer_linear_flow() -> None:
    """Test LinearFlow visualization logic (graph TD)."""
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="Linear", version="1.0"),
        steps=[
            PlaceholderNode(id="step1", type="placeholder", required_capabilities=[]),
            PlaceholderNode(id="step2", type="placeholder", required_capabilities=[])
        ]
    )

    mermaid = to_mermaid(flow)
    assert "graph TD" in mermaid
    assert "step1 --> step2" in mermaid

    rf = to_react_flow(flow)
    assert len(rf["nodes"]) == 2
    assert len(rf["edges"]) == 1
    assert rf["edges"][0]["source"] == "step1"
    assert rf["edges"][0]["target"] == "step2"

def test_visualizer_pure_cycle_fallback() -> None:
    """Test layout computation fallback for pure cycles (no root)."""
    # Cycle A <-> B
    n_a = PlaceholderNode(id="A", type="placeholder", required_capabilities=[])
    n_b = PlaceholderNode(id="B", type="placeholder", required_capabilities=[])

    graph = Graph(
        nodes={"A": n_a, "B": n_b},
        edges=[
            Edge(from_node="A", to_node="B"),
            Edge(from_node="B", to_node="A")
        ],
        entry_point="A"
    )

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="Cycle", version="1.0"),
        interface=FlowInterface(),
        graph=graph
    )

    rf = to_react_flow(flow)
    # Just verify it didn't crash and produced positions
    assert len(rf["nodes"]) == 2
    pos_a = rf["nodes"][0]["position"]
    assert "x" in pos_a and "y" in pos_a
