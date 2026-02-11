import html
from typing import Any

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import (
    Node,
    SwitchNode,
)


def _safe_id(node_id: str) -> str:
    """Sanitizes strings to be valid Mermaid IDs (alphanumeric only)."""
    # Replace spaces and hyphens with underscores to avoid Mermaid syntax errors.
    # Also handle other potential problematic chars if needed, but per instructions:
    return node_id.replace("-", "_").replace(" ", "_")


def _escape_label(text: str) -> str:
    """Escapes text for use in Mermaid labels."""
    return html.escape(text).replace('"', "&quot;")


def _render_node_def(node: Node) -> str:
    """Renders the node definition line for Mermaid."""
    safe_id = _safe_id(node.id)
    label_id = _escape_label(node.id)

    if node.type == "agent":
        return f'{safe_id}["{label_id}<br/>(Agent)"]'
    if node.type == "switch":
        return f'{safe_id}{{"{label_id}<br/>(Switch)"}}'
    if node.type == "planner":
        return f'{safe_id}{{{{"{label_id}<br/>(Planner)"}}}}'
    if node.type == "human":
        return f'{safe_id}[/"{label_id}<br/>(Human)"/]'
    if node.type == "placeholder":
        return f'{safe_id}("{label_id}<br/>(Placeholder)")'
    # Fallback for unknown types
    return f'{safe_id}["{label_id}<br/>({node.type})"]'


def to_mermaid(flow: LinearFlow | GraphFlow) -> str:
    """Generates valid Mermaid.js diagram code."""
    lines: list[str] = []

    if isinstance(flow, LinearFlow):
        lines.append("graph TD")

        # Render nodes
        lines.extend(f"    {_render_node_def(node)}" for node in flow.sequence)

        # Render implicit edges
        for i in range(len(flow.sequence) - 1):
            source = flow.sequence[i]
            target = flow.sequence[i + 1]
            lines.append(f"    {_safe_id(source.id)} --> {_safe_id(target.id)}")

    elif isinstance(flow, GraphFlow):
        lines.append("graph LR")

        # Render nodes from flow.graph.nodes
        lines.extend(f"    {_render_node_def(node)}" for node in flow.graph.nodes.values())

        # Render edges
        for edge in flow.graph.edges:
            source_id = _safe_id(edge.source)
            target_id = _safe_id(edge.target)
            label_text = edge.condition

            if not label_text:
                # Try to infer label from SwitchNode logic
                source_node = flow.graph.nodes.get(edge.source)
                if isinstance(source_node, SwitchNode):
                    # Check cases
                    for case_condition, case_target in source_node.cases.items():
                        if case_target == edge.target:
                            label_text = case_condition
                            break
                    # Check default
                    if not label_text and source_node.default == edge.target:
                        label_text = "default"

            label = f"|{_escape_label(label_text)}|" if label_text else ""
            lines.append(f"    {source_id} -->{label} {target_id}")

    # Add styling classes
    lines.append("")
    lines.append("    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;")
    lines.append("    classDef switch fill:#ffcc00,stroke:#333,stroke-width:2px;")
    lines.append("    classDef human fill:#ff9999,stroke:#333,stroke-width:2px;")

    # Apply classes
    # We need to collect IDs for styling
    switch_ids = []
    human_ids = []

    nodes_iter: list[Any] = []
    if isinstance(flow, LinearFlow):
        nodes_iter = flow.sequence
    elif isinstance(flow, GraphFlow):
        nodes_iter = list(flow.graph.nodes.values())

    for node in nodes_iter:
        if node.type == "switch":
            switch_ids.append(_safe_id(node.id))
        elif node.type == "human":
            human_ids.append(_safe_id(node.id))

    if switch_ids:
        lines.append(f"    class {','.join(switch_ids)} switch;")
    if human_ids:
        lines.append(f"    class {','.join(human_ids)} human;")

    return "\n".join(lines)
