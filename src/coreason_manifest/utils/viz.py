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
    HumanNode,
    RecipeDefinition,
    RouterNode,
)


def _sanitize_id(text: str) -> str:
    """Sanitizes a string for use as a Mermaid node ID."""
    # Replace anything not alphanumeric or underscore with underscore
    return re.sub(r"[^a-zA-Z0-9_]", "_", text)


def generate_mermaid_graph(agent: ManifestV2) -> str:
    """
    Generates a Mermaid.js flowchart string from a ManifestV2 (Agent Definition).
    """
    lines = ["graph TD"]

    # Styling Definitions
    lines.append("classDef input fill:#e1f5fe,stroke:#01579b,stroke-width:2px;")
    lines.append("classDef tool fill:#fff3e0,stroke:#e65100,stroke-width:2px;")
    lines.append("classDef step fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;")
    lines.append("classDef term fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,rx:10,ry:10;")

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
        if isinstance(step, AgentStep):
            capability = step.agent
        elif isinstance(step, LogicStep):
            capability = "Logic"
        elif isinstance(step, CouncilStep):
            capability = "Council"
        elif isinstance(step, SwitchStep):
            capability = "Switch"

        lines.append(f'STEP_{sanitized_id}["{step_id}<br/>(Call: {capability})"]:::step')

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

    return "\n".join(lines)


def generate_recipe_mermaid(recipe: RecipeDefinition) -> str:
    """
    Generates a Mermaid.js flowchart string from a RecipeDefinition.
    """
    lines = ["flowchart TD"]

    # 1. Define Nodes
    for node in recipe.topology.nodes:
        node_id = _sanitize_id(node.id)

        # Determine Label
        label = node.id
        if node.presentation and node.presentation.label:
            label = node.presentation.label

        # Escape quotes in label
        label = label.replace('"', "'")

        # Determine Shape based on Type
        if isinstance(node, AgentNode):
            # Rectangular box: [Label]
            lines.append(f'{node_id}["{label}"]')
        elif isinstance(node, HumanNode):
            # Rounded box: (Label)
            lines.append(f'{node_id}("{label}")')
        elif isinstance(node, RouterNode):
            # Rhombus: {Label}
            lines.append(f'{node_id}{{"{label}"}}')
        elif isinstance(node, EvaluatorNode):
            # Hexagon: {{Label}} (Use double braces for hexagon shape in Mermaid)
            lines.append(f'{node_id}{{{{"{label}"}}}}')
        else:
            # Fallback
            lines.append(f'{node_id}["{label}"]')

    # 2. Define Entry Point
    entry_point = _sanitize_id(recipe.topology.entry_point)
    lines.append(f"Start((Start)) --> {entry_point}")

    # 3. Define Explicit Edges
    for edge in recipe.topology.edges:
        src = _sanitize_id(edge.source)
        tgt = _sanitize_id(edge.target)
        if edge.condition:
            cond = edge.condition.replace('"', "'")
            lines.append(f"{src} -->|{cond}| {tgt}")
        else:
            lines.append(f"{src} --> {tgt}")

    # 4. Define Implicit Router/Evaluator Logic
    # We iterate nodes again to find Routers and Evaluators and add their implicit edges
    for node in recipe.topology.nodes:
        src = _sanitize_id(node.id)

        if isinstance(node, RouterNode):
            # Routes
            for value, target_id in node.routes.items():
                tgt = _sanitize_id(target_id)
                val = value.replace('"', "'")
                lines.append(f"{src} -->|{val}| {tgt}")
            # Default Route
            default_tgt = _sanitize_id(node.default_route)
            lines.append(f"{src} -->|else| {default_tgt}")

        elif isinstance(node, EvaluatorNode):
            # Pass Route
            pass_tgt = _sanitize_id(node.pass_route)
            lines.append(f"{src} -->|pass| {pass_tgt}")
            # Fail Route
            fail_tgt = _sanitize_id(node.fail_route)
            lines.append(f"{src} -->|fail| {fail_tgt}")

    # 5. Apply Styles
    for node in recipe.topology.nodes:
        if node.presentation and node.presentation.color:
            node_id = _sanitize_id(node.id)
            color = node.presentation.color
            lines.append(f"style {node_id} fill:{color},stroke:#333,stroke-width:2px")

    return "\n".join(lines)
