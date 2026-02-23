import pytest
from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.core.nodes import PlaceholderNode
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.spec.interop.exceptions import ManifestError, FaultSeverity

def test_reproduce_placeholder_leak():
    """
    Demonstrate that a published flow with a placeholder now raises ManifestError.
    """
    placeholder = PlaceholderNode(
        id="wip_node",
        type="placeholder",
        required_capabilities=["image_gen"]
    )

    flow_data = {
        "type": "graph",
        "kind": "GraphFlow",
        "status": "published",
        "metadata": {
            "name": "Leak Test",
            "version": "1.0.0",
            "description": "A flow with a placeholder"
        },
        "interface": {
            "inputs": {},
            "outputs": {}
        },
        "graph": {
            "nodes": {"wip_node": placeholder},
            "edges": []
        }
    }

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(**flow_data)

    # Check error code
    assert excinfo.value.fault.error_code == "CRSN-VAL-LIFECYCLE-LEAK"
    assert excinfo.value.fault.severity == FaultSeverity.CRITICAL
    assert "remediation" in excinfo.value.fault.context

def test_reproduce_strict_draft_validation():
    """
    Demonstrate that draft flows now pass validation even if they have integrity issues.
    """
    placeholder = PlaceholderNode(
        id="node_a",
        type="placeholder",
        required_capabilities=["image_gen"]
    )

    flow_data = {
        "type": "graph",
        "kind": "GraphFlow",
        "status": "draft",
        "metadata": {
            "name": "Draft Test",
            "version": "0.1.0",
            "description": "A broken draft"
        },
        "interface": {
            "inputs": {},
            "outputs": {}
        },
        "graph": {
            "nodes": {"node_a": placeholder},
            "edges": [{"from": "node_a", "to": "nonexistent_b"}]
        }
    }

    flow = GraphFlow(**flow_data)
    errors = validate_flow(flow)

    # Should be empty now
    assert len(errors) == 0
