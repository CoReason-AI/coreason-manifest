from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from coreason_manifest.spec.core.engines import (
    CodeExecutionReasoning,
    ComputerUseReasoning,
    StandardReasoning,
)
from coreason_manifest.spec.core.flow import (
    AnyNode,
    Blackboard,
    DataSchema,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.interop.compliance import ComplianceReport, ErrorCatalog, legacy_error_adapter
from coreason_manifest.spec.interop.request import AgentRequest
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.integrity import CanonicalV2Strategy, compute_hash, reconstruct_payload

# --- Mocks for Flow ---


def create_mock_flow(nodes_list: list[AnyNode], edges_list: list[tuple[str, str]]) -> GraphFlow:
    entry_point = nodes_list[0].id if nodes_list else "unknown"
    # Use "draft" status to allow unreachable nodes during testing of Gatekeeper policy.
    # "published" flows enforce strict DAG reachability via validate_dag.
    # Use model_construct for Graph to allow cycles/invalid topology during policy testing
    return GraphFlow.model_construct(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=Blackboard(variables={}, persistence=False),
        graph=Graph.model_construct(
            nodes={n.id: n for n in nodes_list},
            edges=[Edge(source=s, target=t) for s, t in edges_list],
            entry_point=entry_point,
        ),
    )


# --- HELPER FACTORIES ---


def create_safe_profile() -> CognitiveProfile:
    return CognitiveProfile(
        role="tester", persona="safe", reasoning=StandardReasoning(model="gpt-4-turbo"), fast_path=None
    )


def create_unsafe_profile() -> CognitiveProfile:
    return CognitiveProfile(
        role="hacker", persona="unsafe", reasoning=ComputerUseReasoning(model="claude-3-5-sonnet"), fast_path=None
    )


def create_code_exec_profile() -> CognitiveProfile:
    return CognitiveProfile(
        role="coder",
        persona="unsafe_coder",
        reasoning=CodeExecutionReasoning(model="gpt-4", allow_network=True, timeout_seconds=10),
        fast_path=None,
    )


# --- TESTS ---


def test_topology_utility_island_safe() -> None:
    """
    Test that a disconnected node with standard capabilities is ALLOWED.
    """
    node_main = AgentNode(id="main", type="agent", metadata={}, profile=create_safe_profile(), tools=[])
    node_island = AgentNode(id="island", type="agent", metadata={}, profile=create_safe_profile(), tools=[])  # Safe

    # Graph: main (entry), island (disconnected)
    flow = create_mock_flow([node_main, node_island], [])

    reports = validate_policy(flow)

    # Should be no topology errors (maybe domain errors if not mocked, but here no tools)
    topology_errors = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(topology_errors) == 0


def test_topology_utility_island_unsafe() -> None:
    """
    Test that a disconnected node with HIGH RISK capabilities is BLOCKED.
    To be truly "unreachable", it must not be an entry node (in-degree > 0) but not reachable from valid entries.
    So we create a cycle: island1 -> island2 -> island1.
    """
    node_main = AgentNode(id="main", type="agent", metadata={}, profile=create_safe_profile(), tools=[])
    node_island1 = AgentNode(
        id="island1", type="agent", metadata={}, profile=create_unsafe_profile(), tools=[]
    )  # Unsafe
    node_island2 = AgentNode(id="island2", type="agent", metadata={}, profile=create_safe_profile(), tools=[])

    edges = [("island1", "island2"), ("island2", "island1")]

    # Graph: main (entry), island1<->island2 (cycle, no entry)
    flow = create_mock_flow([node_main, node_island1, node_island2], edges)

    reports = validate_policy(flow)

    topology_errors = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(topology_errors) >= 1
    # island1 is unsafe and unreachable. island2 is safe and unreachable.
    # New logic: aggregated into one report.
    report = topology_errors[0]
    assert "island1" in report.details["dangerous_nodes"]
    assert "island2" in report.details["safe_nodes"]
    assert "computer_use" in report.details["risk_details"]["island1"]


def test_telemetry_request_auto_rooting() -> None:
    """
    Test AgentRequest auto-rooting logic.
    """
    # Case A: No root, no parent -> Auto-promote
    req = AgentRequest(agent_id="test", session_id="s1", inputs={})
    assert req.request_id is not None
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None

    # Case C: Parent and Root -> OK
    parent_id = str(uuid4())
    root_id = str(uuid4())
    req2 = AgentRequest(
        agent_id="test", session_id="s1", inputs={}, parent_request_id=parent_id, root_request_id=root_id
    )
    assert req2.parent_request_id == parent_id
    assert req2.root_request_id == root_id


def test_telemetry_request_create_child() -> None:
    """
    Test create_child factory method.
    """
    req = AgentRequest(agent_id="root", session_id="s1", inputs={})
    child = req.create_child(metadata={"step": 1})

    assert child.request_id != req.request_id
    assert child.parent_request_id == req.request_id
    assert child.root_request_id == req.root_request_id
    assert child.session_id == req.session_id
    assert child.metadata["step"] == 1


def test_telemetry_request_orphaned_trace() -> None:
    """
    Test AgentRequest orphaned trace detection.
    """
    # Case B: Parent but no root -> Error
    with pytest.raises(ValueError, match="Broken Lineage"):
        AgentRequest(
            agent_id="test",
            session_id="s1",
            inputs={},
            parent_request_id="some-parent",
            # root_request_id missing
        )


def test_telemetry_node_execution_trace_validation() -> None:
    """
    Test NodeExecution trace validation.
    """
    ts = datetime.now(UTC)
    # Success case
    NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=ts,
        duration_ms=10,
        request_id="req1",
        parent_request_id="p1",
        root_request_id="r1",
    )

    # Failure case
    with pytest.raises(ValueError, match="Orphaned trace detected"):
        NodeExecution(
            node_id="n1",
            state=NodeState.COMPLETED,
            inputs={},
            outputs={},
            timestamp=ts,
            duration_ms=10,
            request_id="req1",
            parent_request_id="p1",
            root_request_id=None,
        )


