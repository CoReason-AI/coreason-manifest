import pytest
from coreason_manifest.definitions.message import FunctionCall, ToolCall

def test_function_call_deprecation():
    with pytest.warns(DeprecationWarning, match="FunctionCall is deprecated"):
        FunctionCall(name="foo", arguments="{}")

def test_tool_call_deprecation():
    fc = FunctionCall(name="foo", arguments="{}") # This also triggers warning, but we want to test ToolCall

    with pytest.warns(DeprecationWarning, match="ToolCall is deprecated"):
        ToolCall(id="call_123", function=fc)
