from typing import Any

from coreason_manifest.core.workflow import GraphFlow, LinearFlow
from coreason_manifest.toolkit.visualizer import to_mermaid


def _render_schema_tables(schema: dict[str, Any] | Any) -> str:
    """Render a dual-audience Markdown table from a JSON schema."""
    if not schema:
        return "No schema defined.\n"

    # If the schema is a Pydantic model (e.g. DataSchema), extract json_schema
    if hasattr(schema, "json_schema"):
        raw_schema = schema.json_schema
    elif isinstance(schema, dict):
        # We need to extract the actual json_schema from inside if it exists
        # FlowInterface typically has `inputs: dict | DataSchema`.
        raw_schema = schema.get("json_schema", schema)
    else:
        raw_schema = {}

    properties = raw_schema.get("properties", {})
    required = raw_schema.get("required", [])

    if not properties:
        return "No properties defined.\n"

    lines = [
        "| Field Name | Type | Required? | Description |",
        "|---|---|---|---|",
    ]

    for field_name, field_def in properties.items():
        field_type = field_def.get("type", "any")
        is_required = "✅" if field_name in required else "❌"
        description = field_def.get("description", "")

        # Replace newlines in description to avoid breaking markdown tables
        if description:
            description = description.replace("\n", " ")

        lines.append(f"| `{field_name}` | `{field_type}` | {is_required} | {description} |")

    return "\n".join(lines) + "\n"


def _render_governance_block(governance: Any) -> str:
    """Disclose the agent's constraints."""
    if not governance:
        return "No governance constraints defined.\n"

    lines = []

    if getattr(governance, "max_risk_level", None):
        max_risk = governance.max_risk_level
        max_risk_str = getattr(max_risk, "value", str(max_risk))
        lines.append(f"- **Global Max Risk Level:** {max_risk_str}")

    policy = getattr(governance, "operational_policy", None)
    if policy:
        lines.append("- **Operational Limits:**")
        if getattr(policy, "financial", None):
            fin = policy.financial
            fin_limits = []
            if getattr(fin, "max_cost_usd", None) is not None:
                fin_limits.append(f"Max Cost: ${fin.max_cost_usd}")
            if getattr(fin, "max_transaction_cost_usd", None) is not None:
                fin_limits.append(f"Max Tx Cost: ${fin.max_transaction_cost_usd}")
            if getattr(fin, "max_tokens_total", None) is not None:
                fin_limits.append(f"Max Tokens: {fin.max_tokens_total}")
            if fin_limits:
                lines.append(f"  - Financial: {', '.join(fin_limits)}")

        if getattr(policy, "compute", None):
            comp = policy.compute
            comp_limits = []
            if getattr(comp, "max_execution_time_seconds", None) is not None:
                comp_limits.append(f"Max Execution Time: {comp.max_execution_time_seconds}s")
            if getattr(comp, "max_cognitive_steps", None) is not None:
                comp_limits.append(f"Max Cognitive Steps: {comp.max_cognitive_steps}")
            if getattr(comp, "max_concurrent_agents", None) is not None:
                comp_limits.append(f"Max Concurrent Agents: {comp.max_concurrent_agents}")
            if getattr(comp, "max_tokens_per_turn", None) is not None:
                comp_limits.append(f"Max Tokens/Turn: {comp.max_tokens_per_turn}")

            compression_strategy = getattr(comp, "context_compression_strategy", None)
            if compression_strategy and compression_strategy != "none":
                comp_limits.append(f"Context Compression: {compression_strategy}")

            if comp_limits:
                lines.append(f"  - Compute: {', '.join(comp_limits)}")

        if getattr(policy, "data", None):
            data = policy.data
            data_limits = []
            if getattr(data, "max_rows_per_query", None) is not None:
                data_limits.append(f"Max Rows/Query: {data.max_rows_per_query}")
            if getattr(data, "max_payload_bytes", None) is not None:
                data_limits.append(f"Max Payload Bytes: {data.max_payload_bytes}")
            if getattr(data, "max_search_results", None) is not None:
                data_limits.append(f"Max Search Results: {data.max_search_results}")
            if data_limits:
                lines.append(f"  - Data: {', '.join(data_limits)}")

    active_middlewares = getattr(governance, "active_middlewares", None)
    if active_middlewares:
        lines.append(f"- **Active Interceptors:** {', '.join(active_middlewares)}")

    circuit_breaker = getattr(governance, "circuit_breaker", None)
    if circuit_breaker:
        lines.append("- **Circuit Breaker Thresholds:**")
        if getattr(circuit_breaker, "error_threshold_count", None) is not None:
            lines.append(f"  - Error Threshold: {circuit_breaker.error_threshold_count} failures")
        if getattr(circuit_breaker, "reset_timeout_seconds", None) is not None:
            lines.append(f"  - Reset Timeout: {circuit_breaker.reset_timeout_seconds}s")

    if not lines:
        return "No specific limits configured.\n"

    return "\n".join(lines) + "\n"


