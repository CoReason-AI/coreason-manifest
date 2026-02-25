from unittest.mock import MagicMock

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


def test_mock_ref_cycle() -> None:
    # Test cycle detection in $ref
    # Schema A refs B, B refs A
    schema_a = {"$ref": "#/definitions/schemas/B"}
    schema_b = {"$ref": "#/definitions/schemas/A"}

    definitions = FlowDefinitions(schemas={"A": schema_a, "B": schema_b})

    planner = PlannerNode(id="planner", type="planner", goal="plan", output_schema=schema_a)

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

    # Should handle cycle gracefully (return empty string or terminate recursion)
    assert len(trace) > 0
    # The output might be empty string or partial
    # In _generate_schema_data, if cycle detected: return ""
    output = trace[0].outputs
    # It wraps result in dict if not dict
    assert output["result"] == ""


def test_mock_ref_generic_exception() -> None:
    # Trigger generic exception during resolution (now only catches Unresolvable/PointerToNowhere)
    # So a generic exception should bubble up
    from referencing.exceptions import Unresolvable

    factory = MockFactory(seed=42)

    # Broken resolver raising generic exception
    resolver_broken = MagicMock()
    resolver_broken.lookup.side_effect = Exception("Boom")

    schema = {"$ref": "something"}

    # Expect it to RAISE Exception, not catch it
    import pytest

    with pytest.raises(Exception, match="Boom"):
        factory._generate_schema_data(schema, resolver=resolver_broken)

    # Now verify Unresolvable is caught
    resolver_unresolvable = MagicMock()
    resolver_unresolvable.lookup.side_effect = Unresolvable(ref="something")

    result = factory._generate_schema_data(schema, resolver=resolver_unresolvable)
    assert result == "mock_ref_error"


def test_mock_edge_cases() -> None:
    factory = MockFactory(seed=42)

    # 1. Boolean schema
    assert factory._generate_schema_data(True) == "mock_data"
    assert factory._generate_schema_data(False) is None

    # 2. Not a dict (and not bool, e.g. None or int - though typing says dict|None)
    # If passed None directly, it returns default
    assert factory._generate_schema_data(None) == {"mock_key": "mock_value"}

    # 3. Union type
    schema_union = {"type": ["string", "null"]}
    assert factory._generate_schema_data(schema_union) == "lorem ipsum"

    # 4. Tuple validation (array of schemas)
    schema_tuple = {
        "type": "array",
        "items": [
            {"type": "string"},
            {"type": "integer"}
        ]
    }
    result = factory._generate_schema_data(schema_tuple)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == "lorem ipsum"
    assert isinstance(result[1], int)
