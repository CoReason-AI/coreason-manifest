import html
from typing import Any

from coreason_manifest.spec.core.flow import LinearFlow, GraphFlow, Graph
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    SwitchNode,
    PlannerNode,
    HumanNode,
    Placeholder,
    Node,
)

def _escape_id(node_id: str) -> str:
    """Escapes the node ID for Mermaid compatibility."""
    # If the ID contains spaces or special characters, wrap it in quotes.
    # Simple heuristic: if it's not alphanumeric (plus _), quote it.
    if not node_id.replace("_", "").isalnum():
        return f'"{node_id}"'
    return node_id

def _escape_label(text: str) -> str:
    """Escapes text for use in Mermaid labels."""
    return html.escape(text).replace('"', '&quot;')

def _render_node_def(node: Node) -> str:
    """Renders the node definition line for Mermaid."""
    safe_id = _escape_id(node.id)
    label_id = _escape_label(node.id)

    if node.type == "agent":
        return f'{safe_id}["{label_id}<br/>(Agent)"]'
    elif node.type == "switch":
        return f'{safe_id}{{"{label_id}<br/>(Switch)"}}'
    elif node.type == "planner":
        return f'{safe_id}{{{{"{label_id}<br/>(Planner)"}}}}'
    elif node.type == "human":
        return f'{safe_id}[/"{label_id}<br/>(Human)"/]'
    elif node.type == "placeholder":
        return f'{safe_id}("{label_id}<br/>(Placeholder)")'
    else:
        # Fallback for unknown types
        return f'{safe_id}["{label_id}<br/>({node.type})"]'

def to_mermaid(flow: LinearFlow | GraphFlow) -> str:
    """Generates valid Mermaid.js diagram code."""
    lines = []

    if isinstance(flow, LinearFlow):
        lines.append("graph TD")

        # Render nodes
        for node in flow.sequence:
            lines.append(f"    {_render_node_def(node)}")

        # Render implicit edges
        for i in range(len(flow.sequence) - 1):
            source = flow.sequence[i]
            target = flow.sequence[i+1]
            lines.append(f"    {_escape_id(source.id)} --> {_escape_id(target.id)}")

    elif isinstance(flow, GraphFlow):
        lines.append("graph LR")

        # Render nodes from flow.graph.nodes
        for node in flow.graph.nodes.values():
            lines.append(f"    {_render_node_def(node)}")

        # Render edges
        for edge in flow.graph.edges:
            source_id = _escape_id(edge.source)
            target_id = _escape_id(edge.target)
            label = ""

            if edge.condition:
                label = f"|{_escape_label(edge.condition)}|"
            else:
                # Try to infer label from SwitchNode logic
                source_node = flow.graph.nodes.get(edge.source)
                if isinstance(source_node, SwitchNode):
                    # Check cases
                    for case_condition, case_target in source_node.cases.items():
                        if case_target == edge.target:
                            label = f"|{_escape_label(case_condition)}|"
                            break
                    # If not found in cases, check if it's default?
                    # The prompt didn't explicitly ask for default handling but it's good practice.
                    # However, sticking to prompt: "If the edge comes from a SwitchNode, try to match the Edge.target against the node's cases to find the condition string if Edge.condition is missing."
                    pass

            lines.append(f"    {source_id} -->{label} {target_id}")

    # Add styling classes
    lines.append("")
    lines.append("    classDef switch fill:#f96,stroke:#333,stroke-width:2px;")
    lines.append("    classDef human fill:#9cf,stroke:#333,stroke-width:2px;")

    # Apply classes
    # We need to collect IDs for styling
    switch_ids = []
    human_ids = []

    nodes_iter = []
    if isinstance(flow, LinearFlow):
        nodes_iter = flow.sequence
    elif isinstance(flow, GraphFlow):
        nodes_iter = list(flow.graph.nodes.values())

    for node in nodes_iter:
        if node.type == "switch":
            switch_ids.append(_escape_id(node.id))
        elif node.type == "human":
            human_ids.append(_escape_id(node.id))

    if switch_ids:
        lines.append(f"    class {','.join(switch_ids)} switch;")
    if human_ids:
        lines.append(f"    class {','.join(human_ids)} human;")

    return "\n".join(lines)
