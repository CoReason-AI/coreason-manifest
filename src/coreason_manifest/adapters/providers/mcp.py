from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from coreason_manifest.core.common.presentation import UIEventMap
from coreason_manifest.core.state import ToolPack
from coreason_manifest.core.state.tools import MCPTool


class MCPRequestMethod(StrEnum):
    EMIT_INTENT = "mcp.ui.emit_intent"
    READY = "mcp.ui.ready"
    ERROR = "mcp.ui.error"


class MCPClientMessage(BaseModel):
    jsonrpc: Literal["2.0"] = Field(default="2.0", description="JSON-RPC version")
    method: MCPRequestMethod = Field(..., description="The lifecycle or intent bubbling method emitted from the UI")
    params: dict[str, Any] = Field(default_factory=dict, description="Intent parameters payload")
    id: str | int = Field(..., description="Message ID")


class MCPUIBroker:
    def validate_iframe_payload(self, payload: dict[str, Any]) -> MCPClientMessage:
        """
        Validates the raw dictionary payload from the WebView iframe
        into a strict MCPClientMessage schema.
        """
        return MCPClientMessage.model_validate(payload)

    def translate_intent_to_action(
        self, message: MCPClientMessage, event_map: UIEventMap | None = None
    ) -> dict[str, Any]:
        """
        Safely unpacks the `params` (the user's intent) so the execution
        engine can route it to the Blackboard or the Agent's context.
        """
        if event_map is None:
            raise ValueError("Untethered state mutation from an MCP iframe is forbidden.")

        payload_mapping = event_map.payload_mapping or {}
        action_payload: dict[str, Any] = {}

        for param_key, param_value in message.params.items():
            if param_key in payload_mapping:
                target_var = payload_mapping[param_key]
                action_payload[target_var] = param_value

        return action_payload


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
