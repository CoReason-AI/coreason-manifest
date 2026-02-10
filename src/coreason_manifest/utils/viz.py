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
    GenerativeNode,
    HumanNode,
    RecipeDefinition,
    RouterNode,
)


def _sanitize_id(text: str) -> str:
    """Sanitizes a string for use as a Mermaid node ID."""
    # Replace anything not alphanumeric or underscore with underscore
    return re.sub(r"[^a-zA-Z0-9_]", "_", text)


def _generate_recipe_mermaid(recipe: RecipeDefinition) -> str:
    """
    Generates a Mermaid.js flowchart string from a RecipeDefinition.
    """
    lines = ["graph TD"]

    # Styling Definitions
    # Consistent color palette but adapted for Recipe nodes
    lines.append("classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;")
    lines.append("classDef input fill:#e1f5fe,stroke:#01579b,stroke-width:2px;")  # Light Blue
    lines.append("classDef agent fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;")  # Blue
    lines.append("classDef human fill:#fff3e0,stroke:#e65100,stroke-width:2px;")  # Orange
    lines.append("classDef router fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;")  # Purple
    lines.append("classDef evaluator fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;")  # Green
    lines.append("classDef generative fill:#fce4ec,stroke:#880e4f,stroke-width:2px;")  # Pink
    lines.append("classDef term fill:#eceff1,stroke:#37474f,stroke-width:2px,rx:10,ry:10;")  # Grey

    # Start Node
    lines.append("START((Start)):::term")

    # Inputs Node
    input_keys = list(recipe.interface.inputs.keys())
    input_label = "Inputs"
    if input_keys:
        input_label += "<br/>" + "<br/>".join(f"- {k}" for k in input_keys)
    lines.append(f'INPUTS["{input_label}"]:::input')

    # Nodes
    for node in recipe.topology.nodes:
        sanitized_id = _sanitize_id(node.id)
        label = node.id
        style_class = "default"
        shape_open = "["
        shape_close = "]"

        if isinstance(node, AgentNode):
            # Agent Node: Box
            style_class = "agent"
            ref = getattr(node, "agent_ref", "Inline")
            if hasattr(ref, "intent"):  # SemanticRef
                ref_str = f"Draft: {ref.intent}"
            else:
                ref_str = str(ref)
            label = f"{node.id}<br/>(Agent: {ref_str})"

        elif isinstance(node, HumanNode):
            # Human Node: Hexagon {{ }}
            style_class = "human"
            shape_open = "{{"
            shape_close = "}}"
            label = f"{node.id}<br/>(Human Input)"

        elif isinstance(node, RouterNode):
            # Router Node: Rhombus { }
            style_class = "router"
            shape_open = "{"
            shape_close = "}"
            label = f"{node.id}<br/>(Router: {node.input_key})"

        elif isinstance(node, EvaluatorNode):
            # Evaluator Node: Circle/Stadium ([ ])
            style_class = "evaluator"
            shape_open = "(["
            shape_close = "])"
            label = f"{node.id}<br/>(Evaluator)"

        elif isinstance(node, GenerativeNode):
            # Generative Node: Subroutine [[ ]]
            style_class = "generative"
            shape_open = "[["
            shape_close = "]]"
            label = f"{node.id}<br/>(Generative)"

        lines.append(f'{sanitized_id}{shape_open}"{label}"{shape_close}:::{style_class}')

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

    # Implicit edges (e.g. from leaf nodes to END)
    # Finding leaf nodes is a bit complex in graph, so we skip for now unless requested.
    # Users can manually add edges to END if needed, or rely on visual inspection.
    # However, for clarity, we might want to verify if any node has no outgoing edges.
    # But graph topology doesn't strictly enforce a sink node structure except via edges.

    return "\n".join(lines)


def generate_mermaid_graph(agent: ManifestV2 | RecipeDefinition) -> str:
    """
    Generates a Mermaid.js flowchart string from a ManifestV2 (Agent Definition) or RecipeDefinition.
    """
    if isinstance(agent, RecipeDefinition):
        return _generate_recipe_mermaid(agent)

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
