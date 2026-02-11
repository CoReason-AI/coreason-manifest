from typing import Any

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow


def flow_to_langchain_config(flow: LinearFlow | GraphFlow) -> dict[str, Any]:
    """
    Convert a Core Flow into a LangChain-compatible configuration.

    Args:
        flow: A LinearFlow or GraphFlow object.

    Returns:
        A dictionary representing the LangChain configuration.
    """
    if isinstance(flow, LinearFlow):
        return {"type": "chain", "steps": [node.id for node in flow.sequence]}
    if isinstance(flow, GraphFlow):
        return {
            "type": "graph",
            "nodes": list(flow.graph.nodes.keys()),
            "edges": [(edge.source, edge.target, edge.condition) for edge in flow.graph.edges],
        }
    # This case should ideally not be reachable if type hints are respected
    raise ValueError(f"Unknown flow type: {type(flow)}")
