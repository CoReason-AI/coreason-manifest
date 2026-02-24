import pytest
from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.nodes import PlaceholderNode
from coreason_manifest.utils.validator import validate_flow

def create_placeholder(id: str):
    return PlaceholderNode(id=id, metadata={}, type="placeholder", required_capabilities=[])

def test_valid_dag_passes():
    """A -> B -> C should pass validation."""
    builder = NewGraphFlow("test_dag", "1.0.0", "desc")
    builder.set_interface(
        inputs={"type": "object", "properties": {}},
        outputs={"type": "object", "properties": {}}
    )

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))
    builder.add_node(create_placeholder("C"))

    builder.connect("A", "B")
    builder.connect("B", "C")
    builder.set_entry_point("A")

    flow = builder.build()
    errors = validate_flow(flow)
    assert not errors

def test_simple_execution_cycle():
    """A -> B -> A should fail."""
    builder = NewGraphFlow("test_cycle", "1.0.0", "desc")
    builder.set_interface(
        inputs={"type": "object", "properties": {}},
        outputs={"type": "object", "properties": {}}
    )

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))

    builder.connect("A", "B")
    builder.connect("B", "A")
    builder.set_entry_point("A")

    with pytest.raises(ValueError) as excinfo:
        builder.build()

    error_msg = str(excinfo.value)
    assert "Topology Integrity Error: Infinite execution cycle detected" in error_msg
    assert "A" in error_msg and "B" in error_msg

def test_self_referencing_node():
    """A -> A should fail."""
    builder = NewGraphFlow("test_self_loop", "1.0.0", "desc")
    builder.set_interface(
        inputs={"type": "object", "properties": {}},
        outputs={"type": "object", "properties": {}}
    )

    builder.add_node(create_placeholder("A"))

    builder.connect("A", "A")
    builder.set_entry_point("A")

    with pytest.raises(ValueError) as excinfo:
        builder.build()

    error_msg = str(excinfo.value)
    assert "Topology Integrity Error: Infinite execution cycle detected" in error_msg
    assert "A" in error_msg

def test_isolated_cycle():
    """A -> B (valid), C -> D -> C (isolated cycle) should fail."""
    builder = NewGraphFlow("test_isolated_cycle", "1.0.0", "desc")
    builder.set_interface(
        inputs={"type": "object", "properties": {}},
        outputs={"type": "object", "properties": {}}
    )

    builder.add_node(create_placeholder("A"))
    builder.add_node(create_placeholder("B"))
    builder.add_node(create_placeholder("C"))
    builder.add_node(create_placeholder("D"))

    builder.connect("A", "B")
    builder.connect("C", "D")
    builder.connect("D", "C")
    builder.set_entry_point("A")

    # Even if it's isolated (unreachable from entry point), strict DAG validation should catch it.
    # Note: If existing validation catches "Orphan Node", builder.build() will raise.
    # We need to make sure it includes the Cycle error.

    with pytest.raises(ValueError) as excinfo:
        builder.build()

    error_msg = str(excinfo.value)
    assert "Topology Integrity Error: Infinite execution cycle detected" in error_msg
    assert "C" in error_msg and "D" in error_msg
