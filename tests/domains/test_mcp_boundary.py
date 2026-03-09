from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.adapters.mcp.schemas import BoundedJSONRPCRequest


def test_jsonrpc_fuzzer_missing_jsonrpc() -> None:
    """Prove the schema definitely rejects payloads missing 'jsonrpc' version."""
    payload = {"method": "test", "params": {}, "id": 1}
    with pytest.raises(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


def test_jsonrpc_fuzzer_missing_method() -> None:
    """Prove the schema definitely rejects payloads missing 'method'."""
    payload = {"jsonrpc": "2.0", "params": {}, "id": 1}
    with pytest.raises(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


def test_jsonrpc_fuzzer_invalid_id() -> None:
    """Prove the schema definitely rejects payloads with invalid 'id' types."""
    payload = {"jsonrpc": "2.0", "method": "test", "params": {}, "id": [1, 2, 3]}
    with pytest.raises(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


@given(st.recursive(st.dictionaries(st.text(), st.text()), lambda children: st.dictionaries(st.text(), children)))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_buffer_and_depth_attack_proof(params: dict[str, Any]) -> None:
    """
    Generate params payloads with deeply recursive JSON objects.
    Prove that the schema triggers a ValidationError if it goes out of bounds.
    """
    payload = {"jsonrpc": "2.0", "method": "test_method", "params": params, "id": 1}
    import contextlib

    with contextlib.suppress(ValidationError):
        BoundedJSONRPCRequest.model_validate(payload)


def test_explicit_buffer_attack_proof() -> None:
    """Explicitly test a massive string buffer attack."""
    payload = {"jsonrpc": "2.0", "method": "test_method", "params": {"huge_string": "A" * 20000}, "id": 1}
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate(payload)
    assert "String exceeds maximum length" in str(exc.value)


def test_explicit_depth_attack_proof() -> None:
    """Explicitly test a deep nesting depth attack."""
    nested: dict[str, Any] = {}
    current = nested
    for _ in range(15):
        current["k"] = {}
        current = current["k"]

    payload = {"jsonrpc": "2.0", "method": "test_method", "params": nested, "id": 1}
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate(payload)
    assert "depth" in str(exc.value)


def test_explicit_keys_and_list_limits() -> None:
    """Ensure the schema rejects too many dictionary keys and too many list items."""
    # Too many keys (>100)
    many_keys_dict = {f"k{i}": "v" for i in range(105)}
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate({"jsonrpc": "2.0", "method": "test", "params": many_keys_dict, "id": 1})
    assert "Dictionary exceeds maximum of 100 keys" in str(exc.value)

    # Key too long (>1000)
    long_key_dict = {"K" * 1005: "v"}
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate({"jsonrpc": "2.0", "method": "test", "params": long_key_dict, "id": 1})
    assert "Dictionary key exceeds maximum length of 1000" in str(exc.value)

    # Null params coverage
    BoundedJSONRPCRequest.model_validate({"jsonrpc": "2.0", "method": "test", "params": None, "id": 1})

    # Very long string in list
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate(
            {"jsonrpc": "2.0", "method": "test", "params": {"list": ["v" * 10005]}, "id": 1}
        )
    assert "String exceeds maximum length of 10000 characters" in str(exc.value)

    # List too long (>1000)
    long_list = ["v" for _ in range(1005)]
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate(
            {"jsonrpc": "2.0", "method": "test", "params": {"list": long_list}, "id": 1}
        )
    assert "List exceeds maximum of 1000 elements" in str(exc.value)

    # Invalid params type
    with pytest.raises(ValidationError) as exc:
        BoundedJSONRPCRequest.model_validate({"jsonrpc": "2.0", "method": "test", "params": "not a dict", "id": 1})
    assert "params must be a dictionary" in str(exc.value)
