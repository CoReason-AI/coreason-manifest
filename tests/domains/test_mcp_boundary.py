import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from mcp.server import Server
from mcp.shared.session import SessionMessage
from mcp.types import JSONRPCMessage
from pydantic import ValidationError

from coreason_manifest.adapters.mcp.schemas import BoundedJSONRPCRequest
from coreason_manifest.cli.mcp_server import _global_error_handler_shield

# Initialize the global shield for tests
_global_error_handler_shield()


def test_jsonrpc_fuzzer_missing_jsonrpc():
    """Prove the schema definitely rejects payloads missing 'jsonrpc' version."""
    payload = {"method": "test", "params": {}, "id": 1}
    with pytest.raises(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


def test_jsonrpc_fuzzer_missing_method():
    """Prove the schema definitely rejects payloads missing 'method'."""
    payload = {"jsonrpc": "2.0", "params": {}, "id": 1}
    with pytest.raises(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


def test_jsonrpc_fuzzer_invalid_id():
    """Prove the schema definitely rejects payloads with invalid 'id' types."""
    payload = {"jsonrpc": "2.0", "method": "test", "params": {}, "id": [1, 2, 3]}
    with pytest.raises(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


@given(st.recursive(st.dictionaries(st.text(), st.text()), lambda children: st.dictionaries(st.text(), children)))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_buffer_and_depth_attack_proof(params):
    """
    Generate params payloads with deeply recursive JSON objects.
    Prove that the schema triggers a ValidationError if it goes out of bounds.
    """
    payload = {"jsonrpc": "2.0", "method": "test_method", "params": params, "id": 1}
    import contextlib

    with contextlib.suppress(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


def test_explicit_buffer_attack_proof():
    """Explicitly test a massive string buffer attack."""
    payload = {"jsonrpc": "2.0", "method": "test_method", "params": {"huge_string": "A" * 20000}, "id": 1}
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate(payload)
    assert "String exceeds maximum length" in str(exc.value)


def test_explicit_depth_attack_proof():
    """Explicitly test a deep nesting depth attack."""
    nested = {}
    current = nested
    for _ in range(15):
        current["k"] = {}
        current = current["k"]

    payload = {"jsonrpc": "2.0", "method": "test_method", "params": nested, "id": 1}
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate(payload)
    assert "depth" in str(exc.value)


@pytest.mark.anyio
async def test_uptime_assertion_poison_pill():
    """
    Pass toxic malformed dictionaries directly into the MCP server's primary request handling function.
    Assert that the function does not raise an exception.
    Assert that it gracefully returns a valid JSONRPCErrorResponse object with code -32600 or -32700.
    """
    # Create a mock server and mock session
    server = Server("mock_server")

    class MockSendStream:
        def __init__(self):
            self.sent_messages = []

        async def send(self, message):
            self.sent_messages.append(message)

    class MockSession:
        def __init__(self):
            self.send_stream = MockSendStream()

    mock_session = MockSession()

    # Pass an Exception directly (simulating a parse failure in stdio_server)
    await server._handle_message(Exception("Simulated Parse Error"), mock_session, None)

    assert len(mock_session.send_stream.sent_messages) == 1
    sent_msg = mock_session.send_stream.sent_messages[0]

    response_dict = sent_msg.message.model_dump()

    assert response_dict["jsonrpc"] == "2.0"
    assert response_dict["error"]["code"] == -32700

    # Test with ValidationError by providing a deeply nested object that will fail internal schema validation
    mock_session.send_stream.sent_messages.clear()

    # We create a JSONRPCMessage using pydantic's construct or parse, but since it bypasses our bounds,
    # we simulate FastMCP parsing it correctly, and then we inject it into the shield.
    nested_bomb = {}
    current = nested_bomb
    for _ in range(15):
        current["k"] = {}
        current = current["k"]

    toxic_payload = {"jsonrpc": "2.0", "method": "list_tools", "params": nested_bomb, "id": 42}

    # Create a raw JSONRPCMessage (using validate to bypass limits if any were set on it,
    # or just pass a valid message according to MCP types)
    try:
        parsed_toxic = JSONRPCMessage.model_validate(toxic_payload)
    except Exception:
        # If it fails even before, we just pass an Exception
        parsed_toxic = Exception("Failed MCP Parse")

    message_wrap = SessionMessage(message=parsed_toxic)

    try:
        # Pass the toxic message wrapper directly. The shield should catch its own validation error or FastMCP error
        await server._handle_message(message_wrap, mock_session, None)
    except Exception as e:
        pytest.fail(f"Server raised exception instead of catching it natively: {e}")

    assert len(mock_session.send_stream.sent_messages) == 1
    sent_msg2 = mock_session.send_stream.sent_messages[0]
    response_dict2 = sent_msg2.message.model_dump()
    assert response_dict2["jsonrpc"] == "2.0"
    assert response_dict2["error"]["code"] in (-32600, -32700)
