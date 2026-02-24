from datetime import datetime

import pytest

from coreason_manifest.spec.core.flow import Edge, FlowDefinitions, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.io import SecurityViolationError


def test_telemetry_parent_hash_backfill() -> None:
    """
    Cover telemetry.py:92: if prev_hashes is None: data["parent_hashes"] = [p_hash]
    """
    # Use model_construct to control input exactly? No, enforce_envelope_consistency is a pre-validator.
    # We need to pass data such that parent_hashes is None (or missing) and parent_hash is present.

    data = {
        "node_id": "n1",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": datetime.now(),
        "duration_ms": 1.0,
        "parent_hash": "some_hash"
        # parent_hashes missing
    }

    node = NodeExecution(**data)
    assert node.parent_hashes == ["some_hash"]

def test_flow_fallback_orphan() -> None:
    """
    Cover flow.py:316: Rule B: Fallback Orphans.
    """
    node = AgentNode(id="n1", type="agent", metadata={}, profile="p1", tools=[], resilience=None)
    graph = Graph(nodes={"n1": node}, edges=[], entry_point="n1")

    # Governance with fallback pointing to missing node
    gov = Governance(circuit_breaker=CircuitBreaker(
        error_threshold_count=1,
        reset_timeout_seconds=1,
        fallback_node_id="missing_node"
    ))

    definitions = FlowDefinitions(profiles={"p1": "dummy"}) # Minimal

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
            interface=FlowInterface(),
            graph=graph,
            governance=gov,
            definitions=definitions
        )
    assert excinfo.value.fault.error_code == "CRSN-VAL-FALLBACK-MISSING"

def test_edge_condition_security_violation_store() -> None:
    """
    Cover flow.py:144: SecurityViolationError for non-Load context (e.g. Walrus).
    Note: NamedExpr is not in whitelist, so it raises generic forbidden error first.
    The Name context check is defensive.
    """
    # Walrus operator := uses Store context for the target name
    # condition: (x := 1)

    with pytest.raises(SecurityViolationError, match="forbidden AST node NamedExpr"):
        Edge(from_node="a", to_node="b", condition="(x := 1)")
