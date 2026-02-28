from typing import Any

from coreason_manifest.spec.core.state.tools import MCPTool, ToolPack


def pack_to_mcp_resources(pack: ToolPack) -> list[dict[str, Any]]:
    """
    Convert a ToolPack into Model Context Protocol (MCP) resource definitions.

    Args:
        pack: The ToolPack to convert.

    Returns:
        A list of dictionaries representing MCP resources.
    """
    resources = []
    for tool in pack.tools:
        if isinstance(tool, MCPTool):
            resources.extend(
                [
                    {
                        "uri": tpl.uri_template,
                        "name": tpl.name,
                        "mimeType": tpl.mime_type or "application/json",
                        "description": tpl.description or "",
                    }
                    for tpl in tool.resource_templates
                ]
            )
        else:
            resources.append(
                {"uri": f"mcp://{pack.namespace}/{tool.name}", "name": tool.name, "mimeType": "application/json"}
            )
    return resources


def pack_to_mcp_prompts(pack: ToolPack) -> list[dict[str, Any]]:
    """
    Convert a ToolPack's MCP tools into MCP prompt definitions.
    """
    prompts = []
    for tool in pack.tools:
        if isinstance(tool, MCPTool):
            prompts.extend(
                [
                    {"name": prompt.name, "description": prompt.description or "", "arguments": prompt.arguments or []}
                    for prompt in tool.prompts
                ]
            )
    return prompts


def parse_mcp_tool_payload(tool: MCPTool) -> dict[str, Any]:
    """
    Safely parse an MCPTool into a standard dictionary payload suitable
    for a remote Model Context Protocol server handshake.
    """
    return {
        "mcp_version": tool.mcp_version,
        "capabilities": tool.supported_capabilities,
        "server_uri": str(tool.server_uri),
    }
