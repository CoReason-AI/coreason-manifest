import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.workflow.nodes import CompositeNode
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


def test_composite_node_depth_limit_rejected() -> None:
    """
    AGENT INSTRUCTION: Mathematically prove that a 6-level deep CompositeNode
    is rejected by the Pydantic Rust core before execution.
    """
    # Create a simple valid leaf node
    leaf_node = {"description": "Leaf", "type": "system"}

    # Manually nest a dictionary structure to bypass bottom-up instantiation blocks
    # and test the top-level deserialization drop
    # (Agent: Construct a recursive dictionary mapping that reaches depth 6,
    # then attempt to parse it into a CompositeNode).

    current_topology = {
        "type": "dag",
        "nodes": {"did:web:leaf_node": leaf_node},
        "edges": [],
        "allow_cycles": False,
    }

    for i in range(5):
        current_topology = {
            "type": "dag",
            "nodes": {
                f"did:web:composite_node_{i}": {
                    "type": "composite",
                    "description": f"Level {i + 1} composite node",
                    "topology": current_topology,
                }
            },
            "edges": [],
            "allow_cycles": False,
        }

    payload = {"description": "Root composite node", "type": "composite", "topology": current_topology}

    with pytest.raises(ValidationError) as exc_info:
        CompositeNode.model_validate(payload)

    assert "CompositeNode topology encapsulation exceeds maximum allowable depth of 5" in str(exc_info.value)
