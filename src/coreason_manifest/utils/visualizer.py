import html

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import Node, SwitchNode
from coreason_manifest.spec.interop.telemetry import ExecutionSnapshot, NodeState


def _safe_id(node_id: str) -> str:
    """Sanitizes strings to be valid Mermaid IDs (alphanumeric only)."""
    return node_id.replace("-", "_").replace(" ", "_")


def _escape_label(text: str) -> str:
    """Escapes text for use in Mermaid labels."""
    return html.escape(text).replace('"', "&quot;")


def _get_state_class(state: NodeState) -> str | None:
    match state:
        case NodeState.RUNNING:
            return "running"
        case NodeState.RETRYING:
            return "retrying"
        case NodeState.FAILED | NodeState.CANCELLED:
            return "failed"
        case NodeState.COMPLETED:
            return "completed"
        case NodeState.SKIPPED:
            return "skipped"
        case _:
            return None


def _render_node_def(node: Node, snapshot: ExecutionSnapshot | None) -> str:
    """Renders the node definition line for Mermaid with optional state styling."""
    safe_id = _safe_id(node.id)
    label_id = _escape_label(node.id)

    # Determine shape based on type
    if node.type == "agent":
        shape_start, shape_end = "[", "]"
        label_suffix = "<br/>(Agent)"
    elif node.type == "switch":
        shape_start, shape_end = "{", "}"
        label_suffix = "<br/>(Switch)"
    elif node.type == "planner":
        shape_start, shape_end = "{{", "}}"
        label_suffix = "<br/>(Planner)"
    elif node.type == "human":
        shape_start, shape_end = "[/", "/]"
        label_suffix = "<br/>(Human)"
    elif node.type == "placeholder":
        shape_start, shape_end = "(", ")"
        label_suffix = "<br/>(Placeholder)"
    else:
        shape_start, shape_end = "[", "]"
        label_suffix = f"<br/>({node.type})"

    definition = f'{safe_id}{shape_start}"{label_id}{label_suffix}"{shape_end}'

    # Apply state styling if snapshot is provided
    if snapshot and node.id in snapshot.node_states:
        state = snapshot.node_states[node.id]
        class_name = _get_state_class(state)
        if class_name:
            definition += f":::{class_name}"

    return definition


def to_mermaid(flow: LinearFlow | GraphFlow, snapshot: ExecutionSnapshot | None = None) -> str:
    """Generates valid Mermaid.js diagram code."""
    lines: list[str] = []

    if isinstance(flow, LinearFlow):
        lines.append("graph TD")
        nodes = flow.sequence

        # Render nodes
        lines.extend(f"    {_render_node_def(node, snapshot)}" for node in nodes)

        # Render implicit edges
        for i in range(len(nodes) - 1):
            source = nodes[i]
            target = nodes[i + 1]
            lines.append(f"    {_safe_id(source.id)} --> {_safe_id(target.id)}")

    elif isinstance(flow, GraphFlow):
        lines.append("graph LR")
        nodes_dict = flow.graph.nodes

        # Render nodes
        lines.extend(f"    {_render_node_def(node, snapshot)}" for node in nodes_dict.values())

        # Render edges
        for edge in flow.graph.edges:
            source_id = _safe_id(edge.source)
            target_id = _safe_id(edge.target)
            label_text = edge.condition

            if not label_text:
                # Try to infer label from SwitchNode logic
                source_node = nodes_dict.get(edge.source)
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
    lines.append("    %% Styling Classes")
    # Active (Pulse effect simulated with dashed border for compatibility)
    lines.append("    classDef running fill:#fcf3cf,stroke:#f1c40f,stroke-width:3px,stroke-dasharray: 5 5;")
    # Retrying (Orange/Warning)
    lines.append("    classDef retrying fill:#ffe0b2,stroke:#fb8c00,stroke-width:3px,stroke-dasharray: 5 5;")
    lines.append("    classDef failed fill:#f2d7d5,stroke:#c0392b,stroke-width:2px;")  # Red/Alert
    lines.append("    classDef completed fill:#d5f5e3,stroke:#2ecc71,stroke-width:2px;")  # Green/Success
    lines.append("    classDef skipped fill:#e5e7e9,stroke:#bdc3c7,stroke-dasharray: 2 2;")  # Grey/Dashed

    return "\n".join(lines)
