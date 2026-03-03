from coreason_manifest.adapters.providers.mcp import MCPClientMessage, MCPUIBroker
from coreason_manifest.core.common.presentation import PresentationHints


def test_mcp_client_message() -> None:
    data = {"jsonrpc": "2.0", "method": "mcp.ui.emit_intent", "params": {"action": "checkout"}, "id": 1}
    msg = MCPClientMessage(**data)
    assert msg.jsonrpc == "2.0"
    assert msg.method == "mcp.ui.emit_intent"
    assert msg.params == {"action": "checkout"}
    assert msg.id == 1


def test_mcp_ui_broker() -> None:
    broker = MCPUIBroker()
    data = {"jsonrpc": "2.0", "method": "mcp.ui.emit_intent", "params": {"action": "save_draft"}, "id": "abc"}
    msg = broker.validate_iframe_payload(data)
    assert isinstance(msg, MCPClientMessage)

    intent = broker.translate_intent_to_action(msg)
    assert intent == {"action": "save_draft"}


def test_presentation_hints_mcp_uri() -> None:
    hints = PresentationHints(mcp_ui_resource_uri="ui://my-custom-app")
    assert hints.mcp_ui_resource_uri == "ui://my-custom-app"
