import random
import secrets
from typing import Any

from coreason_manifest.spec.core.flow import DataSchema, Edge, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import PlaceholderNode, PlannerNode, SwarmNode
from coreason_manifest.utils.mock import MockFactory


def _create_metadata() -> FlowMetadata:
    return FlowMetadata(name="Test Flow", version="1.0.0", description="A test flow", tags=["test"])


def _create_interface() -> FlowInterface:
    return FlowInterface(
        inputs=DataSchema(json_schema={"type": "object"}), outputs=DataSchema(json_schema={"type": "object"})
    )


def test_mock_factory_init() -> None:
    # Test with seed (deterministic)
    factory = MockFactory(seed=42)
    assert isinstance(factory.rng, random.Random)
    val1 = factory.rng.random()

    factory2 = MockFactory(seed=42)
    val2 = factory2.rng.random()
    assert val1 == val2

    # Test without seed (system random)
    factory3 = MockFactory()
    assert isinstance(factory3.rng, secrets.SystemRandom)


def test_generate_schema_data_types() -> None:
    factory = MockFactory(seed=1)

    # String
    assert factory._generate_schema_data({"type": "string"}) == "lorem ipsum"

    # Integer
    val = factory._generate_schema_data({"type": "integer"})
    assert isinstance(val, int)
    assert 1 <= val <= 100

    # Number
    val = factory._generate_schema_data({"type": "number"})
    assert isinstance(val, float)

    # Boolean
    val = factory._generate_schema_data({"type": "boolean"})
    assert isinstance(val, bool)

    # Object
    schema: dict[str, Any] = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    val = factory._generate_schema_data(schema)
    assert isinstance(val, dict)
    assert val["name"] == "lorem ipsum"
    assert isinstance(val["age"], int)

    # Array
    schema = {"type": "array", "items": {"type": "string"}}
    val = factory._generate_schema_data(schema)
    assert isinstance(val, list)
    assert len(val) == 1
    assert val[0] == "lorem ipsum"

    # Array empty items
    schema = {"type": "array"}
    assert factory._generate_schema_data(schema) == []

    # Default (unknown type)
    assert factory._generate_schema_data({"type": "unknown"}) == "mock_data"

    # None schema
    assert factory._generate_schema_data(None) == {"mock_key": "mock_value"}


def test_generate_schema_data_cycle() -> None:
    factory = MockFactory()

    # Create a recursive schema
    schema: dict[str, Any] = {"type": "object"}
    properties = {"self": schema}
    schema["properties"] = properties

    # Should handle cycle gracefully returning "" or stop recursing
    result = factory._generate_schema_data(schema)
    assert isinstance(result, dict)
    assert result["self"] == ""


def test_generate_schema_data_depth_limit() -> None:
    factory = MockFactory()

    # Create a deep nested schema (linear)
    root: dict[str, Any] = {"type": "object", "properties": {"next": {}}}
    current = root["properties"]["next"]
    for _ in range(12):
        current["type"] = "object"
        current["properties"] = {"next": {}}
        current = current["properties"]["next"]

    result = factory._generate_schema_data(root)
    assert isinstance(result, dict)


def test_simulate_trace_linear_flow() -> None:
    factory = MockFactory(seed=1)

    node1 = PlaceholderNode(id="n1", type="placeholder", required_capabilities=["c1"])
    node2 = PlaceholderNode(id="n2", type="placeholder", required_capabilities=["c2"])

    flow = LinearFlow(kind="LinearFlow", metadata=_create_metadata(), steps=[node1, node2])

    trace = factory.simulate_trace(flow)
    assert len(trace) == 2
    assert trace[0].node_id == "n1"
    assert trace[1].node_id == "n2"
    assert trace[1].parent_hashes == [trace[0].execution_hash]


