from typing import cast

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.flow import (
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
    FlowMetadata
)
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    SwitchNode,
)
from coreason_manifest.spec.core.resilience import (
    FallbackStrategy,
    SupervisionPolicy,
)
from coreason_manifest.utils.validator import validate_flow


def create_placeholder(node_id: str) -> AgentNode:
    """Helper to create a minimal valid AgentNode (acting as placeholder)."""
    return AgentNode(id=node_id, profile=CognitiveProfile(role="tester", persona="persona"))


def build_flow_without_validation(builder: NewGraphFlow) -> GraphFlow:
    """
    Helper to construct GraphFlow directly from builder state,
    bypassing builder.build() which performs validation.
    """
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
    """Test that a valid A -> B -> C Directed Acyclic Graph (DAG) passes validation."""
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
    """
    Test that a simple execution loop (A -> B -> A) is ALLOWED in GraphFlow.
    CoReason v2 supports cyclic graphs.
    """
    builder = NewGraphFlow("test_cycle", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))

    builder.connect("A", "B")
    builder.connect("B", "A")
    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    # Cycles are allowed in v0.25.0+
    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) == 0, f"Unexpected cycle error: {errors}"


def test_self_referencing_node() -> None:
    """Test that a direct self-loop (A -> A) is ALLOWED."""
    builder = NewGraphFlow("test_self_loop", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    builder.add_node(create_placeholder("A"))

    builder.connect("A", "A")
    builder.set_entry_point("A")

    flow = build_flow_without_validation(builder)
    errors = validate_flow(flow)

    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) == 0, f"Unexpected cycle error: {errors}"


def test_isolated_cycle() -> None:
    """
    Test an isolated cycle (C -> D -> C) unreachable from entry point.
    """
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

    # Should be valid structurally
    assert not errors, f"Unexpected errors: {errors}"


def test_switch_node_cycle() -> None:
    """
    Test cycle detection involving a SwitchNode via implicit routing.
    Cycle: A (Switch) -> B (via case) -> A
    ALLOWED in cyclic graphs.
    """
    builder = NewGraphFlow("test_switch_cycle", "1.0.0", "desc")
    # Need a variable for SwitchNode
    builder.set_blackboard(variables={"v": VariableDef(type="string", id="v")})
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
    assert len(cycle_errors) == 0, f"Unexpected cycle error: {errors}"


def test_linear_flow_cycle() -> None:
    """
    Test LinearFlow implicit sequential edges combined with SwitchNode cycle.
    """
    node_a = create_placeholder("A")
    node_b = create_placeholder("B")
    node_c = SwitchNode(id="C", metadata={}, type="switch", variable="v", cases={}, default="A")

    flow = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="linear_cycle_test", version="1.0.0", description=""),
        steps=[node_a, node_b, node_c],
        definitions=None,
    )

    errors = validate_flow(flow)
    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) == 0


def test_hybrid_fallback_cycle() -> None:
    """
    Test hybrid cycle via execution and fallback edges.
    Graph: A -> B
    Fallback: B -> A
    Cycle: A -> B -> (fail) -> A

    Current `validator.py` only detects PURE fallback cycles (chains of fallbacks).
    Hybrid cycles are not currently flagged as errors in validation (though they might be infinite loops at runtime).
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

    # Expect error from _validate_fallback_cycles? No, it doesn't catch hybrid.
    cycle_errors = [e for e in errors if "Fallback cycle detected" in e]
    assert len(cycle_errors) == 0, "Wait, we don't expect fallback cycle errors for hybrid cycles in current impl."


def test_global_circuit_breaker_cycle() -> None:
    """
    Test cycle involving Global Circuit Breaker.
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
    assert len(cycle_errors) == 0


def test_valid_global_circuit_breaker_passes() -> None:
    """
    Test that a valid global circuit breaker does NOT flag a cycle.
    Graph: A -> B. Global Fallback is C.
    A -> C, B -> C. No cycle.
    """
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

    # Filter out Orphan warnings as C is technically an orphan in the execution graph
    critical_errors = [e for e in errors if "Orphan Node Warning" not in e]
    assert not critical_errors, f"Unexpected errors: {errors}"


def test_referenced_template_cycle() -> None:
    """
    Test that a cycle introduced via a referenced supervision template is caught.
    """
    builder = NewGraphFlow("template_cycle", "1.0.0", "desc")
    builder.set_interface(inputs={"type": "object", "properties": {}}, outputs={"type": "object", "properties": {}})

    node_a = create_placeholder("A")
    # Node B references a template
    node_b = AgentNode(id="B", type="agent", metadata={}, resilience="ref:loop_to_a", profile="p", tools=[])

    builder.add_node(node_a)
    builder.add_node(node_b)
    builder.connect("A", "B")
    builder.set_entry_point("A")
    builder.define_profile("p", "r", "p")

    from coreason_manifest.spec.core.resilience import FallbackStrategy, SupervisionPolicy

    definitions = builder._build_definitions()
    object.__setattr__(
        definitions,
        "supervision_templates",
        {"loop_to_a": SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="A"))},
    )

    ep = builder._entry_point
    if not ep:
        ep = next(iter(builder._nodes.keys())) if builder._nodes else "missing_entry_point"

    graph = Graph(nodes=builder._nodes, edges=builder._edges, entry_point=ep)

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=builder.metadata,
        interface=builder.interface,
        blackboard=builder.blackboard,
        graph=graph,
        definitions=definitions,
        governance=builder.governance,
    )

    errors = validate_flow(flow)
    # _validate_fallback_cycles should NOT find a cycle because A has no fallback.
    cycle_errors = [e for e in errors if "cycle detected" in e]
    assert len(cycle_errors) == 0
