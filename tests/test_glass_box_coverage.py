from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.core.flow import (
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    HumanNode,
    PlannerNode,
    SwarmNode,
)
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.diff import ChangeType, ManifestDiff, _deep_diff
from coreason_manifest.utils.mock import MockFactory
from coreason_manifest.utils.visualizer import to_react_flow


def _get_base_metadata() -> FlowMetadata:
    return FlowMetadata(name="CovTest", version="1.0", description="T", tags=[])


def test_deep_diff_helpers() -> None:
    # Test _deep_diff logic coverage
    # Dict added key
    diffs = _deep_diff("root", {"a": 1}, {"a": 1, "b": 2}, ChangeType.COSMETIC, None)
    assert len(diffs) == 1
    assert diffs[0].field == "root.b"
    assert "added" in diffs[0].description

    # Dict removed key
    diffs = _deep_diff("root", {"a": 1, "b": 2}, {"a": 1}, ChangeType.COSMETIC, None)
    assert len(diffs) == 1
    assert diffs[0].field == "root.b"
    assert "removed" in diffs[0].description

    # Primitives
    diffs = _deep_diff("val", 1, 2, ChangeType.COSMETIC, None)
    assert len(diffs) == 1
    assert diffs[0].old_value == "1"

    # Lists
    diffs = _deep_diff("list", [1], [2], ChangeType.COSMETIC, None)
    assert len(diffs) == 1
    assert diffs[0].old_value == "[1]"


def test_diff_engine_coverage() -> None:
    # Interface
    meta = _get_base_metadata()
    flow1 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={"a": "int"}, outputs={}),
        blackboard=None,
        graph=Graph(nodes={}, edges=[]),
    )
    flow2 = flow1.model_copy(update={"interface": FlowInterface(inputs={"a": "str"}, outputs={"b": "int"})})

    changes = ManifestDiff.compare(flow1, flow2)
    assert any(c.field == "interface.inputs.a" for c in changes)
    assert any(c.field == "interface.outputs.b" for c in changes)

    # Agent Tools
    p = CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None)
    node1 = AgentNode(id="a", metadata={}, supervision=None, profile=p, tools=["t1"])
    node2 = node1.model_copy(update={"tools": ["t1", "t2"]})

    # Human interaction
    h1 = HumanNode(id="h", metadata={}, supervision=None, prompt="p1", timeout_seconds=10)
    h2 = h1.model_copy(update={"prompt": "p2", "interaction_mode": "steering"})

    # Swarm worker
    s1 = SwarmNode(
        id="s",
        metadata={},
        supervision=None,
        worker_profile="wp1",
        workload_variable="w",
        distribution_strategy="sharded",
        max_concurrency=1,
        failure_tolerance_percent=0,
        reducer_function="concat",
        output_variable="o",
    )
    s2 = s1.model_copy(update={"worker_profile": "wp2"})

    graph1 = Graph(nodes={"a": node1, "h": h1, "s": s1}, edges=[])
    graph2 = Graph(nodes={"a": node2, "h": h2, "s": s2}, edges=[])

    # We need definitions for SwarmNode validation AND AgentNode tool validation
    defs = FlowDefinitions(
        profiles={"wp1": p, "wp2": p},
        tool_packs={
            "default": ToolPack(kind="ToolPack", namespace="d", tools=["t1", "t2"], dependencies=[], env_vars=[])
        },
    )

    f1 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph1,
    )
    f2 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph2,
    )

    changes = ManifestDiff.compare(f1, f2)
    assert any(c.field == "tools" for c in changes)
    assert any(c.field == "prompt" for c in changes)
    assert any(c.field == "interaction_mode" for c in changes)
    assert any(c.field == "worker_profile" for c in changes)

    # Governance
    gov = Governance(rate_limit_rpm=100)
    f3 = f1.model_copy(update={"governance": gov})
    changes = ManifestDiff.compare(f1, f3)
    assert any(c.field == "governance.rate_limit_rpm" for c in changes)

    # Metadata Change
    node1_meta = node1.model_copy(update={"metadata": {"changed": True}})
    graph_meta = Graph(nodes={"a": node1_meta, "h": h1, "s": s1}, edges=[])
    f_meta = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph_meta,
    )
    changes = ManifestDiff.compare(f1, f_meta)
    assert any(c.field == "metadata.changed" for c in changes)

    # Presentation Change
    node1_pres = node1.model_copy(update={"presentation": PresentationHints(label="new")})
    graph_pres = Graph(nodes={"a": node1_pres, "h": h1, "s": s1}, edges=[])
    f_pres = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph_pres,
    )
    changes = ManifestDiff.compare(f1, f_pres)
    assert any(c.field == "presentation.label" for c in changes)

    # Profile Reference Change (String)
    node1_ref = AgentNode(id="a", metadata={}, supervision=None, profile="wp1", tools=[])
    node2_ref = AgentNode(id="a", metadata={}, supervision=None, profile="wp2", tools=[])

    f_ref1 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=Graph(nodes={"a": node1_ref}, edges=[]),
    )
    f_ref2 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=Graph(nodes={"a": node2_ref}, edges=[]),
    )

    changes = ManifestDiff.compare(f_ref1, f_ref2)
    assert any(c.field == "profile" and c.type == ChangeType.BEHAVIORAL for c in changes)

    # Node Type Change
    # Change 'a' from AgentNode to PlannerNode
    planner = PlannerNode(id="a", metadata={}, supervision=None, goal="g", optimizer=None, output_schema={})
    graph_type = Graph(nodes={"a": planner, "h": h1, "s": s1}, edges=[])
    f_type = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph_type,
    )
    changes = ManifestDiff.compare(f1, f_type)
    assert any(c.type == ChangeType.TOPOLOGICAL and c.field == "type" for c in changes)

    # Profile Object Change
    p1 = CognitiveProfile(role="r1", persona="p", reasoning=None, fast_path=None)
    p2 = CognitiveProfile(role="r2", persona="p", reasoning=None, fast_path=None)
    node1_p = AgentNode(id="a", metadata={}, supervision=None, profile=p1, tools=[])
    node2_p = AgentNode(id="a", metadata={}, supervision=None, profile=p2, tools=[])

    graph_p1 = Graph(nodes={"a": node1_p}, edges=[])
    graph_p2 = Graph(nodes={"a": node2_p}, edges=[])

    f_p1 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph_p1,
    )
    f_p2 = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=graph_p2,
    )

    changes = ManifestDiff.compare(f_p1, f_p2)
    assert any(c.field == "profile.role" for c in changes)


