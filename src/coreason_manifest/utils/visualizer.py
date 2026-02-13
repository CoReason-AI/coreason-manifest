import html
from typing import Any

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import Node, SwitchNode
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState


def _safe_id(node_id: str) -> str:
    """Sanitizes strings to be valid Mermaid IDs (alphanumeric only)."""
    return node_id.replace("-", "_").replace(" ", "_")


def _escape_label(text: str) -> str:
    """Escapes text for use in Mermaid labels."""
    return html.escape(text).replace('"', "&quot;")


def _get_node_label(node: Node) -> str:
    if node.presentation and node.presentation.label:
        return _escape_label(node.presentation.label)
    return _escape_label(node.id)


def _get_node_shape(node: Node) -> tuple[str, str]:
    # Default shapes
    shape_map = {
        "agent": ("[", "]"),
        "switch": ("{", "}"),
        "planner": ("{{", "}}"),
        "inspector": ("{{", "}}"),
        "emergence_inspector": ("{{", "}}"),
        "human": ("[/", "/]"),
        "placeholder": ("(", ")"),
        "swarm": ("[[", "]]"),
    }
    return shape_map.get(node.type, ("[", "]"))


def _render_mermaid_node(node: Node, snapshot: ExecutionSnapshot | None = None) -> str:
    safe_id = _safe_id(node.id)
    label = _get_node_label(node)

    # Fallback/Enhancement if no explicit presentation label
    if not (node.presentation and node.presentation.label):
         # Convert snake_case to Title Case (e.g. emergence_inspector -> Emergence Inspector)
         type_label = node.type.replace("_", " ").title()
         # Special case for Emergence Inspector if needed, but generic is fine.
         # Legacy used "EmergenceInspectorNode", we stick to clean UI "Emergence Inspector"

         label += f"<br/>({type_label})"
         if node.type == "human" and hasattr(node, "options") and node.options:
             opts = ", ".join(node.options)
             label += f"<br/>[{opts}]"

    shape_start, shape_end = _get_node_shape(node)

    definition = f'{safe_id}{shape_start}"{label}"{shape_end}'

    # Classes
    classes = []

    # Type class
    classes.append(node.type)

    # Runtime State class
    if snapshot and node.id in snapshot.node_states:
        state = snapshot.node_states[node.id]
        classes.append(state.lower())

    if classes:
        definition += ":::" + ":::".join(classes)

    return definition


