import pytest

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.nodes import PlaceholderNode
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.spec.core.flow import Graph, GraphFlow


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
