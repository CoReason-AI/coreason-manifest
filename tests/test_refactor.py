import asyncio
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import (
    AgentRequest,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof
from coreason_manifest.utils.io import SecurityViolationError
from coreason_manifest.utils.loader import _jail_root_var, sandbox_context


# Helper to create minimal valid metadata
def get_meta() -> FlowMetadata:
    return FlowMetadata(name="test", version="0.1.0", description="test")


def get_agent_node(nid: str) -> AgentNode:
    return AgentNode(id=nid, type="agent", profile=CognitiveProfile(role="r", persona="p"), tools=[])


def test_dangling_entry_point_rejected() -> None:
    """
    1. test_dangling_entry_point_rejected: Attempting to instantiate a GraphFlow
       where the entry_point is "node_a" but nodes only contains "node_b" throws a Pydantic ValidationError.
    """
    # The framework raises a specific ManifestError inside the validator
    with pytest.raises((ValidationError, ManifestError)) as excinfo:
        GraphFlow(
            metadata=get_meta(),
            interface=FlowInterface(),
            graph=Graph(nodes={"node_b": get_agent_node("node_b")}, edges=[], entry_point="node_a"),
        )
    assert "CRSN-VAL-ENTRY-POINT-MISSING" in str(excinfo.value) or "Entry point 'node_a' not found" in str(
        excinfo.value
    )


def test_ast_injection_blocked() -> None:
    """
    2. test_ast_injection_blocked: Defining an Edge with
       condition="__import__('os').system('rm -rf /')" throws a Pydantic ValidationError.
    """
    # The framework raises a specific SecurityViolationError inside the validator
    with pytest.raises((ValidationError, SecurityViolationError)) as excinfo:
        Edge(from_node="a", to_node="b", condition="__import__('os').system('rm -rf /')")
    assert "Security Violation: forbidden AST node Call" in str(excinfo.value)


@pytest.mark.asyncio
async def test_sandboxed_loader_concurrent(tmp_path: Path) -> None:
    """
    3. test_sandboxed_loader_concurrent: Run two mocked agents concurrently using asyncio.gather.
       Prove that ContextVar successfully isolates their import paths.
    """
    jail_a = tmp_path / "jail_a"
    jail_b = tmp_path / "jail_b"
    jail_a.mkdir()
    jail_b.mkdir()

    async def task_a() -> Path | None:
        with sandbox_context(jail_a):
            # Simulate work
            await asyncio.sleep(0.01)
            assert _jail_root_var.get() == jail_a.resolve()
            return _jail_root_var.get()

    async def task_b() -> Path | None:
        with sandbox_context(jail_b):
            # Simulate work
            await asyncio.sleep(0.01)
            assert _jail_root_var.get() == jail_b.resolve()
            return _jail_root_var.get()

    results = await asyncio.gather(task_a(), task_b())
    assert results[0] == jail_a.resolve()
    assert results[1] == jail_b.resolve()


def test_merkle_dag_parallel() -> None:
    """
    4. test_merkle_dag_parallel: Create a Swarm trace where Node A branches to Node B1 and B2,
       which then aggregate to Node C. Prove that verify_merkle_proof successfully validates the DAG topology.
    """
    # Create nodes
    # A (Genesis)
    node_a: dict[str, Any] = {"data": "A", "parent_hashes": []}
    hash_a = compute_hash(node_a)
    node_a["execution_hash"] = hash_a

    # B1 (Parent: A)
    node_b1: dict[str, Any] = {"data": "B1", "parent_hashes": [hash_a]}
    hash_b1 = compute_hash(node_b1)
    node_b1["execution_hash"] = hash_b1

    # B2 (Parent: A)
    node_b2: dict[str, Any] = {"data": "B2", "parent_hashes": [hash_a]}
    hash_b2 = compute_hash(node_b2)
    node_b2["execution_hash"] = hash_b2

    # C (Parents: B1, B2)
    node_c: dict[str, Any] = {"data": "C", "parent_hashes": [hash_b1, hash_b2]}
    hash_c = compute_hash(node_c)
    node_c["execution_hash"] = hash_c

    trace = [node_a, node_b1, node_b2, node_c]

    # Verify in order
    assert verify_merkle_proof(trace) is True

    # Shuffle and verify (should sort internally)
    import random

    shuffled_trace = trace[:]
    random.shuffle(shuffled_trace)
    assert verify_merkle_proof(shuffled_trace) is True

    # Tamper with one hash
    tampered_node_c = node_c.copy()
    tampered_node_c["data"] = "C_tampered"
    # Keeping old hash -> mismatch
    trace_tampered = [node_a, node_b1, node_b2, tampered_node_c]
    assert verify_merkle_proof(trace_tampered) is False


def test_extra_fields_forbidden() -> None:
    """
    5. test_extra_fields_forbidden: Attempt to pass tenant_id="123" at the root of an
       AgentRequest instantiation. Prove it crashes with a validation error.
    """
    # Valid manifest
    manifest = GraphFlow(
        metadata=get_meta(),
        interface=FlowInterface(),
        graph=Graph(nodes={"start": get_agent_node("start")}, edges=[], entry_point="start"),
    )

    # Valid request
    AgentRequest(manifest=manifest, metadata={"tenant_id": "123"})

    # Invalid request with extra field
    with pytest.raises(ValidationError) as excinfo:
        AgentRequest(
            manifest=manifest,
            tenant_id="123",  # type: ignore # Extra field
        )
    # Pydantic v2 error for extra fields
    assert "Extra inputs are not permitted" in str(excinfo.value)
