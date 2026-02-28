from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.core.workflow.flow import GraphFlow
from coreason_manifest.core.workflow.nodes import PlaceholderNode
from coreason_manifest.toolkit.validator import _validate_orphan_nodes


def create_minimal_flow(status: str, include_placeholder: bool = False, include_orphan: bool = False) -> dict[str, Any]:
    nodes: dict[str, Any] = {}
    edges: list[dict[str, Any]] = []

    # Valid entry point
    nodes["start_node"] = {
        "id": "start_node",
        "type": "agent",
        "profile": {"role": "Agent", "persona": "Test"},
        "tools": [],
    }

    if include_placeholder:
        nodes["draft_node"] = {"id": "draft_node", "type": "placeholder", "required_capabilities": ["image_generation"]}
        edges.append({"from_node": "start_node", "to_node": "draft_node"})
    elif not include_orphan:
        nodes["end_node"] = {
            "id": "end_node",
            "type": "agent",
            "profile": {"role": "Agent", "persona": "Test"},
            "tools": [],
        }
        edges.append({"from_node": "start_node", "to_node": "end_node"})

    if include_orphan:
        nodes["orphan_node"] = {
            "id": "orphan_node",
            "type": "agent",
            "profile": {"role": "Orphan", "persona": "Test"},
            "tools": [],
        }

    return {
        "kind": "GraphFlow",
        "type": "graph",
        "status": status,
        "metadata": {"name": "test_flow", "version": "1.0", "description": "Test"},
        "interface": {"inputs": {"json_schema": {}}, "outputs": {"json_schema": {}}},
        "graph": {"nodes": nodes, "edges": edges, "entry_point": "start_node"},
    }


def test_draft_flow_with_placeholder() -> None:
    """Verify that a GraphFlow with a PlaceholderNode parses successfully when status="draft"."""
    data = create_minimal_flow(status="draft", include_placeholder=True)
    flow = GraphFlow.model_validate(data)
    assert flow.status == "draft"
    assert "draft_node" in flow.graph.nodes
    assert isinstance(flow.graph.nodes["draft_node"], PlaceholderNode)


def test_published_flow_with_placeholder_raises_error() -> None:
    """Verify that setting status="published" on a flow with PlaceholderNode raises ValidationError."""
    data = create_minimal_flow(status="published", include_placeholder=True)
    with pytest.raises(ValidationError, match="Published flow contains abstract PlaceholderNode"):
        GraphFlow.model_validate(data)


def test_published_flow_without_entry_point_raises_error() -> None:
    """Verify that setting status="published" on a flow without an entry point raises ValidationError."""
    data = create_minimal_flow(status="published")
    del data["graph"]["entry_point"]
    # Pydantic core structure expects entry_point normally to be optional, but our validator enforces it
    with pytest.raises(ValidationError, match=r"Published GraphFlow MUST have a defined entry_point\."):
        GraphFlow.model_validate(data)


def test_validate_orphan_nodes_lifecycle() -> None:
    """
    Verify _validate_orphan_nodes returns an info report in draft mode,
    but a warning with a remediation patch in published mode.
    """
    # 1. Test Draft Mode
    draft_data = create_minimal_flow(status="draft", include_orphan=True)
    draft_flow = GraphFlow.model_validate(draft_data)

    draft_reports = _validate_orphan_nodes(draft_flow)
    assert len(draft_reports) == 1
    assert draft_reports[0].severity == "info"
    assert "Safe Dead Code" in draft_reports[0].message
    assert draft_reports[0].remediation is None

    # 2. Test Published Mode
    published_data = create_minimal_flow(status="published", include_orphan=True)
    published_flow = GraphFlow.model_validate(published_data)

    published_reports = _validate_orphan_nodes(published_flow)
    assert len(published_reports) == 1
    assert published_reports[0].severity == "warning"
    assert "no incoming edges" in published_reports[0].message
    assert published_reports[0].remediation is not None
    assert published_reports[0].remediation.type == "prune_node"

    # Verify the patch removes the node
    patch = published_reports[0].remediation.patch_data
    assert any(
        isinstance(op, dict)
        and op.get("op") == "remove"
        and isinstance(op.get("path"), str)
        and "orphan_node" in str(op.get("path"))
        for op in patch
    )
