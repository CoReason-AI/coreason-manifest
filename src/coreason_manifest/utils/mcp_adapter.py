from typing import Any

from coreason_manifest.spec.core.tools import MCPServerConfig


def pack_to_mcp_resources(pack: MCPServerConfig) -> list[dict[str, Any]]:
    """
    Convert a ToolPack into Model Context Protocol (MCP) resource definitions.

    Args:
        pack: The ToolPack to convert.

    Returns:
        A list of dictionaries representing MCP resources.
    """
    return [
        {"uri": f"mcp://{pack.namespace}/{tool.name}", "name": tool.name, "mimeType": "application/json"}
        for tool in pack.tools
    ]
