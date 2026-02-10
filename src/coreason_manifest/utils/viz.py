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
from typing import Any

from coreason_manifest.spec.common.presentation import (
    GraphTheme,
    RuntimeStateSnapshot,
    ViewportMode,
)
from coreason_manifest.spec.v2.definitions import (
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestV2,
    SwitchStep,
)
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    EvaluatorNode,
    GenerativeNode,
    HumanNode,
    RecipeDefinition,
    RouterNode,
    TransparencyLevel,
)

# Default Shape Lookup Table
DEFAULT_SHAPE_MAP = {
    "agent": "rect",
    "human": "hexagon",
    "router": "diamond",
    "evaluator": "stadium",
    "generative": "subprocess",
    "switch": "diamond",
    "council": "subprocess",
    "step": "rect",
}

# Mermaid Syntax Map
MERMAID_SHAPES = {
    "rect": ("[", "]"),
    "diamond": ("{", "}"),
    "hexagon": ("{{", "}}"),
    "stadium": ("([", "])"),
    "subprocess": ("[[", "]]"),
    "circle": ("((", "))"),
}


def _sanitize_id(text: str) -> str:
    """Sanitizes a string for use as a Mermaid node ID."""
    # Replace anything not alphanumeric or underscore with underscore
    return re.sub(r"[^a-zA-Z0-9_]", "_", text)


def _get_shape(node_type: str, theme: GraphTheme | None) -> tuple[str, str, str]:
    """
    Resolve shape for a node type based on theme or defaults.
    Returns: (shape_name, open_char, close_char)
    """
    shape_name = "rect"
    # 1. Theme Override
    if theme and node_type in theme.node_shapes:
        shape_name = theme.node_shapes[node_type]
    # 2. Default Map
    elif node_type in DEFAULT_SHAPE_MAP:
        shape_name = DEFAULT_SHAPE_MAP[node_type]

    # 3. Resolve Chars
    open_char, close_char = MERMAID_SHAPES.get(shape_name, ("[", "]"))
    return shape_name, open_char, close_char


