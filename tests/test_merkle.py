from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof


def create_node(
    node_id: str,
    parent: str | None = None,
    previous: list[str] | None = None,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
) -> NodeExecution:
    if inputs is None:
        inputs = {}
    if outputs is None:
        outputs = {}
    if previous is None:
        previous = []

    # Generate IDs
    req_id = str(uuid4())
    root_id = str(uuid4())  # Simplification

    # Construct initial data to compute hash

    data: dict[str, Any] = {
        "node_id": node_id,
        "state": NodeState.COMPLETED,
        "inputs": inputs,
        "outputs": outputs,
        "timestamp": datetime.now(UTC),
        "duration_ms": 10.0,
        "request_id": req_id,
        "root_request_id": root_id,
        "parent_hashes": previous,
        "parent_hash": parent,
        "hash_version": "v2",
    }

    # Helper to clean None
    if parent is None:
        del data["parent_hash"]

    # Validation will run here (enforce_topology_consistency)
    temp_node = NodeExecution(**data)

    # Compute hash
    payload = temp_node.model_dump()
    h = compute_hash(payload)

    # Final node
    final_data = temp_node.model_dump()
    final_data["execution_hash"] = h

    return NodeExecution(**final_data)


def test_linear_chain_verification() -> None:
    n1 = create_node("n1")
    n2 = create_node("n2", parent=n1.execution_hash)
    n3 = create_node("n3", parent=n2.execution_hash)

    trace = [n1, n2, n3]
    assert verify_merkle_proof(trace), "Linear chain should verify"


def test_dag_fan_in_verification() -> None:
    n1 = create_node("n1")
    n2 = create_node("n2")

    # n3 depends on n1 and n2
    n3 = create_node("n3", previous=[n1.execution_hash, n2.execution_hash])  # type: ignore

    trace = [n1, n2, n3]
    assert verify_merkle_proof(trace), "DAG fan-in should verify"


def test_topology_violation_hallucinated_parent() -> None:
    n1 = create_node("n1")
    n2 = create_node("n2", parent="sha256:fakehash")

    trace = [n1, n2]
    assert not verify_merkle_proof(trace), "Hallucinated parent should fail verification"


def test_topology_violation_order() -> None:
    n1 = create_node("n1")
    n2 = create_node("n2", parent=n1.execution_hash)

    # Topological sort violation (child before parent)
    trace = [n2, n1]
    assert not verify_merkle_proof(trace), "Out-of-order trace should fail verification"


def test_content_tampering() -> None:
    n1 = create_node("n1")

    # Tamper with content but keep hash
    # Since NodeExecution is frozen, we hack the dict
    tampered_data = n1.model_dump()
    tampered_data["inputs"] = {"malicious": "payload"}
    # Note: execution_hash in tampered_data is still the original hash of n1

    # If verify_merkle_proof takes dicts (it does support reconstruct_payload from dict),
    # let's pass dict. But verify_merkle_proof also takes objects.
    # The `trace` is usually list[NodeExecution] or list[dict].

    trace = [tampered_data]
    assert not verify_merkle_proof(trace), "Tampered content should fail hash check"
