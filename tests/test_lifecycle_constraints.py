
from typing import Any, cast

import pytest
from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.spec.core.flow import FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.interop.compliance import ErrorCatalog, RemediationAction
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.gatekeeper import validate_policy

def create_flow(
    status: str = "draft",
    entry_point: str | None = None,
    nodes: dict[str, Any] | None = None,
    edges: list[Any] | None = None,
) -> GraphFlow:
    if nodes is None:
        nodes = {}
    if edges is None:
        edges = []

    return GraphFlow(
        status=cast(Any, status),
        metadata=FlowMetadata(name="Test Flow", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(
            nodes=nodes,
            edges=edges,
            entry_point=entry_point
        )
    )

def test_draft_mode_disconnected_safe_nodes() -> None:
    # Setup: 2 disconnected nodes, no entry point, draft mode
    nodes = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        "node2": AgentNode(id="node2", profile=CognitiveProfile(role="assistant", persona="p"))
    }

    flow = create_flow(status="draft", entry_point="node1", nodes=nodes)

    reports = validate_policy(flow)

    # Expect info/warning report about dead code, but NO PRUNING
    orphan_reports = [
        r for r in reports
        if r.code == ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001
    ]

    assert len(orphan_reports) > 0
    report = orphan_reports[0]

    assert report.severity == "info"
    assert report.remediation is None

def test_draft_mode_disconnected_dangerous_node() -> None:
    # Setup: 1 safe node, 1 dangerous node (disconnected)
    nodes = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        "node2": AgentNode(
            id="node2",
            profile=CognitiveProfile(
                role="hacker",
                persona="p",
                reasoning=ComputerUseReasoning(
                    model="gpt-4",
                    interaction_mode="native_os",
                    coordinate_system="normalized_0_1"
                )
            )
        )
    }

    flow = create_flow(status="draft", entry_point="node1", nodes=nodes)

    reports = validate_policy(flow)

    # Expect warning about dangerous unreachable node, and Guard Injection patch
    risk_reports = [
        r for r in reports
        if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003
    ]
    assert len(risk_reports) > 0
    report = risk_reports[0]

    assert report.severity == "warning"
    assert report.remediation is not None
    assert report.remediation.type == "add_guard_node"

    # Ensure patch_data is a list
    patch: list[dict[str, Any]]
    if isinstance(report.remediation.patch_data, list):
        patch = report.remediation.patch_data
    else:
        patch = [report.remediation.patch_data] # Should not happen for this type but for typing sake

    # Should contain add node and add edge
    adds_node = [
        op for op in patch
        if op["op"] == "add"
        and "nodes" in str(op["path"])
        and "guard_node2" in str(op["path"])
    ]
    adds_edge = [
        op for op in patch
        if op["op"] == "add" and "edges" in str(op["path"])
    ]

    assert len(adds_node) > 0
    assert len(adds_edge) > 0

def test_published_mode_missing_entry_point() -> None:
    # Setup: Nodes present but no entry point. Published mode.
    nodes = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p"))
    }

    # Expect ManifestError now
    with pytest.raises(ManifestError) as excinfo:
        create_flow(status="published", entry_point=None, nodes=nodes)

    # The message in SemanticFault is what we check? Or the error code.
    # ManifestError str() usually contains the message.
    # The error code I used was CRSN-VAL-ENTRY-POINT-MISSING
    assert "CRSN-VAL-ENTRY-POINT-MISSING" in str(excinfo.value)