def _generate_recipe_mermaid(
    recipe: RecipeDefinition,
    theme: GraphTheme | None = None,
    state: RuntimeStateSnapshot | None = None,
) -> str:
    """
    Generates a Mermaid.js flowchart string from a RecipeDefinition.
    """
    # 1. Orientation
    orientation = theme.orientation if theme else "TD"
    lines = [f"graph {orientation}"]

    # 2. Styling Definitions
    # Defaults
    styles = {
        "default": "fill:#f9f9f9,stroke:#333,stroke-width:1px",
        "input": "fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
        "agent": "fill:#e3f2fd,stroke:#1565c0,stroke-width:2px",
        "human": "fill:#fff3e0,stroke:#e65100,stroke-width:2px",
        "router": "fill:#f3e5f5,stroke:#4a148c,stroke-width:2px",
        "evaluator": "fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px",
        "generative": "fill:#fce4ec,stroke:#880e4f,stroke-width:2px",
        "term": "fill:#eceff1,stroke:#37474f,stroke-width:2px,rx:10,ry:10",
        # State styles
        "running": "stroke:#ffeb3b,stroke-width:4px,animation:pulse 2s infinite",
        "completed": "stroke:#4caf50,stroke-width:3px",
        "failed": "stroke:#f44336,stroke-width:3px",
        "skipped": "stroke:#9e9e9e,stroke-dasharray: 5 5",
        "pending": "stroke:#bdbdbd,stroke-width:2px,stroke-dasharray: 2 2",
        "magentic": "fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,stroke-dasharray: 5 5",
    }

    # Override with theme
    if theme:
        styles.update(theme.node_styles)

    for name, style in styles.items():
        lines.append(f"classDef {name} {style};")

    # Start Node
    lines.append("START((Start)):::term")

    # Inputs Node
    input_keys = list(recipe.interface.inputs.keys())
    input_label = "Inputs"
    if input_keys:
        input_label += "<br/>" + "<br/>".join(f"- {k}" for k in input_keys)
    lines.append(f'INPUTS["{input_label}"]:::input')

    # Nodes
    callback_name = theme.interaction_callback if theme else "call_interaction_handler"

    for node in recipe.topology.nodes:
        sanitized_id = _sanitize_id(node.id)

        # Resolve Visualization Hints
        display_name = node.id
        viz = node.visualization
        is_magentic = False
        viewport_label = ""

        if viz:
            if viz.display_title:
                display_name = viz.display_title

            if viz.icon:
                display_name = f"{viz.icon} {display_name}"

            if viz.initial_viewport and viz.initial_viewport != ViewportMode.STREAM:
                viewport_label = f"<br/>(View: {viz.initial_viewport})"

            if viz.components:
                for comp in viz.components:
                    if comp.is_mutable:
                        is_magentic = True
                        break

        label = display_name
        style_class = "default"
        is_subgraph = False

        # Determine Type for Lookup
        if isinstance(node, AgentNode):
            node_type = "agent"
            style_class = "agent"
        elif isinstance(node, HumanNode):
            node_type = "human"
            style_class = "human"
        elif isinstance(node, RouterNode):
            node_type = "router"
            style_class = "router"
        elif isinstance(node, EvaluatorNode):
            node_type = "evaluator"
            style_class = "evaluator"
        elif isinstance(node, GenerativeNode):
            node_type = "generative"
            style_class = "generative"
        else:
            node_type = "step"

        # Override style if magentic
        if is_magentic:
            style_class = "magentic"

        # Resolve Shape
        _, shape_open, shape_close = _get_shape(node_type, theme)

        if isinstance(node, AgentNode):
            # Check for inline cognitive profile (Nested Graph)
            if node.cognitive_profile:
                is_subgraph = True
                role = node.cognitive_profile.role

                lines.append(f'subgraph cluster_{sanitized_id} ["{display_name} (Cognitive Profile)"]')
                lines.append(f"  direction {orientation}")

                profile_label = f"Role: {role}"
                if node.cognitive_profile.reasoning_mode:
                    profile_label += f"<br/>Mode: {node.cognitive_profile.reasoning_mode}"

                lines.append(f'  {sanitized_id}["{profile_label}"]:::{style_class}')
                lines.append("end")

            else:
                ref = getattr(node, "agent_ref", "Inline")
                ref_str = f"Draft: {ref.intent}" if hasattr(ref, "intent") else str(ref)
                label = f"{display_name}<br/>(Agent: {ref_str})"

        elif isinstance(node, HumanNode):
            label = f"{display_name}<br/>(Human Input)"

        elif isinstance(node, RouterNode):
            label = f"{display_name}<br/>(Router: {node.input_key})"

        elif isinstance(node, EvaluatorNode):
            label = f"{display_name}<br/>(Evaluator)"

        elif isinstance(node, GenerativeNode):
            label = f"{display_name}<br/>(Generative)"

        if not is_subgraph:
            # Append viewport label if present
            label += viewport_label
            # Escape quotes in label
            safe_label = label.replace('"', "'")
            lines.append(f'{sanitized_id}{shape_open}"{safe_label}"{shape_close}:::{style_class}')

        # Interaction Binding
        if node.interaction and node.interaction.transparency == TransparencyLevel.INTERACTIVE:
            tooltip = f"Interact with {node.id}"
            lines.append(f'click {sanitized_id} {callback_name} "{tooltip}"')

    # End Node
    lines.append("END((End)):::term")

    # Edges: Start -> Inputs -> Entry Point
    lines.append("START --> INPUTS")
    entry_point = recipe.topology.entry_point
    if entry_point:
        lines.append(f"INPUTS --> {_sanitize_id(entry_point)}")
    else:
        lines.append("INPUTS --> END")

    # Topology Edges
    for edge in recipe.topology.edges:
        src = _sanitize_id(edge.source)
        tgt = _sanitize_id(edge.target)
        if edge.condition:
            # Labeled edge
            safe_cond = edge.condition.replace('"', "'")
            lines.append(f'{src} -- "{safe_cond}" --> {tgt}')
        else:
            # Unlabeled edge
            lines.append(f"{src} --> {tgt}")

    # Runtime State Overlay
    if state:
        for node_id, status in state.node_states.items():
            sanitized = _sanitize_id(node_id)
            # Map status enum to classDef name
            # e.g. NodeStatus.RUNNING -> "running"
            if status.value in styles:
                lines.append(f"class {sanitized} {status.value};")

            # TODO: Handle active_path highlighting if needed (e.g. bold edges)

    return "\n".join(lines)


