from typing import Any

from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.tools import MCPServerConfig


def node_to_openai_assistant(node: AgentNode, mcp_servers: list[MCPServerConfig] | None = None) -> dict[str, Any]:
    """
    Convert an AgentNode into an OpenAI Assistant definition.

    Args:
        node: The AgentNode to convert.
        mcp_servers: A list of available MCPServerConfigs.

    Returns:
        A dictionary representing the OpenAI Assistant configuration.
    """
    if mcp_servers is None:
        mcp_servers = []

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

    # Tools: Generate function definitions for every tool listed in node.tools found in mcp_servers
    available_tools: dict[str, Any] = {}
    for server in mcp_servers:
        for tool in server.tools:
            available_tools[tool.name] = tool

    tools_definitions = []
    for tool_name in node.tools:
        if tool_name in available_tools:
            tool = available_tools[tool_name]
            tool_def: dict[str, Any] = {
                "type": "function",
                "function": {"name": tool_name, "description": tool.description, "parameters": {}},
            }
            if tool.type == "mcp_tool" and tool.input_schema:
                tool_def["function"]["parameters"] = tool.input_schema

            tools_definitions.append(tool_def)

    return {"name": node.id, "instructions": instructions, "model": model, "tools": tools_definitions}