def test_integrity_sanitization() -> None:
    """
    Verify hash sanitization rules.
    """
    dt = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=UTC)

    data: dict[str, Any] = {
        "b": 2,
        "a": 1,
        "integrity_hash": "legacy",
        "execution_hash": "modern",
        "signature": "sig",
        "__private": "secret",
        "nested": {"d": 4, "c": 3, "execution_hash": "nested_bad", "timestamp": dt},
    }

    strategy = CanonicalV2Strategy()
    sanitized = strategy._recursive_sort_and_sanitize(data)

    # Check stripped keys
    assert "integrity_hash" not in sanitized
    assert "execution_hash" not in sanitized
    assert "signature" not in sanitized
    assert "__private" not in sanitized
    assert "execution_hash" not in sanitized["nested"]

    # Check sorting (implicitly by keys being ordered in output, but hard to assert on dict)
    # Compute hash of original vs manual sanitized should match

    # Check timestamp
    assert sanitized["nested"]["timestamp"] == "2023-01-01T12:00:00Z"

    # Check UUID fast-path
    uid = uuid4()
    data_uuid = {"id": uid}
    sanitized_uuid = strategy._recursive_sort_and_sanitize(data_uuid)
    assert sanitized_uuid["id"] == str(uid)

    # Determinism check
    h1 = compute_hash(data)

    data_reordered = {
        "a": 1,
        "b": 2,
        "nested": {"c": 3, "d": 4, "timestamp": dt},
        "integrity_hash": "different",  # Should be stripped
    }
    h2 = compute_hash(data_reordered)

    assert h1 == h2


def test_compliance_legacy_adapter() -> None:
    """
    Verify LegacyErrorAdapter.
    """
    report = ComplianceReport(
        code=ErrorCatalog.ERR_SEC_DOMAIN_BLOCKED_002,
        severity="violation",
        message="Blocked domain",
        details={"domain": "bad.com", "tool_name": "curl"},
        remediation=None,
    )

    # Modern consumer
    json_out = legacy_error_adapter(report, consumer_version="v0.25.0")
    assert "ERR_SEC_DOMAIN_BLOCKED_002" in json_out

    # Legacy consumer
    legacy_out = legacy_error_adapter(report, consumer_version="v0.24.0")
    assert legacy_out == "Tool 'curl' uses blocked domain: bad.com"


