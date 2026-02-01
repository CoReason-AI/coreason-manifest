import pytest
from coreason_manifest.definitions.message import FunctionCall, ToolCall, ToolCallRequestPart


def test_function_call_deprecation() -> None:
    with pytest.warns(DeprecationWarning, match="FunctionCall is deprecated"):
        FunctionCall(name="foo", arguments="{}")


def test_tool_call_deprecation() -> None:
    # Capture the expected warning for FunctionCall to avoid breaking strict CI
    with pytest.warns(DeprecationWarning, match="FunctionCall is deprecated"):
        fc = FunctionCall(name="foo", arguments="{}")

    with pytest.warns(DeprecationWarning, match="ToolCall is deprecated"):
        ToolCall(id="call_123", function=fc)


def test_tool_call_request_part_caching() -> None:
    # Test JSON parsing and caching behavior
    part = ToolCallRequestPart(name="test", arguments='{"key": "value"}')

    # First access - should parse
    args1 = part.parsed_arguments
    assert args1 == {"key": "value"}

    # Second access - should return cached object (same identity)
    args2 = part.parsed_arguments
    assert args2 is args1

    # Verify parsing logic for non-JSON strings
    part_bad = ToolCallRequestPart(name="bad", arguments="invalid json")
    assert part_bad.parsed_arguments == {}

    # Verify direct dict arguments
    part_dict = ToolCallRequestPart(name="dict", arguments={"direct": "dict"})
    assert part_dict.parsed_arguments == {"direct": "dict"}
