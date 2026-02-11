from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, SwitchNode


def validate_flow(flow: LinearFlow | GraphFlow) -> list[str]:
    """
    Validates the semantic correctness of a flow.

    Args:
        flow: The LinearFlow or GraphFlow to validate.

    Returns:
        A list of human-readable error strings. If empty, the flow is valid.
    """
    errors = []

    # 1. Gather all node IDs and nodes
    nodes = []
    node_ids = set()

    if isinstance(flow, GraphFlow):
        nodes = list(flow.graph.nodes.values())
        node_ids = set(flow.graph.nodes.keys())
    elif isinstance(flow, LinearFlow):
        nodes = flow.sequence
        node_ids = {node.id for node in nodes}
    else:
        # Should not happen given type hint, but safe to handle?
        return ["Unknown flow type"]

    # 2. Gather all available tools
    available_tools = set()
    for tool_pack in flow.tool_packs:
        available_tools.update(tool_pack.tools)

    # 3. Graph Integrity (GraphFlow only)
    if isinstance(flow, GraphFlow):
        for edge in flow.graph.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' not found in graph nodes.")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' not found in graph nodes.")

    # 4. Linear Integrity (LinearFlow only)
    if isinstance(flow, LinearFlow) and not flow.sequence:
        errors.append("LinearFlow sequence must not be empty.")

    # 5. Node Logic Checks
    for node in nodes:
        # Switch Logic
        if isinstance(node, SwitchNode):
            for case_key, target_id in node.cases.items():
                if target_id not in node_ids:
                    errors.append(f"SwitchNode '{node.id}' case '{case_key}' target '{target_id}' not found.")
            if node.default not in node_ids:
                errors.append(f"SwitchNode '{node.id}' default target '{node.default}' not found.")

        # Missing Tool Check
        if isinstance(node, AgentNode):
            errors.extend(
                f"Agent '{node.id}' requires tool '{tool}' but it is not provided by any ToolPack."
                for tool in node.tools
                if tool not in available_tools
            )

    # 6. Governance Sanity Check
    if flow.governance:
        # rate_limit_rpm: int | None
        if (
            flow.governance.rate_limit_rpm is not None
            and flow.governance.rate_limit_rpm < 0
        ):
            errors.append("Governance rate_limit_rpm must be non-negative.")
        # cost_limit_usd: float | None
        if (
            flow.governance.cost_limit_usd is not None
            and flow.governance.cost_limit_usd < 0
        ):
            errors.append("Governance cost_limit_usd must be non-negative.")

    return errors
