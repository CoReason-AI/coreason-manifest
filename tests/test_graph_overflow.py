import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.workflow.topologies import AnyTopology

topology_adapter: TypeAdapter[AnyTopology] = TypeAdapter(AnyTopology)


def test_cwe_674_deep_linear_chain() -> None:
    """
    Prove that a 5000-deep linear chain can be validated without RecursionError.
    """
    payload = {
        "type": "dag",
        "nodes": {f"did:web:node_{i}": {"type": "system", "description": "pass"} for i in range(5000)},
        "edges": [(f"did:web:node_{i}", f"did:web:node_{i + 1}") for i in range(4999)],
        "allow_cycles": False,
    }

    # This should succeed and not raise any exception.
    # If the DFS implementation is recursive instead of iterative,
    # this will raise a RecursionError because the default limit is 1000.
    topology_adapter.validate_python(payload)


def test_cwe_674_deep_cycle_detection() -> None:
    """
    Prove that a 5000-deep graph containing a cycle raises a ValidationError

    without causing a RecursionError or hanging.
    """
    edges = [(f"did:web:node_{i}", f"did:web:node_{i + 1}") for i in range(4999)]
    # Connect the tail to the head to create a loop-back cycle
    edges.append(("did:web:node_4999", "did:web:node_0"))

    payload = {
        "type": "dag",
        "nodes": {f"did:web:node_{i}": {"type": "system", "description": "pass"} for i in range(5000)},
        "edges": edges,
        "allow_cycles": False,
    }

    with pytest.raises(ValidationError) as exc_info:
        topology_adapter.validate_python(payload)

    # Verify the error message proves the DFS safely traversed the graph and found the cycle
    assert "Graph contains cycles" in str(exc_info.value)
