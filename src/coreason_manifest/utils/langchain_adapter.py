from typing import Any

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.topology import get_unified_topology


def flow_to_langchain_config(flow: LinearFlow | GraphFlow) -> dict[str, Any]:
    """
    Convert a Core Flow into a LangChain-compatible configuration.

    Args:
        flow: A LinearFlow or GraphFlow object.

    Returns:
        A dictionary representing the LangChain configuration.
    """
    nodes, edges = get_unified_topology(flow)

    if isinstance(flow, LinearFlow):
        return {"type": "chain", "steps": [node.id for node in nodes]}
    if isinstance(flow, GraphFlow):
        # TODO(Orchestration): Handle dynamic routing and HITL interrupts when LangChain supports them.
        # Currently, these SOTA features (Memory, EscalationCriteria) are passed through but not executed by standard LC chains.
        return {
            "type": "graph",
            "nodes": [node.id for node in nodes],
            "edges": [(edge.from_node, edge.to_node, edge.condition) for edge in edges],
        }

    return {}  # pragma: no cover
