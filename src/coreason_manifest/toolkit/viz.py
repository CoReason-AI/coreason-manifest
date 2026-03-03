# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re

from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow
from coreason_manifest.core.workflow.topology import get_unified_topology


def _sanitize_string(text: str | None) -> str:
    """Sanitize strings for Mermaid.js by stripping malicious or layout-breaking characters."""
    if text is None:
        return ""
    # Strip quotes, brackets, greater/less than, semi-colons, ampersands
    return re.sub(r'["\[\]<>;&]', "", text)


def _map_shape(node_type: str, safe_id: str, safe_label: str) -> str:
    """Map node types to Mermaid shapes."""
    if node_type == "agent":
        # Rect
        return f"{safe_id}[{safe_label}]"
    if node_type == "human":
        # Hexagon
        return f"{safe_id}{{{{{safe_label}}}}}"
    if node_type == "swarm":
        # Subprocess
        return f"{safe_id}[[{safe_label}]]"
    if node_type == "switch":
        # Diamond
        return f"{safe_id}{{{safe_label}}}"
    if node_type in ("inspector", "emergence_inspector", "visual_inspector"):
        # Stadium
        return f"{safe_id}([{safe_label}])"
    # Default Round Rect
    return f"{safe_id}({safe_label})"


def flow_to_mermaid(flow: GraphFlow | LinearFlow) -> str:
    """Compile a Pydantic AST into a deterministic Mermaid.js string."""
    nodes, edges = get_unified_topology(flow)

    # Sort deterministically
    sorted_nodes = sorted(nodes, key=lambda n: n.id)
    sorted_edges = sorted(edges, key=lambda e: (e.from_node, e.to_node))

    lines = ["graph TD"]

    # Add nodes
    for node in sorted_nodes:
        safe_id = _sanitize_string(node.id)
        # Fallback label to safe_id if label not present or empty
        safe_label = _sanitize_string(getattr(node, "label", node.id) or node.id)

        node_str = _map_shape(node.type, safe_id, safe_label)
        lines.append(f"    {node_str}")

    # Add edges
    for edge in sorted_edges:
        safe_from = _sanitize_string(edge.from_node)
        safe_to = _sanitize_string(edge.to_node)
        lines.append(f"    {safe_from} --> {safe_to}")

    return "\n".join(lines)
