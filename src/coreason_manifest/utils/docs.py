# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import TYPE_CHECKING, Any

from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2

if TYPE_CHECKING:
    from coreason_manifest.spec.v2.resources import ModelProfile


def render_agent_card(agent: ManifestV2) -> str:
    """
    Render a standardized Markdown "Agent Card" from a ManifestV2 object.

    Args:
        agent: The Agent Manifest to render. Must contain at least one AgentDefinition.

    Returns:
        A Markdown string formatted with Metadata, Financials, Governance, and API Interface.
    """
    # 1. Component Extraction
    manifest = agent
    metadata = manifest.metadata

    # Find the AgentDefinition
    # Priority:
    # 1. Definition matching the manifest name
    # 2. The first AgentDefinition found in definitions
    agent_def: AgentDefinition | None = None

    if metadata.name in manifest.definitions:
        candidate = manifest.definitions[metadata.name]
        if isinstance(candidate, AgentDefinition):
            agent_def = candidate

    if not agent_def:
        for definition in manifest.definitions.values():
            if isinstance(definition, AgentDefinition):
                agent_def = definition
                break

    # 2. Header Section
    # Check for version in extra fields of metadata
    version = getattr(metadata, "version", "0.0.0")
    if not isinstance(version, str):
        version = str(version)

    output = [f"# {metadata.name} (v{version})"]

    # Metadata Block
    role = agent_def.role if agent_def else "Unknown Role"
    created = getattr(metadata, "created", None)

    meta_parts = [f"**Role:** {role}"]
    if created:
        meta_parts.append(f" | **Created:** {created}")

    output.append("\n" + "".join(meta_parts))

    # Description
    description = None
    if agent_def and agent_def.backstory:
        # Quote the backstory
        description = "\n".join(f"> {line}" for line in agent_def.backstory.splitlines())
    elif agent_def and hasattr(agent_def, "description") and agent_def.description:
        description = agent_def.description

    if description:
        output.append("\n" + description)

    # 3. Financials (If resources exist)
    if agent_def and agent_def.resources:
        res: ModelProfile = agent_def.resources
        output.append("\n## 💰 Resource & Cost Profile")
        output.append(f"- **Model:** {res.provider}/{res.model_id}")

        if res.pricing:
            p = res.pricing
            # Fallback for display if unit is enum
            unit_str = p.unit.value if hasattr(p.unit, "value") else str(p.unit)
            # Simplify TOKEN_1M to "1M" for display if it matches
            if unit_str == "TOKEN_1M":
                display_unit = "1M"
            elif unit_str == "TOKEN_1K":
                display_unit = "1k"
            else:
                display_unit = unit_str

            output.append(
                f"- **Pricing:** ${p.input_cost} / {display_unit} Input | ${p.output_cost} / {display_unit} Output"
            )

        if res.constraints:
            output.append(f"- **Context Window:** {res.constraints.context_window_size} tokens")

    # 4. Governance (If agent.governance exists)
    # Check for 'governance' attribute on the manifest object (duck typing/extra)
    # This supports cases where the manifest object might be wrapped or extended.
    governance = getattr(manifest, "governance", None)

    # Also check if policy indicates risks or if we have critical tools
    # For now, we strictly follow instructions: "If agent.governance exists"
    if governance:
        output.append("\n## 🛡️ Governance & Safety")

        risk = getattr(governance, "risk_level", None)
        if risk:
            output.append(f"- **Risk Level:** {risk}")

        # "List all active policies" - assuming governance has a 'policies' list or similar
        policies = getattr(governance, "policies", [])
        if policies:
            output.append("- **Active Policies:**")
            output.extend(f"  - {policy}" for policy in policies)

    # 5. Interface Contract
    output.append("\n## 🔌 API Interface")

    # Inputs
    inputs_schema = manifest.interface.inputs
    output.append("\n### Inputs")
    output.append(_render_schema_table(inputs_schema))

    # Outputs
    outputs_schema = manifest.interface.outputs
    output.append("\n### Outputs")
    output.append(_render_schema_table(outputs_schema))

    # 6. Quality Assurance (If agent.evaluation exists)
    if agent_def and agent_def.evaluation:
        eval_profile = agent_def.evaluation
        output.append("\n## 🧪 Evaluation Standards")

        if eval_profile.grading_rubric:
            output.append("- **Grading Rubric:**")
            output.extend(
                f"  - **{criterion.name}:** {criterion.description} (Threshold: {criterion.threshold})"
                for criterion in eval_profile.grading_rubric
            )

        if eval_profile.expected_latency_ms:
            output.append(f"- **SLA:** {eval_profile.expected_latency_ms}ms latency")

    return "\n".join(output)


def _render_schema_table(schema: dict[str, Any]) -> str:
    """Helper to render a JSON Schema properties table in Markdown."""
    if not schema or "properties" not in schema or not schema["properties"]:
        return "_No fields defined._"

    headers = ["Field Name", "Type", "Required?", "Description"]
    # Markdown table header
    lines = ["| " + " | ".join(headers) + " |"]
    # Markdown table separator
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    properties = schema.get("properties", {})
    required_set = set(schema.get("required", []))

    # Sort properties for consistent output
    sorted_props = sorted(properties.items())

    for name, prop in sorted_props:
        type_ = prop.get("type", "any")
        req = "Yes" if name in required_set else "No"
        desc = prop.get("description", "").replace("\n", " ").strip()
        if not desc:
            desc = "-"

        row = [f"`{name}`", f"`{type_}`", req, desc]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)