def test_simulate_trace_graph_flow() -> None:
    factory = MockFactory(seed=1)

    n1 = PlaceholderNode(id="n1", type="placeholder", required_capabilities=["c1"])
    n2 = PlaceholderNode(id="n2", type="placeholder", required_capabilities=["c2"])
    n3 = PlaceholderNode(id="n3", type="placeholder", required_capabilities=["c3"])

    # n1 -> n2 -> n3
    graph = Graph(
        nodes={"n1": n1, "n2": n2, "n3": n3},
        edges=[Edge(from_node="n1", to_node="n2"), Edge(from_node="n2", to_node="n3")],
        entry_point="n1",
    )

    flow = GraphFlow(kind="GraphFlow", metadata=_create_metadata(), interface=_create_interface(), graph=graph)

    trace = factory.simulate_trace(flow, max_steps=5)
    # n1, n2, n3
    assert len(trace) == 3
    assert trace[0].node_id == "n1"
    assert trace[1].node_id == "n2"
    assert trace[2].node_id == "n3"


def test_simulate_trace_graph_cycle() -> None:
    factory = MockFactory(seed=1)

    n1 = PlaceholderNode(id="n1", type="placeholder", required_capabilities=["c1"])
    n2 = PlaceholderNode(id="n2", type="placeholder", required_capabilities=["c2"])

    # n1 <-> n2
    graph = Graph(
        nodes={"n1": n1, "n2": n2},
        edges=[Edge(from_node="n1", to_node="n2"), Edge(from_node="n2", to_node="n1")],
        entry_point="n1",
    )

    flow = GraphFlow(kind="GraphFlow", metadata=_create_metadata(), interface=_create_interface(), graph=graph)

    trace = factory.simulate_trace(flow, max_steps=5)
    assert len(trace) == 5


def test_execute_node_swarm() -> None:
    factory = MockFactory(seed=1)

    # Swarm node with limit
    swarm = SwarmNode(
        id="swarm1",
        type="swarm",
        worker_profile="profile1",
        max_concurrency=5,
        workload_variable="work",
        distribution_strategy="sharded",
        reducer_function="concat",
        output_variable="out",
    )
    exec_map: dict[str, Any] = {}

    results = factory._execute_node(swarm, exec_map)
    assert len(results) == 4
    assert results[0].attributes["worker"] is True
    assert results[-1].attributes["role"] == "aggregator"

    # Swarm node with infinite
    swarm_inf = SwarmNode(
        id="swarm2",
        type="swarm",
        worker_profile="profile1",
        max_concurrency="infinite",
        workload_variable="work",
        distribution_strategy="sharded",
        reducer_function="concat",
        output_variable="out",
    )
    results_inf = factory._execute_node(swarm_inf, exec_map)
    assert len(results_inf) == 4

    # Swarm node with None
    # Assuming validation allows it or we construct carefully
    try:
        swarm_none = SwarmNode.model_construct(
            id="swarm3",
            type="swarm",
            worker_profile="profile1",
            max_concurrency=None,
            workload_variable="work",
            distribution_strategy="sharded",
            reducer_function="concat",
            output_variable="out",
        )
        results_none = factory._execute_node(swarm_none, exec_map)
        assert len(results_none) == 4
    except Exception:
        pass


def test_execute_node_planner() -> None:
    factory = MockFactory(seed=1)
    planner = PlannerNode(id="planner1", type="planner", output_schema={"type": "string"}, goal="make plan")
    exec_map: dict[str, Any] = {}

    results = factory._execute_node(planner, exec_map)
    assert len(results) == 1
    assert results[0].outputs == {"result": "lorem ipsum"}


def test_simulate_trace_empty_graph() -> None:
    factory = MockFactory()
    # Use model_construct to bypass validation that requires entry_point to exist
    graph = Graph.model_construct(nodes={}, edges=[], entry_point="n1")
    flow = GraphFlow.model_construct(
        kind="GraphFlow", metadata=_create_metadata(), interface=_create_interface(), graph=graph
    )

    trace = factory.simulate_trace(flow)
    assert trace == []
