from coreason_manifest.spec.core.contracts import ActionNode, StrategyNode, StrictJsonValue
from coreason_manifest.spec.core.workflow.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.topology import get_unified_topology


def flow_to_langchain_config(flow: LinearFlow | GraphFlow) -> dict[str, StrictJsonValue]:
    """
    Convert a Core Flow into a LangChain-compatible configuration.

    Args:
        flow: A LinearFlow or GraphFlow object.

    Returns:
        A dictionary representing the LangChain configuration.
    """
    nodes, _ = get_unified_topology(flow)

    # 1. Bind the Skills
    tools: list[StrictJsonValue] = []
    if flow.definitions and flow.definitions.skills:
        for skill in flow.definitions.skills.values():
            # Get description from definition if available, otherwise default to empty string
            desc = ""
            if isinstance(skill.definition, dict) and "description" in skill.definition:
                desc_val = skill.definition["description"]
                if isinstance(desc_val, str):
                    desc = desc_val

            tools.append({
                "name": skill.name,
                "description": desc,
                "parameters": skill.definition
            })

    if isinstance(flow, LinearFlow):
        return {
            "type": "chain",
            "steps": [node.id for node in nodes],
            "tools": tools
        }

    if isinstance(flow, GraphFlow):
        edges: list[StrictJsonValue] = []
        # Dynamic Edge Extraction from the new architecture
        for node in nodes:
            if isinstance(node, ActionNode):
                if node.next_node:
                    edges.append([node.id, node.next_node, None])
            elif isinstance(node, StrategyNode):
                for route_key, route_target in node.routes.items():
                    edges.append([node.id, route_target, route_key])
                edges.append([node.id, node.default_route, "default"])

        return {
            "type": "graph",
            "nodes": [node.id for node in nodes],
            "edges": edges,
            "tools": tools
        }

    return {}  # pragma: no cover
