import pytest

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.flow import (
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import PlaceholderNode
from coreason_manifest.spec.interop.exceptions import ManifestError


def test_graph_flow_published_placeholder_leak() -> None:
    """
    Test that a published GraphFlow containing a PlaceholderNode raises a ManifestError.
    """
    builder = NewGraphFlow("test_graph", "1.0.0", "Test Graph Flow")
    input_s = {"type": "object", "properties": {"query": {"type": "string"}}}
    output_s = {"type": "object", "properties": {"answer": {"type": "string"}}}
    builder.set_interface(inputs=input_s, outputs=output_s)

    node = PlaceholderNode(id="placeholder_1", metadata={}, type="placeholder", required_capabilities=[])
    builder.add_node(node)

    builder.set_entry_point("placeholder_1")

    # Assert that raising ManifestError works as expected
    # The builder attempts to create a published flow by default, so it should fail here.
    with pytest.raises(ManifestError) as excinfo:
        builder.build()

    assert excinfo.value.fault.error_code == "CRSN-VAL-LIFECYCLE-PLACEHOLDER"
    assert excinfo.value.fault.severity == "CRITICAL"
    assert excinfo.value.fault.recovery_action == "HALT_GRAPH"

def test_linear_flow_published_placeholder_leak() -> None:
    """
    Test that a published LinearFlow containing a PlaceholderNode raises a ManifestError.
    """
    metadata = FlowMetadata(name="test_linear", version="1.0.0", description="Test Linear Flow")

    placeholder_node = PlaceholderNode(id="placeholder_1", metadata={}, type="placeholder", required_capabilities=[])

    with pytest.raises(ManifestError) as excinfo:
        LinearFlow(
            metadata=metadata,
            steps=[placeholder_node],
            status="published"
        )

    assert excinfo.value.fault.error_code == "CRSN-VAL-LIFECYCLE-PLACEHOLDER"

def test_graph_flow_published_missing_entrypoint() -> None:
    """
    Test that a published GraphFlow with missing or invalid entry_point raises ManifestError.
    """
    metadata = FlowMetadata(name="test_graph_entrypoint", version="1.0.0", description="Test Graph Flow Entrypoint")
    interface = FlowInterface()

    # Case 1: Entry point is None
    # We construct GraphFlow manually to bypass Builder's auto-fix logic
    graph = Graph(nodes={}, edges=[], entry_point=None)

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            metadata=metadata,
            interface=interface,
            graph=graph,
            status="published"
        )

    assert excinfo.value.fault.error_code == "CRSN-VAL-LIFECYCLE-ENTRYPOINT"

    # Case 2: Entry point set but not in nodes
    graph_bad_ep = Graph(nodes={}, edges=[], entry_point="non_existent_node")

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            metadata=metadata,
            interface=interface,
            graph=graph_bad_ep,
            status="published"
        )

    assert excinfo.value.fault.error_code == "CRSN-VAL-LIFECYCLE-ENTRYPOINT"
