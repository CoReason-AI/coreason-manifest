from coreason_manifest.spec.core.flow import FlowDefinitions, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.nodes import PlannerNode
from coreason_manifest.utils.mock import MockFactory


def test_mock_ref_resolution() -> None:
    # Define a flow with a schema definition and a planner node referencing it
    schema_def = {"type": "object", "properties": {"foo": {"type": "string"}}}

    ref_schema = {"$ref": "#/definitions/schemas/MyType"}

    definitions = FlowDefinitions(schemas={"MyType": schema_def})

    # PlannerNode output_schema is dict
    planner = PlannerNode(id="planner", type="planner", goal="plan", output_schema=ref_schema)

    graph = Graph(nodes={"planner": planner}, edges=[], entry_point="planner")

    flow = GraphFlow(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0.0", description="desc"),
        interface=FlowInterface(),
        definitions=definitions,
        graph=graph,
    )

    factory = MockFactory(seed=42)
    trace = factory.simulate_trace(flow)

    assert len(trace) > 0
    output = trace[0].outputs

    assert isinstance(output, dict)
    assert "foo" in output
    assert output["foo"] == "lorem ipsum"


def test_mock_ref_resolution_fail() -> None:
    # Test fallback when ref is invalid
    ref_schema = {"$ref": "#/definitions/schemas/Missing"}

    definitions = FlowDefinitions(schemas={})

    planner = PlannerNode(id="planner", type="planner", goal="plan", output_schema=ref_schema)

    graph = Graph(nodes={"planner": planner}, edges=[], entry_point="planner")

    flow = GraphFlow(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0.0", description="desc"),
        interface=FlowInterface(),
        definitions=definitions,
        graph=graph,
    )

    factory = MockFactory(seed=42)
    trace = factory.simulate_trace(flow)

    assert len(trace) > 0
    output = trace[0].outputs
    # Fallback is "mock_ref_error"
    # But MockFactory wraps non-dict in {"result": ...}
    assert output["result"] == "mock_ref_error"
