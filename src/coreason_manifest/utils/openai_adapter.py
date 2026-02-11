from typing import Any

from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.tools import ToolPack


def node_to_openai_assistant(node: AgentNode, tool_packs: list[ToolPack] | None = None) -> dict[str, Any]:
    """
    Convert an AgentNode into an OpenAI Assistant definition.

    Args:
        node: The AgentNode to convert.
        tool_packs: A list of available ToolPacks.

    Returns:
        A dictionary representing the OpenAI Assistant configuration.
    """
    if tool_packs is None:
        tool_packs = []

    # Model: use node.brain.reasoning.model or default
    model = "gpt-4-turbo"
    if node.brain.reasoning:
        model = node.brain.reasoning.model

    # Instructions: Combine role and persona
    instructions = f"{node.brain.role} {node.brain.persona}"

    # Tools: Generate function definitions for every tool listed in node.tools found in tool_packs
    available_tools = set()
    for pack in tool_packs:
        available_tools.update(pack.tools)

    tools_definitions = [
        {"type": "function", "function": {"name": tool_name}}
        for tool_name in node.tools
        if tool_name in available_tools
    ]

    return {"name": node.id, "instructions": instructions, "model": model, "tools": tools_definitions}