def test_compliance_legacy_adapter_extended() -> None:
    """Cover all branches of legacy_error_adapter."""
    # 1. ERR_SEC_UNGUARDED_CRITICAL_003
    report_unguarded = ComplianceReport(
        code=ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003,
        severity="violation",
        message="msg",
        node_id="n1",
        details={"reason": "bad stuff"},
    )
    assert "Policy Violation: Node 'n1' requires" in legacy_error_adapter(report_unguarded, "v0.24.0")

    # 2. ERR_TOPOLOGY_UNREACHABLE_RISK_003
    report_topo = ComplianceReport(
        code=ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003,
        severity="violation",
        message="msg",
        node_id="n2",
        details={"reason": "risky"},
    )
    assert "Topology Violation: Node 'n2' is unreachable" in legacy_error_adapter(report_topo, "v0.24.0")

    # 3. Fallback
    report_other = ComplianceReport(
        code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001,
        severity="warning",
        message="missing tool",
        node_id="n3",
    )
    assert "Warning: missing tool (Code: ERR_CAP_MISSING_TOOL_001)" in legacy_error_adapter(report_other, "v0.24.0")


def test_topology_utility_island_acyclic_unsafe() -> None:
    """
    Test a node downstream of a cycle (unreachable tail).
    Exercises line 284 in gatekeeper.py (structure_type="island").
    Graph: Safe1 <-> Safe2 -> Unsafe
    """
    node_safe1 = AgentNode(id="safe1", type="agent", metadata={}, profile=create_safe_profile(), tools=[])
    node_safe2 = AgentNode(id="safe2", type="agent", metadata={}, profile=create_safe_profile(), tools=[])
    node_unsafe = AgentNode(id="unsafe", type="agent", metadata={}, profile=create_unsafe_profile(), tools=[])

    edges = [("safe1", "safe2"), ("safe2", "safe1")]

    flow = create_mock_flow([node_safe1, node_safe2, node_unsafe], edges)

    reports = validate_policy(flow)

    # We expect multiple errors:
    # 1. Unguarded critical (because no entry point -> fail closed default)
    # 2. Topology unreachable risk

    topo_errors = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(topo_errors) == 1

    # SOTA Fix: Aggregated reporting
    report = topo_errors[0]
    assert "unsafe" in report.details["dangerous_nodes"]
    assert report.details["risk_details"]["unsafe"] is not None


def test_integrity_reconstruct_payload_fallback() -> None:
    """Cover the fallback case in reconstruct_payload (line 105)."""
    # reconstruct_payload(dict) returns dict.
    # reconstruct_payload(BaseModel) returns model_dump.
    # reconstruct_payload(other) returns dict(other).

    # We pass a list of tuples which dict() accepts.
    obj = [("a", 1), ("b", 2)]
    res = reconstruct_payload(obj)
    assert res == {"a": 1, "b": 2}


def test_topology_utility_island_code_exec() -> None:
    """
    Test unreachable island with code_execution capability.
    Exercises line 284 in gatekeeper.py.
    """
    node_safe1 = AgentNode(id="safe1", type="agent", metadata={}, profile=create_safe_profile(), tools=[])
    node_safe2 = AgentNode(id="safe2", type="agent", metadata={}, profile=create_safe_profile(), tools=[])
    node_unsafe = AgentNode(
        id="code_island",
        type="agent",
        metadata={},
        profile=create_code_exec_profile(),
        tools=[],
    )

    edges = [("safe1", "safe2"), ("safe2", "safe1")]

    flow = create_mock_flow([node_safe1, node_safe2, node_unsafe], edges)

    reports = validate_policy(flow)
    # Expect error about code_execution
    topo_errors = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(topo_errors) == 1
    assert "code_island" in topo_errors[0].details["dangerous_nodes"]
    assert "code_execution" in topo_errors[0].details["risk_details"]["code_island"]
