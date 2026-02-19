from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from coreason_manifest.spec.core.engines import ComputerUseReasoning, StandardReasoning
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
from coreason_manifest.utils.integrity import _recursive_sort_and_sanitize, compute_hash

# --- Mocks for Flow ---


def create_mock_flow(nodes_list: list[AnyNode], edges_list: list[tuple[str, str]]) -> GraphFlow:
    return GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=Blackboard(variables={}, persistence=False),
        graph=Graph(nodes={n.id: n for n in nodes_list}, edges=[Edge(source=s, target=t) for s, t in edges_list]),
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
    # island1 is unsafe and unreachable. island2 is safe and unreachable (no error for island2).

    unsafe_errors = [r for r in topology_errors if r.node_id == "island1"]
    assert len(unsafe_errors) == 1
    assert "computer_use" in unsafe_errors[0].message


def test_telemetry_request_auto_rooting() -> None:
    """
    Test AgentRequest auto-rooting logic.
    """
    # Case A: No root, no parent -> Auto-promote
    req = AgentRequest(agent_id="test", inputs={})
    assert req.request_id is not None
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None

    # Case C: Parent and Root -> OK
    parent_id = str(uuid4())
    root_id = str(uuid4())
    req2 = AgentRequest(agent_id="test", inputs={}, parent_request_id=parent_id, root_request_id=root_id)
    assert req2.parent_request_id == parent_id
    assert req2.root_request_id == root_id


def test_telemetry_request_orphaned_trace() -> None:
    """
    Test AgentRequest orphaned trace detection.
    """
    # Case B: Parent but no root -> Error
    with pytest.raises(ValueError, match="Orphaned trace detected"):
        AgentRequest(
            agent_id="test",
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

    sanitized = _recursive_sort_and_sanitize(data)

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
