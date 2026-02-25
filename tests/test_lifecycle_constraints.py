from typing import Any, cast

import pytest

from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.spec.core.flow import FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, PlaceholderNode
from coreason_manifest.spec.interop.compliance import ErrorCatalog
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
        status=cast("Any", status),
        metadata=FlowMetadata(name="Test Flow", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes=nodes, edges=edges, entry_point=entry_point),
    )


def test_draft_mode_disconnected_safe_nodes() -> None:
    # Setup: 2 disconnected nodes, no entry point, draft mode
    nodes = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        "node2": AgentNode(id="node2", profile=CognitiveProfile(role="assistant", persona="p")),
    }

    flow = create_flow(status="draft", entry_point="node1", nodes=nodes)

    reports = validate_policy(flow)

    # Expect info/warning report about dead code, but NO PRUNING
    orphan_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001]

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
                    model="gpt-4", interaction_mode="native_os", coordinate_system="normalized_0_1"
                ),
            ),
        ),
    }

    flow = create_flow(status="draft", entry_point="node1", nodes=nodes)

    reports = validate_policy(flow)

    # 1. Expect warning about dangerous unreachable node (Topology), but NO PATCH (handled by Red Button)
    risk_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(risk_reports) > 0
    report = risk_reports[0]

    assert report.severity == "warning"
    assert report.remediation is None

    # 2. Expect violation about unguarded dangerous node (Security), WITH PATCH
    sec_reports = [r for r in reports if r.code == ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003]
    assert len(sec_reports) > 0
    sec_report = sec_reports[0]

    assert sec_report.severity == "violation"
    assert sec_report.remediation is not None
    assert sec_report.remediation.type == "add_guard_node"

    # Ensure patch_data is a list
    patch: list[dict[str, Any]]
    if isinstance(sec_report.remediation.patch_data, list):
        patch = sec_report.remediation.patch_data
    else:
        patch = [sec_report.remediation.patch_data]  # Should not happen for this type but for typing sake

    # Should contain add node and add edge
    adds_node = [
        op for op in patch if op["op"] == "add" and "nodes" in str(op["path"]) and "guard_node2" in str(op["path"])
    ]

    assert len(adds_node) > 0


def test_published_mode_missing_entry_point() -> None:
    # Setup: Nodes present but no entry point. Published mode.
    nodes = {"node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p"))}

    # Expect ManifestError now
    with pytest.raises(ManifestError) as excinfo:
        create_flow(status="published", entry_point=None, nodes=nodes)

    # The message in SemanticFault is what we check? Or the error code.
    # ManifestError str() usually contains the message.
    # The error code I used was CRSN-VAL-ENTRY-POINT-MISSING
    assert "CRSN-VAL-ENTRY-POINT-MISSING" in str(excinfo.value)


def test_published_mode_with_placeholder_node() -> None:
    # Setup: Published mode with entry point and one PlaceholderNode
    nodes = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        "placeholder1": PlaceholderNode(id="placeholder1", type="placeholder", required_capabilities=[]),
    }

    with pytest.raises(ManifestError) as excinfo:
        create_flow(status="published", entry_point="node1", nodes=nodes)

    err = excinfo.value
    assert "CRSN-VAL-ABSTRACT-NODE" in str(err)

    # Check that error context contains node_ids list
    node_ids = err.fault.context.get("node_ids", [])
    assert "placeholder1" in node_ids

    # Check patch data
    patch_data = err.fault.context["remediation"]["patch_data"]
    assert len(patch_data) == 1
    assert patch_data[0]["op"] == "replace"
    assert patch_data[0]["path"] == "/graph/nodes/placeholder1"


def test_linear_flow_published_constraints() -> None:
    # Setup: LinearFlow with one PlaceholderNode
    steps = [
        AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        PlaceholderNode(id="placeholder1", type="placeholder", required_capabilities=[]),
    ]

    with pytest.raises(ManifestError) as excinfo:
        LinearFlow(
            metadata=FlowMetadata(name="Linear Test", version="1.0"),
            steps=steps,
            status="published"
        )

    err = excinfo.value
    assert "CRSN-VAL-ABSTRACT-NODE" in str(err)

    # Check patch data
    patch_data = err.fault.context["remediation"]["patch_data"]
    assert len(patch_data) == 1
    assert patch_data[0]["op"] == "replace"
    assert patch_data[0]["path"] == "/sequence/1"
