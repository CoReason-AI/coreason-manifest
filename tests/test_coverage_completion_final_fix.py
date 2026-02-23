from datetime import datetime
import pytest

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.constants import NodeCapability
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof


def test_builder_graph_flow_empty_entry_point() -> None:
    """
    Test builder behavior when graph is empty (triggers 'missing_entry_point' branch)
    and validation failure coverage (builder.py:391).
    We inject an invalid governance to force validation error even in draft mode.
    """
    gf = NewGraphFlow(name="Empty Graph")

    # Set governance with negative rate limit to trigger validation error
    gf.set_governance(Governance(rate_limit_rpm=-10))

    with pytest.raises(ValueError, match="Governance Error: rate_limit_rpm cannot be negative"):
        gf.build()


def test_gatekeeper_coverage_complex() -> None:
    """
    Cover:
    - _is_guarded with entry_point set.
    - Self-loop detection in validate_policy (gatekeeper.py:219).
    """
    gf = NewGraphFlow(name="Risky Graph")

    # Define tool pack with critical tool
    from coreason_manifest.spec.core.tools import ToolCapability, ToolPack

    critical_tool = ToolCapability(name="rm_rf_tool", risk_level="critical", description="Deletes stuff")
    pack = ToolPack(kind="ToolPack", namespace="sys", tools=[critical_tool])

    gf.add_tool_pack(pack)

    # Add a safe node as entry point
    safe = AgentNode(id="safe", metadata={}, resilience=None, type="agent", profile="dummy", tools=[])
    gf.add_node(safe)

    # Add a risky agent
    risky = AgentNode(
        id="risky",
        metadata={},
        resilience=None,
        type="agent",
        profile="dummy",
        tools=["rm_rf_tool"]
    )
    gf.add_node(risky)

    # Connect safe -> risky (Unguarded)
    gf.connect("safe", "risky")

    # Add self-loop to risky (Cover gatekeeper.py:219)
    gf.connect("risky", "risky")

    gf.set_entry_point("safe")

    flow = gf.build()

    # Run policy validation
    reports = validate_policy(flow)

    # Check for UNGUARDED violation
    assert any("Policy Violation: Node 'risky'" in r.message for r in reports)


def test_integrity_naive_datetime() -> None:
    """
    Test canonical hashing of naive datetime objects.
    """
    dt = datetime(2023, 1, 1, 12, 0, 0) # Naive
    assert dt.tzinfo is None

    # Should not raise
    h = compute_hash({"time": dt})
    assert h


def test_integrity_merkle_genesis_mismatch() -> None:
    """
    Test verify_merkle_proof with genesis node mismatch against trusted root.
    """
    trace = [
        {"execution_hash": "hash1", "parent_hashes": []}
    ]

    # Correct hash
    computed = compute_hash(trace[0])
    trace[0]["execution_hash"] = computed

    # Mismatch
    result = verify_merkle_proof(trace, trusted_root_hash="wrong_hash")
    assert result is False


def test_integrity_reconstruct_payload_error() -> None:
    """
    Test verify_merkle_proof with invalid node type (integrity.py:161-162).
    """
    # Pass a string instead of dict/model
    trace = ["invalid_node"]
    result = verify_merkle_proof(trace)  # type: ignore[arg-type]
    assert result is False