def _render_tools(tool_packs: dict[str, Any] | None) -> str:
    """Iterate over ToolPack definitions and list tools."""
    if not tool_packs:
        return "No permitted tools defined.\n"

    lines = []
    for pack_def in tool_packs.values():
        tools = getattr(pack_def, "tools", [])
        for tool in tools:
            tool_name = getattr(tool, "name", "Unknown Tool")
            risk_level = getattr(tool, "risk_level", "Unknown Risk")
            risk_level_str = getattr(risk_level, "value", str(risk_level))
            description = getattr(tool, "description", "No description provided.")
            lines.append(f"- **{tool_name}** (Risk: {risk_level_str}) - {description}")

    if not lines:
        return "No permitted tools defined.\n"

    return "\n".join(lines) + "\n"


def render_agent_card(flow: GraphFlow | LinearFlow) -> str:
    """
    Parses a GraphFlow or LinearFlow and deterministically outputs a
    standardized Markdown 'Agent Card'.
    """

    # Extract metadata
    name = flow.metadata.name
    version = flow.metadata.version
    description = flow.metadata.description or "No description provided."

    doc_parts = []

    # 1. Header
    doc_parts.append(f"# 🤖 Agent: {name} (v{version})")
    doc_parts.append(f"> {description}")
    doc_parts.append("")

    provenance = getattr(flow.metadata, "provenance", None)
    if provenance:
        doc_parts.append("## 🧬 Supply Chain Lineage")
        doc_parts.append(f"- **Origin Type:** `{provenance.type}`")
        if getattr(provenance, "generated_by", None):
            doc_parts.append(f"- **Generated By:** `{provenance.generated_by}`")
        if getattr(provenance, "derived_from", None):
            doc_parts.append(f"- **Derived From:** `{provenance.derived_from}`")
        doc_parts.append("")

    # 2. Execution Topology
    doc_parts.append("## 🗺️ Execution Topology")
    doc_parts.append("```mermaid")
    doc_parts.append(to_mermaid(flow))
    doc_parts.append("```")
    doc_parts.append("")

    # 3. API Interface
    doc_parts.append("## 🔌 API Interface")
    doc_parts.append("### Inputs")
    inputs_schema = getattr(flow, "interface", None)
    if inputs_schema:
        doc_parts.append(_render_schema_tables(inputs_schema.inputs))
    else:
        doc_parts.append("No schema defined.\n")

    doc_parts.append("### Outputs")
    outputs_schema = getattr(flow, "interface", None)
    if outputs_schema:
        doc_parts.append(_render_schema_tables(outputs_schema.outputs))
    else:
        doc_parts.append("No schema defined.\n")
    doc_parts.append("")

    # 4. Governance & Blast Radius
    doc_parts.append("## 🛡️ Governance & Blast Radius")
    doc_parts.append(_render_governance_block(flow.governance))
    doc_parts.append("")

    # 5. Permitted Tools
    doc_parts.append("## 🛠️ Permitted Tools")
    tool_packs = None
    if flow.definitions:
        tool_packs = getattr(flow.definitions, "tool_packs", None)
    doc_parts.append(_render_tools(tool_packs))
    doc_parts.append("")

    return "\n".join(doc_parts)
