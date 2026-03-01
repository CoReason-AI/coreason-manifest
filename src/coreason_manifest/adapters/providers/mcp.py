from typing import Any, Literal

from pydantic import BaseModel, Field

from coreason_manifest.core.state.tools import MCPTool, ToolPack


class MCPClientMessage(BaseModel):
    jsonrpc: Literal["2.0"] = Field(default="2.0", description="JSON-RPC version")
    method: Literal["mcp.ui.emit_intent"] = Field(..., description="The intent bubbling method emitted from the UI")
    params: dict[str, Any] = Field(default_factory=dict, description="Intent parameters payload")
    id: str | int = Field(..., description="Message ID")


class MCPUIBroker:
    def validate_iframe_payload(self, payload: dict[str, Any]) -> MCPClientMessage:
        """
        Validates the raw dictionary payload from the WebView iframe
        into a strict MCPClientMessage schema.
        """
        return MCPClientMessage.model_validate(payload)

    def translate_intent_to_action(self, message: MCPClientMessage) -> dict[str, Any]:
        """
        Safely unpacks the `params` (the user's intent) so the execution
        engine can route it to the Blackboard or the Agent's context.
        """
        return message.params


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
