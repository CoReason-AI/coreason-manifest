from typing import Any, override

from coreason_manifest.core.state import ToolPack
from coreason_manifest.core.workflow import AgentNode
from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow
from coreason_manifest.core.workflow.topology import get_unified_topology
from coreason_manifest.ports.llm_provider import GenerativeAdapter


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
        return {
            "type": "graph",
            "nodes": [node.id for node in nodes],
            "edges": [(edge.from_node, edge.to_node, edge.condition) for edge in edges],
        }

    return {}  # pragma: no cover


class LangChainAdapter(GenerativeAdapter):
    """
    LangChain implementation of the GenerativeAdapter protocol.
    """

    @override
    def node_to_provider_assistant(self, node: AgentNode, tool_packs: list[ToolPack] | None = None) -> dict[str, Any]:
        """
        Converts an AgentNode into a LangChain-specific assistant payload.
        """
        return {}
