import pytest

from coreason_manifest.spec.core.flow import FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import PlaceholderNode
from coreason_manifest.spec.interop.exceptions import FaultSeverity, ManifestError, RecoveryAction


def test_graph_flow_lifecycle_validation() -> None:
    """
    Test that GraphFlow raises ManifestError when status is 'published' and contains a PlaceholderNode.
    """
    placeholder = PlaceholderNode(id="placeholder_1", type="placeholder", required_capabilities=["reasoning"])

    graph = Graph(nodes={"placeholder_1": placeholder}, edges=[])

    metadata = FlowMetadata(name="test_flow", version="0.1.0")

    # Should pass in draft mode
    flow_draft = GraphFlow(status="draft", metadata=metadata, graph=graph, interface=FlowInterface())
    assert flow_draft.status == "draft"

    # Should fail in published mode
    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(status="published", metadata=metadata, graph=graph, interface=FlowInterface())

    fault = excinfo.value.fault
    assert fault.error_code == "CRSN-VAL-LIFECYCLE-LEAK"
    assert fault.severity == FaultSeverity.CRITICAL
    assert fault.recovery_action == RecoveryAction.HALT
    assert "Cannot publish flow: Contains abstract PlaceholderNode 'placeholder_1'" in fault.message
    assert fault.context["remediation"]["type"] == "replace_node"


def test_linear_flow_lifecycle_validation() -> None:
    """
    Test that LinearFlow raises ManifestError when status is 'published' and contains a PlaceholderNode.
    """
    placeholder = PlaceholderNode(id="placeholder_1", type="placeholder", required_capabilities=["reasoning"])

    metadata = FlowMetadata(name="test_linear_flow", version="0.1.0")

    # Should pass in draft mode
    flow_draft = LinearFlow(status="draft", metadata=metadata, steps=[placeholder])
    assert flow_draft.status == "draft"

    # Should fail in published mode
    with pytest.raises(ManifestError) as excinfo:
        LinearFlow(status="published", metadata=metadata, steps=[placeholder])

    fault = excinfo.value.fault
    assert fault.error_code == "CRSN-VAL-LIFECYCLE-LEAK"
    assert fault.severity == FaultSeverity.CRITICAL
    assert fault.recovery_action == RecoveryAction.HALT
    assert "Cannot publish linear flow: Contains abstract PlaceholderNode 'placeholder_1'" in fault.message
    assert fault.context["remediation"]["type"] == "replace_node"
