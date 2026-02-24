from coreason_manifest.builder import NewGraphFlow, NewLinearFlow
from coreason_manifest.spec.core.flow import Graph, GraphFlow, LinearFlow, VariableDef
from coreason_manifest.spec.core.nodes import AgentNode, PlaceholderNode, SwitchNode
from coreason_manifest.spec.core.resilience import FallbackStrategy
from coreason_manifest.utils.validator import validate_flow


def create_placeholder(node_id: str) -> PlaceholderNode:
    return PlaceholderNode(id=node_id, metadata={}, type="placeholder", required_capabilities=[])


def build_flow_without_validation(builder: NewGraphFlow) -> GraphFlow:
    # Helper to construct GraphFlow directly from builder state, bypassing builder.build() which validates
    ep = builder._entry_point
    if not ep:
        ep = next(iter(builder._nodes.keys())) if builder._nodes else "missing_entry_point"

    graph = Graph(nodes=builder._nodes, edges=builder._edges, entry_point=ep)

    return GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=builder.metadata,
        interface=builder.interface,
        blackboard=builder.blackboard,
        graph=graph,
        definitions=builder._build_definitions(),
        governance=builder.governance,
    )


def test_valid_dag_passes() -> None:
    """A -> B -> C should pass validation."""
    builder = NewGraphFlow("test_dag", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))
    builder.add_node(create_placeholder("C"))

    builder.connect("A", "B")
    builder.connect("B", "C")
    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)
    assert not errors


def test_simple_execution_cycle() -> None:
    """A -> B -> A should fail."""
    builder = NewGraphFlow("test_cycle", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))

    builder.connect("A", "B")
    builder.connect("B", "A")
    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]

    assert len(cycle_errors) > 0, f"Expected cycle error, got: {errors}"
    assert "A" in cycle_errors[0]
    assert "B" in cycle_errors[0]


def test_self_referencing_node() -> None:
    """A -> A should fail."""
    builder = NewGraphFlow("test_self_loop", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))

    builder.connect("A", "A")
    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) > 0, f"Expected cycle error, got: {errors}"
    assert "A" in cycle_errors[0]


def test_isolated_cycle() -> None:
    """A -> B (valid), C -> D -> C (isolated cycle) should fail."""
    builder = NewGraphFlow("test_isolated_cycle", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))
    builder.add_node(create_placeholder("C"))
    builder.add_node(create_placeholder("D"))

    builder.connect("A", "B")
    builder.connect("C", "D")
    builder.connect("D", "C")
    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) > 0, f"Expected cycle error, got: {errors}"
    assert "C" in cycle_errors[0]
    assert "D" in cycle_errors[0]


def test_switch_node_cycle() -> None:
    """
    Test cycle detection involving a SwitchNode via implicit routing.
    A (Switch) -> B (via case) -> A
    """
    builder = NewGraphFlow("test_switch_cycle", "1.0.0", "desc")
    # Need a variable for SwitchNode
    builder.set_blackboard(variables={"v": VariableDef(type="string")})
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    # A is SwitchNode: if v="x" -> B
    builder.add_node(SwitchNode(id="A", metadata={}, type="switch", variable="v", cases={"x": "B"}, default="B"))

    # B is Placeholder: B -> A
    builder.add_node(create_placeholder("B"))
    builder.connect("B", "A")

    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) > 0, f"Expected cycle error involving SwitchNode, got: {errors}"
    assert "A" in cycle_errors[0]
    assert "B" in cycle_errors[0]


def test_linear_flow_cycle() -> None:
    """
    Test linear flow implicit edges combined with SwitchNode cycle.
    Linear: [A, B, C]
    Edges: A -> B -> C
    SwitchNode C: default -> A
    Cycle: A -> B -> C -> A
    """
    lf = NewLinearFlow("linear_cycle_test")

    # Need variable for switch
    # LinearFlow builder doesn't have set_blackboard in my mock?
    # I'll construct it manually or assume NewLinearFlow can do it.
    # NewLinearFlow inherits BaseFlowBuilder, so it doesn't have set_blackboard exposed?
    # But LinearFlow model has blackboard.
    # I'll construct the flow manually.

    node_a = create_placeholder("A")
    node_b = create_placeholder("B")
    node_c = SwitchNode(id="C", metadata={}, type="switch", variable="v", cases={}, default="A")

    flow = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=lf.metadata,
        steps=[node_a, node_b, node_c],
        definitions=lf._build_definitions(),
    )

    # Need variable 'v' to pass data flow check, but we are testing cycles.
    # Data flow check is separate.
    # If I don't provide blackboard, data flow check might fail.
    # But I care about cycle error.

    errors = validate_flow(flow)
    cycle_errors = [e for e in errors if "cycle detected" in e]

    assert len(cycle_errors) > 0, f"Expected cycle error in LinearFlow, got: {errors}"
    assert "A" in cycle_errors[0]
    assert "C" in cycle_errors[0]


def test_hybrid_fallback_cycle() -> None:
    """
    Graph: A -> B
    Fallback: B -> A
    Cycle: A -> B -> (fail) -> A
    """
    builder = NewGraphFlow("hybrid_fallback", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    node_a = create_placeholder("A")

    # Node B with fallback to A
    fallback = FallbackStrategy(fallback_node_id="A")
    node_b = AgentNode(id="B", type="agent", metadata={}, resilience=fallback, profile="p", tools=[])

    builder.add_node(node_a)
    builder.add_node(node_b)
    builder.connect("A", "B")
    builder.set_entry_point("A")
    builder.define_profile("p", "r", "p")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) > 0, f"Expected hybrid fallback cycle, got: {errors}"
    assert "A" in cycle_errors[0]
    assert "B" in cycle_errors[0]


def test_global_circuit_breaker_cycle() -> None:
    """
    Graph: A -> B
    Global Circuit Breaker: fallback -> A
    Cycle: A -> B -> (global fail) -> A
    """
    builder = NewGraphFlow("global_cb_cycle", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))
    builder.connect("A", "B")
    builder.set_entry_point("A")

    # Set global circuit breaker pointing to A
    builder.set_circuit_breaker(error_threshold=5, reset_timeout=30, fallback_node="A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) > 0, f"Expected global circuit breaker cycle, got: {errors}"
    assert "A" in cycle_errors[0]
    assert "B" in cycle_errors[0]


def test_valid_global_circuit_breaker_passes() -> None:
    """A -> B. Global Fallback is C. Should NOT flag as a cycle."""
    builder = NewGraphFlow("valid_global_cb", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))
    builder.add_node(create_placeholder("C"))  # The Fallback Node
    builder.connect("A", "B")
    builder.set_entry_point("A")

    builder.set_circuit_breaker(error_threshold=5, reset_timeout=30, fallback_node="C")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)
    # SOTA FIX: With unified adjacency map, 'C' is reachable via global fallback, so it shouldn't be an orphan.
    # Assert absolutely NO errors are returned.
    assert not errors, f"Unexpected errors: {errors}"