def test_mock_factory_coverage() -> None:
    factory = MockFactory(seed=123)

    # Test Schema generation types
    schema = {
        "type": "object",
        "properties": {
            "i": {"type": "integer"},
            "n": {"type": "number"},
            "b": {"type": "boolean"},
            "l": {"type": "array", "items": {"type": "string"}},
            "s": {"type": "string"},
            "o": {"type": "object", "properties": {"x": {"type": "integer"}}},
            "u": {"type": "unknown"},
        },
    }
    data = factory._generate_schema_data(schema)
    assert isinstance(data["i"], int)
    assert isinstance(data["n"], float)
    assert isinstance(data["b"], bool)
    assert isinstance(data["l"], list)
    assert isinstance(data["s"], str)
    assert isinstance(data["o"], dict)
    assert isinstance(data["o"]["x"], int)
    assert data["u"] == "mock_data"

    # Test LinearFlow
    nodes = [
        PlannerNode(id="p", metadata={}, supervision=None, goal="g", optimizer=None, output_schema=schema),
        HumanNode(id="h", metadata={}, supervision=None, prompt="p", timeout_seconds=1, input_schema=schema),
    ]
    flow = LinearFlow(kind="LinearFlow", metadata=_get_base_metadata(), sequence=nodes)  # type: ignore[arg-type]

    trace = factory.simulate_trace(flow)
    assert len(trace) == 2
    assert trace[0].node_id == "p"
    assert trace[1].node_id == "h"

    # Test GraphFlow Cycle
    # A -> B -> A
    n_a = AgentNode(
        id="a",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )
    n_b = AgentNode(
        id="b",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )

    from coreason_manifest.spec.core.flow import Edge

    edges = [Edge(source="a", target="b"), Edge(source="b", target="a")]

    graph = Graph(nodes={"a": n_a, "b": n_b}, edges=edges)
    flow_g = GraphFlow(
        kind="GraphFlow",
        metadata=_get_base_metadata(),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
    )

    trace_g = factory.simulate_trace(flow_g, max_steps=5)
    # Should run 5 steps due to loop
    assert len(trace_g) == 5

    # Test Generic node output (AgentNode uses generic logic in mock)
    generic_node_trace = next(t for t in trace_g if t.node_id == "a")
    assert "result" in generic_node_trace.outputs

    # Test Swarm execution
    s = SwarmNode(
        id="s",
        metadata={},
        supervision=None,
        worker_profile="wp1",
        workload_variable="w",
        distribution_strategy="sharded",
        max_concurrency=2,
        failure_tolerance_percent=0,
        reducer_function="concat",
        output_variable="o",
    )

    # Needs definitions? MockFactory doesn't check definitions.
    # But GraphFlow validation does.
    defs = FlowDefinitions(profiles={"wp1": CognitiveProfile(role="w", persona="w", reasoning=None, fast_path=None)})
    flow_swarm = GraphFlow(
        kind="GraphFlow",
        metadata=_get_base_metadata(),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        definitions=defs,
        graph=Graph(nodes={"s": s}, edges=[]),
    )
    trace_s = factory.simulate_trace(flow_swarm)
    # 2 workers + 1 aggregator
    assert len(trace_s) == 3

    # Test empty schema
    no_schema_data = factory._generate_schema_data(None)
    assert no_schema_data["mock_key"] == "mock_value"

    # Empty Graph (disconnected/no roots)
    graph_empty = Graph(nodes={}, edges=[])
    flow_empty = GraphFlow(
        kind="GraphFlow",
        metadata=_get_base_metadata(),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph_empty,
    )
    trace_empty = factory.simulate_trace(flow_empty)
    assert len(trace_empty) == 0


