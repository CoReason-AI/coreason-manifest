# src/coreason_manifest/utils/validator.py

from coreason_manifest.spec.core.flow import AnyNode, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode, SwitchNode
from coreason_manifest.spec.core.tools import ToolPack


def validate_flow(flow: LinearFlow | GraphFlow) -> list[str]:
    """
    Semantically validate a Flow (Linear or Graph).
    Returns a list of error strings. Empty list implies validity.
    """
    errors: list[str] = []

    # Flatten nodes based on flow type
    nodes: list[AnyNode] = []
    if isinstance(flow, GraphFlow):
        nodes = list(flow.graph.nodes.values())
    elif isinstance(flow, LinearFlow):
        nodes = flow.sequence

    valid_ids = {n.id for n in nodes}

    # 1. Common Checks
    if flow.governance:
        errors.extend(_validate_governance(flow.governance, valid_ids))

    if flow.definitions and flow.definitions.tool_packs:
        # Convert dict to list for backward compatibility with _validate_tools
        tool_packs = list(flow.definitions.tool_packs.values())
        errors.extend(_validate_tools(nodes, tool_packs))

    for node in nodes:
        errors.extend(_validate_supervision(node, valid_ids))

    # 2. LinearFlow Specific Checks
    if isinstance(flow, LinearFlow):
        errors.extend(_validate_linear_integrity(flow))
        node_ids = {n.id for n in flow.sequence}
        errors.extend(_validate_unique_ids(flow.sequence))
        errors.extend(_validate_switch_logic(flow.sequence, node_ids))

    # 3. GraphFlow Specific Checks
    if isinstance(flow, GraphFlow):
        if not flow.graph.nodes:
            errors.append("GraphFlow Error: Graph must contain at least one node.")

        errors.extend(_validate_graph_integrity(flow.graph))

        # Helper for extracting nodes for generic logic checks
        nodes_list = list(flow.graph.nodes.values())
        node_ids = set(flow.graph.nodes.keys())

        errors.extend(_validate_unique_ids(nodes_list))
        errors.extend(_validate_switch_logic(nodes_list, node_ids))
        errors.extend(_validate_orphan_nodes(flow.graph))

    return errors


def _validate_governance(gov: Governance, valid_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if gov.rate_limit_rpm is not None and gov.rate_limit_rpm < 0:
        errors.append("Governance Error: rate_limit_rpm cannot be negative.")
    if gov.cost_limit_usd is not None and gov.cost_limit_usd < 0:
        errors.append("Governance Error: cost_limit_usd cannot be negative.")
    if (
        gov.circuit_breaker
        and gov.circuit_breaker.fallback_node_id
        and gov.circuit_breaker.fallback_node_id not in valid_ids
    ):
        errors.append(
            f"Circuit Breaker Error: 'fallback_node_id' points to missing ID '{gov.circuit_breaker.fallback_node_id}'."
        )
    return errors


def _validate_tools(nodes: list[AnyNode], packs: list[ToolPack]) -> list[str]:
    errors: list[str] = []
    available_tools = {t for pack in packs for t in pack.tools}

    for node in nodes:
        if isinstance(node, AgentNode):
            errors.extend(
                f"Missing Tool Warning: Agent '{node.id}' requires tool '{tool}' "
                "but it is not provided by any attached ToolPack."
                for tool in node.tools
                if tool not in available_tools
            )
    return errors


def _validate_linear_integrity(flow: LinearFlow) -> list[str]:
    if not flow.sequence:
        return ["LinearFlow Error: Sequence cannot be empty."]
    return []


def _validate_unique_ids(nodes: list[AnyNode]) -> list[str]:
    seen = set()
    errors: list[str] = []
    for node in nodes:
        if node.id in seen:
            errors.append(f"ID Collision Error: Duplicate Node ID '{node.id}' found.")
        seen.add(node.id)
    return errors


def _validate_graph_integrity(graph: Graph) -> list[str]:
    errors: list[str] = []
    valid_ids = set(graph.nodes.keys())

    # Check 1: Key/ID Integrity
    for key, node in graph.nodes.items():
        if key != node.id:
            errors.append(f"Graph Integrity Error: Node key '{key}' does not match Node ID '{node.id}'.")

    # Check 2: Edge Validity
    for edge in graph.edges:
        if edge.source not in valid_ids:
            errors.append(f"Dangling Edge Error: Source '{edge.source}' not found in graph nodes.")
        if edge.target not in valid_ids:
            errors.append(f"Dangling Edge Error: Target '{edge.target}' not found in graph nodes.")

    return errors


def _validate_switch_logic(nodes: list[AnyNode], valid_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for node in nodes:
        if isinstance(node, SwitchNode):
            # Check Cases
            for condition, target_id in node.cases.items():
                if target_id not in valid_ids:
                    errors.append(
                        f"Broken Switch Error: Node '{node.id}' case '{condition}' points to missing ID '{target_id}'."
                    )
            # Check Default
            if node.default not in valid_ids:
                errors.append(
                    f"Broken Switch Error: Node '{node.id}' default route points to missing ID '{node.default}'."
                )
    return errors


def _validate_orphan_nodes(graph: Graph) -> list[str]:
    if not graph.nodes:
        return []

    # All nodes physically present in the dict
    all_ids = set(graph.nodes.keys())

    # Assume first node is entry point and exempt it
    entry_point = next(iter(graph.nodes.keys()))

    targeted_ids = {edge.target for edge in graph.edges}

    orphans = all_ids - targeted_ids

    # Remove entry point from orphans if present (it's expected to have no incoming edges)
    if entry_point in orphans:
        orphans.remove(entry_point)

    return [f"Orphan Node Warning: Node '{oid}' has no incoming edges." for oid in orphans]


def _validate_supervision(node: AnyNode, valid_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if node.supervision:
        if node.supervision.strategy == "degrade" and node.supervision.default_payload is None:
            errors.append(f"Node '{node.id}' is set to 'degrade' but missing 'default_payload'.")

        if node.supervision.backoff_factor < 1.0:
            errors.append(f"Supervision Error: Node '{node.id}' backoff_factor must be >= 1.0.")

        if node.supervision.fallback and node.supervision.fallback not in valid_ids:
            errors.append(
                f"Supervision Error: Node '{node.id}' fallback points to missing ID '{node.supervision.fallback}'."
            )

    return errors
