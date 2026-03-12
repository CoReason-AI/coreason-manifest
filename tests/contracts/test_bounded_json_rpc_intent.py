from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BoundedJSONRPCIntent


def test_valid_json_rpc_intent() -> None:
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params={"key": "value"}, id=1)
    assert intent.method == "test_method"
    assert intent.params == {"key": "value"}


def test_json_rpc_intent_max_depth() -> None:
    params: dict[str, Any] = {}
    current = params
    for _i in range(11):
        current["key"] = {}
        current = current["key"]

    with pytest.raises(ValidationError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_dict_keys() -> None:
    params: dict[str, Any] = {f"key_{i}": i for i in range(101)}

    with pytest.raises(ValidationError, match="Dictionary exceeds maximum of 100 keys"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_dict_key_length() -> None:
    params: dict[str, Any] = {"k" * 1001: "value"}

    with pytest.raises(ValidationError, match="Dictionary key exceeds maximum length of 1000"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_list_elements() -> None:
    params: dict[str, Any] = {"list": [1] * 1001}

    with pytest.raises(ValidationError, match="List exceeds maximum of 1000 elements"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_string_length() -> None:
    params: dict[str, Any] = {"key": "v" * 10001}

    with pytest.raises(ValidationError, match="String exceeds maximum length of 10000 characters"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_params_not_dict() -> None:
    with pytest.raises(ValidationError, match="params must be a dictionary"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=[1, 2, 3], id=1)  # type: ignore[arg-type]
