import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BoundedJSONRPCIntent


def test_bounded_json_rpc_intent_valid() -> None:
    intent = BoundedJSONRPCIntent(
        jsonrpc="2.0",
        method="test.method",
        params={"key": "value", "nested": [1, 2, 3]},
        id=1
    )
    assert intent.method == "test.method"
    assert intent.params == {"key": "value", "nested": [1, 2, 3]}


def test_bounded_json_rpc_intent_none_params() -> None:
    intent = BoundedJSONRPCIntent(
        jsonrpc="2.0",
        method="test.method",
        params=None,
        id="abc"
    )
    assert intent.params == {}


def test_bounded_json_rpc_intent_invalid_params_type() -> None:
    with pytest.raises(ValidationError, match="params must be a dictionary"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params=["not", "a", "dict"],  # type: ignore
        )


def test_bounded_json_rpc_intent_exceeds_depth() -> None:
    # Create a dictionary nested 11 levels deep
    nested_dict = {}
    current = nested_dict
    for _ in range(11):
        current["child"] = {}
        current = current["child"]

    with pytest.raises(ValidationError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params=nested_dict
        )


def test_bounded_json_rpc_intent_exceeds_dict_keys() -> None:
    # Create a dictionary with 101 keys
    large_dict = {f"key_{i}": i for i in range(101)}

    with pytest.raises(ValidationError, match="Dictionary exceeds maximum of 100 keys"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params=large_dict
        )


def test_bounded_json_rpc_intent_exceeds_dict_key_length() -> None:
    # Create a dictionary with a key > 1000 chars
    long_key = "a" * 1001
    bad_dict = {long_key: "value"}

    with pytest.raises(ValidationError, match="Dictionary key exceeds maximum length of 1000"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params=bad_dict
        )


def test_bounded_json_rpc_intent_exceeds_list_length() -> None:
    # Create a list with 1001 elements
    large_list = [i for i in range(1001)]

    with pytest.raises(ValidationError, match="List exceeds maximum of 1000 elements"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params={"data": large_list}
        )


def test_bounded_json_rpc_intent_exceeds_string_length() -> None:
    # Create a string with > 10000 characters
    long_string = "a" * 10001

    with pytest.raises(ValidationError, match="String exceeds maximum length of 10000 characters"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params={"data": long_string}
        )
