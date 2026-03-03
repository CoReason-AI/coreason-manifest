from typing import Any, Literal

from pydantic import BaseModel, Field


class MCPClientMessage(BaseModel):
    """Strict JSON-RPC 2.0 structure for MCP client messages."""

    jsonrpc: Literal["2.0"] = Field(default="2.0", description="JSON-RPC version.")
    method: Literal["mcp.ui.emit_intent"] = Field(..., description="Method for intent bubbling.")
    params: dict[str, Any] = Field(default_factory=dict, description="Payload parameters.")
    id: str | int = Field(..., description="Unique request identifier.")


class MCPUIBroker:
    """Broker for handling MCP UI JSON-RPC messages."""

    def validate_iframe_payload(self, payload: dict[str, Any]) -> MCPClientMessage:
        """Parses and validates the raw dictionary from the Flutter WebView."""
        return MCPClientMessage.model_validate(payload)

    def translate_intent_to_action(self, message: MCPClientMessage) -> dict[str, Any]:
        """Safely unpacks the `params` (the user's intent) so the execution engine can route it."""
        return message.params