def to_mermaid(flow: GraphFlow | LinearFlow, snapshot: ExecutionSnapshot | None = None) -> str:
    """Generates valid Mermaid.js diagram code."""
    lines = []

    nodes: list[Node] = []
    edges: list[tuple[str, str, str | None]] = []

    if isinstance(flow, LinearFlow):
        lines.append("graph TD")
        nodes = flow.sequence
        for i in range(len(nodes) - 1):
            edges.append((nodes[i].id, nodes[i+1].id, None))
    elif isinstance(flow, GraphFlow):
        lines.append("graph LR")
        nodes = list(flow.graph.nodes.values())
        edges = [(e.source, e.target, e.condition) for e in flow.graph.edges]
    else:
        return ""

    # Grouping
    grouped_nodes: dict[str, list[Node]] = {}
    ungrouped_nodes: list[Node] = []

    for node in nodes:
        if node.presentation and node.presentation.group:
            g = node.presentation.group
            if g not in grouped_nodes:
                grouped_nodes[g] = []
            grouped_nodes[g].append(node)
        else:
            ungrouped_nodes.append(node)

    # Render Subgraphs
    for group_name, group_nodes in grouped_nodes.items():
        safe_group_name = _safe_id(group_name)
        lines.append(f"    subgraph {safe_group_name} [{_escape_label(group_name)}]")
        for node in group_nodes:
            lines.append(f"        {_render_mermaid_node(node, snapshot)}")
        lines.append("    end")

    # Render Ungrouped Nodes
    for node in ungrouped_nodes:
        lines.append(f"    {_render_mermaid_node(node, snapshot)}")

    # Render Edges
    nodes_dict = {n.id: n for n in nodes}
    for source_id, target_id, condition in edges:
        s_safe = _safe_id(source_id)
        t_safe = _safe_id(target_id)

        label = ""
        if condition:
             label = f"|{_escape_label(condition)}|"
        else:
            # Infer switch label logic
            source_node = nodes_dict.get(source_id)
            if source_node and isinstance(source_node, SwitchNode):
                 for case_cond, case_target in source_node.cases.items():
                     if case_target == target_id:
                         label = f"|{_escape_label(case_cond)}|"
                         break
                 if not label and source_node.default == target_id:
                     label = "|default|"

        lines.append(f"    {s_safe} -->{label} {t_safe}")

    # Styling Classes
    lines.append("")
    lines.append("    %% Styling Classes")
    lines.append("    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;")
    lines.append("    classDef switch fill:#ffcc00,stroke:#333,stroke-width:2px;")
    lines.append("    classDef human fill:#ff9999,stroke:#333,stroke-width:2px;")
    lines.append("    classDef inspector fill:#e8daef,stroke:#8e44ad,stroke-width:2px;")
    lines.append("    classDef emergence_inspector fill:#e8daef,stroke:#8e44ad,stroke-width:2px;")
    lines.append("    classDef swarm fill:#aed6f1,stroke:#2e86c1,stroke-width:2px;")

    # State styles
    lines.append("    classDef running fill:#fcf3cf,stroke:#f1c40f,stroke-width:3px,stroke-dasharray: 5 5;")
    lines.append("    classDef retrying fill:#ffe0b2,stroke:#fb8c00,stroke-width:3px,stroke-dasharray: 5 5;")
    lines.append("    classDef failed fill:#f2d7d5,stroke:#c0392b,stroke-width:2px;")
    lines.append("    classDef completed fill:#d5f5e3,stroke:#2ecc71,stroke-width:2px;")
    lines.append("    classDef skipped fill:#e5e7e9,stroke:#bdc3c7,stroke-dasharray: 2 2;")
    lines.append("    classDef cancelled fill:#e5e7e9,stroke:#bdc3c7,stroke-dasharray: 2 2;")
    lines.append("    classDef pending fill:#ffffff,stroke:#333,stroke-width:1px,stroke-dasharray: 2 2;")

    return "\n".join(lines)


def to_react_flow(flow: GraphFlow | LinearFlow, snapshot: ExecutionSnapshot | None = None) -> dict[str, Any]:
    """Generates React Flow compatible JSON."""
    rf_nodes: list[dict[str, Any]] = []
    rf_edges: list[dict[str, Any]] = []

    nodes: list[Node] = []
    edges: list[tuple[str, str, str | None]] = []

    if isinstance(flow, LinearFlow):
        nodes = flow.sequence
        for i in range(len(nodes) - 1):
            edges.append((nodes[i].id, nodes[i+1].id, None))
    else:
        nodes = list(flow.graph.nodes.values())
        edges = [(e.source, e.target, e.condition) for e in flow.graph.edges]

    for i, node in enumerate(nodes):
        # Basic layouting placeholder.
        # In a real scenario, this might need a DAG layout algorithm (e.g. dagre).
        position = {"x": 0, "y": i * 100}

        node_data = {
            "label": node.id,
            "type": node.type,
            "metadata": node.metadata,
        }

        # Inject Presentation Hints
        if node.presentation:
            node_data["presentation"] = node.presentation.model_dump(exclude_none=True)
            if node.presentation.label:
                node_data["label"] = node.presentation.label

        # Inject Runtime State
        if snapshot and node.id in snapshot.node_states:
            node_data["state"] = snapshot.node_states[node.id]

        rf_nodes.append({
            "id": node.id,
            "type": node.type,
            "position": position,
            "data": node_data,
        })

    for i, (source, target, condition) in enumerate(edges):
        edge_data = {
            "id": f"e{i}",
            "source": source,
            "target": target,
        }
        if condition:
            edge_data["label"] = condition

        rf_edges.append(edge_data)

    return {
        "nodes": rf_nodes,
        "edges": rf_edges
    }