def test_visualizer_layout_coverage() -> None:
    # Test 1: Pure Cycle (No roots) to trigger fallback logic
    # A -> B -> A
    n_a = AgentNode(
        id="a",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )
    n_b = AgentNode(
        id="b",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )

    from coreason_manifest.spec.core.flow import Edge

    edges = [Edge(source="a", target="b"), Edge(source="b", target="a")]
    graph = Graph(nodes={"a": n_a, "b": n_b}, edges=edges)
    flow_cycle = GraphFlow(
        kind="GraphFlow",
        metadata=_get_base_metadata(),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
    )

    # This should trigger "no roots" logic
    rf_data = to_react_flow(flow_cycle)
    # Check that positions are assigned (not 0,0 for all)
    # Actually, the fallback assigns ranks.
    assert len(rf_data["nodes"]) == 2

    # Test 2: Disconnected Component / Unreachable Cycle to trigger "unvisited" logic
    # C (root), A -> B -> A (cycle)
    n_c = AgentNode(
        id="c",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
    )

    edges_mixed = [Edge(source="a", target="b"), Edge(source="b", target="a")]  # C is isolated
    graph_mixed = Graph(nodes={"a": n_a, "b": n_b, "c": n_c}, edges=edges_mixed)
    flow_mixed = GraphFlow(
        kind="GraphFlow",
        metadata=_get_base_metadata(),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph_mixed,
    )

    # C is root, so queue initially has [C]. A and B are never reached via BFS from C.
    # But A and B are part of a cycle, so their in-degree is initially > 0.
    # So they are unvisited.
    rf_data_mixed = to_react_flow(flow_mixed)
    assert len(rf_data_mixed["nodes"]) == 3
    # Check A and B got a fallback rank > C's rank (0)
    # Positions are x = rank * 300
    pos_c = next(n["position"]["x"] for n in rf_data_mixed["nodes"] if n["id"] == "c")
    pos_a = next(n["position"]["x"] for n in rf_data_mixed["nodes"] if n["id"] == "a")
    assert pos_a > pos_c
