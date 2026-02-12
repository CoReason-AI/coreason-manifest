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

    # Model: use node.profile.reasoning.model or default
    model: Any = "gpt-4-turbo"
    if isinstance(node.profile, str):
        # TODO: Lookup Profile from registry in Phase 2
        # For now, we raise an error as we can't resolve the string ID without the registry context
        raise NotImplementedError("Profile resolution from string ID not yet implemented in adapter.")

    if node.profile.reasoning:
        model = node.profile.reasoning.model

    # Instructions: Combine role and persona
    instructions = f"{node.profile.role} {node.profile.persona}"

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
