import pytest

from coreason_manifest.adapters.providers.mcp import MCPClientMessage, MCPUIBroker
from coreason_manifest.core.common.presentation import PresentationHints
from coreason_manifest.ports.mcp import MCPOperation, MCPToolName


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


def test_mcp_operation_validation() -> None:
    # This should pass because we provide a target_element_id
    op1 = MCPOperation(
        operation_id="123",
        tool_name=MCPToolName.CANVAS_UPDATE_ELEMENT,
        target_element_id="elem-1",
    )
    assert op1.target_element_id == "elem-1"

    # This should pass because CANVAS_ADD_ELEMENT does not require a target_element_id
    op2 = MCPOperation(
        operation_id="124",
        tool_name=MCPToolName.CANVAS_ADD_ELEMENT,
    )
    assert op2.target_element_id is None

    # This should fail because CANVAS_REMOVE_ELEMENT requires a target_element_id
    with pytest.raises(ValueError, match="target_element_id cannot be None"):
        MCPOperation(
            operation_id="125",
            tool_name=MCPToolName.CANVAS_REMOVE_ELEMENT,
        )