def generate_mermaid_graph(
    agent: ManifestV2 | RecipeDefinition,
    theme: GraphTheme | None = None,
    state: RuntimeStateSnapshot | None = None,
) -> str:
    """
    Generates a Mermaid.js flowchart string from a ManifestV2 (Agent Definition) or RecipeDefinition.
    """
    if isinstance(agent, RecipeDefinition):
        return _generate_recipe_mermaid(agent, theme, state)

    # ManifestV2 Handling
    orientation = theme.orientation if theme else "TD"
    lines = [f"graph {orientation}"]

    # Styling Definitions
    # Defaults
    styles = {
        "input": "fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
        "tool": "fill:#fff3e0,stroke:#e65100,stroke-width:2px",
        "step": "fill:#f3e5f5,stroke:#4a148c,stroke-width:2px",
        "council": "fill:#fce4ec,stroke:#880e4f,stroke-width:2px",
        "term": "fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,rx:10,ry:10",
        # State styles
        "running": "stroke:#ffeb3b,stroke-width:4px,animation:pulse 2s infinite",
        "completed": "stroke:#4caf50,stroke-width:3px",
        "failed": "stroke:#f44336,stroke-width:3px",
        "skipped": "stroke:#9e9e9e,stroke-dasharray: 5 5",
        "pending": "stroke:#bdbdbd,stroke-width:2px,stroke-dasharray: 2 2",
    }

    # Override with theme
    if theme:
        styles.update(theme.node_styles)

    for name, style in styles.items():
        lines.append(f"classDef {name} {style};")

    # Start Node
    lines.append("START((Start)):::term")

    # Inputs Node
    input_keys = list(agent.interface.inputs.keys())
    input_label = "Inputs"
    if input_keys:
        # Mermaid allows HTML-like labels
        input_label += "<br/>" + "<br/>".join(f"- {k}" for k in input_keys)
    lines.append(f'INPUTS["{input_label}"]:::input')

    # Workflow Steps Nodes
    steps = agent.workflow.steps
    for step_id, step in steps.items():
        sanitized_id = _sanitize_id(step_id)
        capability = "Unknown"
        style_class = "step"

        node_type = "step"
        if isinstance(step, AgentStep):
            node_type = "agent"
            capability = step.agent
        elif isinstance(step, LogicStep):
            node_type = "step"  # Logic steps are generic steps
            capability = "Logic"
        elif isinstance(step, CouncilStep):
            node_type = "council"
            capability = "Council"
            style_class = "council"
        elif isinstance(step, SwitchStep):
            node_type = "switch"
            capability = "Switch"

        # Resolve Shape
        _, shape_open, shape_close = _get_shape(node_type, theme)

        lines.append(
            f'STEP_{sanitized_id}{shape_open}"{step_id}<br/>(Call: {capability})"{shape_close}:::{style_class}'
        )

    # End Node
    lines.append("END((End)):::term")

    # Edges: Start -> Inputs
    lines.append("START --> INPUTS")

    # Edges: Inputs -> First Step
    start_step_id = agent.workflow.start
    if start_step_id in steps:
        lines.append(f"INPUTS --> STEP_{_sanitize_id(start_step_id)}")
    else:
        # Fallback if start step is missing/invalid, though schema validation usually catches this
        lines.append("INPUTS --> END")

    # Edges: Step -> Step / End
    for step_id, step in steps.items():
        src = f"STEP_{_sanitize_id(step_id)}"

        if isinstance(step, (AgentStep, LogicStep, CouncilStep)):
            if step.next:
                tgt = f"STEP_{_sanitize_id(step.next)}"
                lines.append(f"{src} --> {tgt}")
            else:
                lines.append(f"{src} --> END")

        elif isinstance(step, SwitchStep):
            for condition, target_id in step.cases.items():
                tgt = f"STEP_{_sanitize_id(target_id)}"
                # Escape quotes in condition for label
                safe_cond = condition.replace('"', "'")
                lines.append(f'{src} -- "{safe_cond}" --> {tgt}')

            if step.default:
                tgt = f"STEP_{_sanitize_id(step.default)}"
                lines.append(f'{src} -- "default" --> {tgt}')
            # If no default and no case matches, flow implicitly stops or errors.
            # Visualizing implicit end for switch is complex, we leave it as open unless mapped.

    # State overlay for ManifestV2
    if state:
        for node_id, status in state.node_states.items():
            sanitized = f"STEP_{_sanitize_id(node_id)}"
            # Map status enum to classDef name
            if status.value in styles:
                lines.append(f"class {sanitized} {status.value};")

    return "\n".join(lines)


