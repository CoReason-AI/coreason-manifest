import pytest
from pydantic import ValidationError
from typing import Any
from unittest.mock import patch

from coreason_manifest.spec.core.flow import GraphFlow, Graph, Edge, FlowMetadata, FlowInterface
from coreason_manifest.spec.core.governance import Governance, CircuitBreaker
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.integrity import verify_merkle_proof
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from datetime import datetime

# Helper
def get_meta() -> FlowMetadata:
    return FlowMetadata(name="test", version="0.1.0", description="test")

def get_agent_node(nid: str) -> AgentNode:
    return AgentNode(
        id=nid,
        type="agent",
        profile=CognitiveProfile(role="r", persona="p"),
        tools=[]
    )

def test_edge_condition_syntax_error() -> None:
    """Test that invalid Python syntax in Edge condition raises ValueError (wrapped in ValidationError)."""
    with pytest.raises(ValidationError) as excinfo:
        Edge(from_node="a", to_node="b", condition="if (")
    # Pydantic wraps the ValueError raised in validator
    assert "Invalid Python syntax" in str(excinfo.value)

def test_graph_fallback_missing() -> None:
    """Test that GraphFlow validates existence of circuit breaker fallback node."""
    graph = Graph(
        nodes={"start": get_agent_node("start")},
        edges=[],
        entry_point="start"
    )

    gov = Governance(
        circuit_breaker=CircuitBreaker(
            error_threshold_count=3,
            reset_timeout_seconds=10,
            fallback_node_id="missing_fallback"
        )
    )

    with pytest.raises(ManifestError, match="CRSN-VAL-FALLBACK-MISSING"):
        GraphFlow(
            kind="GraphFlow",
            metadata=get_meta(),
            interface=FlowInterface(),
            graph=graph,
            governance=gov
        )

def test_verify_merkle_cycle() -> None:
    """Test that verify_merkle_proof returns False for cyclical traces."""
    def mock_hash(obj: Any) -> str:
        # Return the 'id' field as the hash
        return str(obj.get("id"))

    with patch("coreason_manifest.utils.integrity.compute_hash", side_effect=mock_hash):
        # Now hash("A") = "A".
        # Node A: id="A", parent_hashes=["B"]
        # Node B: id="B", parent_hashes=["A"]

        node_a = {"id": "A", "parent_hashes": ["B"], "execution_hash": "A"}
        node_b = {"id": "B", "parent_hashes": ["A"], "execution_hash": "B"}

        trace = [node_a, node_b]

        # This should form a cycle A <-> B.
        # Topological sort should fail.
        # Function should return False.
        assert verify_merkle_proof(trace) is False

def test_telemetry_parent_hash_sync() -> None:
    """Test synchronization of parent_hash to parent_hashes in NodeExecution."""
    # Case: parent_hash present, parent_hashes missing (None)
    ne = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=10,
        parent_hash="ph1"
    )
    # The validator should have populated parent_hashes
    assert ne.parent_hashes == ["ph1"]

    # Case: parent_hash present, parent_hashes list but missing hash
    ne2 = NodeExecution(
        node_id="n2",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=10,
        parent_hash="ph2",
        parent_hashes=["other"]
    )
    assert "ph2" in ne2.parent_hashes
    assert "other" in ne2.parent_hashes
