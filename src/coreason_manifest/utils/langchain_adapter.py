from typing import Any

from coreason_manifest.spec.core.flow import FlowSpec
from coreason_manifest.utils.topology import get_unified_topology


def flow_to_langchain_config(flow: FlowSpec) -> dict[str, Any]:
    """
    Convert a Core Flow into a LangChain-compatible configuration.

    Args:
        flow: A FlowSpec object.

    Returns:
        A dictionary representing the LangChain configuration.
    """
    nodes, edges = get_unified_topology(flow)

    return {
        "type": "graph",
        "nodes": [node.id for node in nodes],
        "edges": [(edge.from_node, edge.to_node, edge.condition) for edge in edges],
    }