def to_graph_json(
    recipe: RecipeDefinition,
    theme: GraphTheme | None = None,
) -> dict[str, Any]:
    """
    Exports the recipe topology as a structured JSON dict for frontend rendering.
    """
    nodes = []

    # Map nodes
    for node in recipe.topology.nodes:
        node_type = node.type
        sanitized_id = _sanitize_id(node.id)

        # Determine Visual Hint (Shape)
        shape_name, _, _ = _get_shape(node_type, theme)

        # Determine Label
        if isinstance(node, AgentNode):
            ref = getattr(node, "agent_ref", "Inline")
            ref_str = f"Draft: {ref.intent}" if hasattr(ref, "intent") else str(ref)
            if node.cognitive_profile:
                ref_str = f"Profile: {node.cognitive_profile.role}"
            label = f"{node.id} ({ref_str})"
        elif isinstance(node, RouterNode):
            label = f"{node.id} (Router: {node.input_key})"
        elif isinstance(node, HumanNode):
            label = f"{node.id}<br/>(Human Input)"
        elif isinstance(node, EvaluatorNode):
            label = f"{node.id}<br/>(Evaluator)"
        elif isinstance(node, GenerativeNode):
            label = f"{node.id}<br/>(Generative)"
        else:
            label = f"{node.id} ({node_type})"

        # Config / Metadata
        config = node.model_dump(exclude={"id", "type"}, mode="json")

        # Presentation
        x: float = 0.0
        y: float = 0.0
        if node.presentation:
            x = node.presentation.x
            y = node.presentation.y

        nodes.append(
            {
                "id": sanitized_id,
                "original_id": node.id,
                "type": node_type,
                "label": label,
                "shape": shape_name,
                "x": x,
                "y": y,
                "config": config,
            }
        )

    # Map edges
    edges = [
        {
            "source": _sanitize_id(edge.source),
            "target": _sanitize_id(edge.target),
            "label": edge.condition,
        }
        for edge in recipe.topology.edges
    ]

    # Implicit edges (Inputs -> Entry)
    if recipe.topology.entry_point:
        edges.append(
            {
                "source": "INPUTS",
                "target": _sanitize_id(recipe.topology.entry_point),
                "label": None,
                "type": "implicit",
            }
        )

    # Add special INPUTS node
    input_keys = list(recipe.interface.inputs.keys())
    nodes.insert(
        0,
        {
            "id": "INPUTS",
            "type": "input",
            "label": "Inputs",
            "shape": "rect",
            "x": 0,
            "y": 0,
            "config": {"inputs": input_keys},
        },
    )

    # Default Theme
    default_theme = GraphTheme().model_dump()
    if theme:
        default_theme.update(theme.model_dump(exclude_unset=True))

    return {"nodes": nodes, "edges": edges, "theme": default_theme}
