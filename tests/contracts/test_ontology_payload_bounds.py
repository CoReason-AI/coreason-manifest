# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at [https://prosperitylicense.com/versions/3.0.0](https://prosperitylicense.com/versions/3.0.0)
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: [https://github.com/CoReason-AI/coreason-manifest](https://github.com/CoReason-AI/coreason-manifest)

from typing import Any, cast

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings

from coreason_manifest.spec.ontology import JsonPrimitiveState, StateHydrationManifest, _validate_payload_bounds

# 1. Define the Valid Mathematical Space
valid_json_st = st.recursive(
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.integers()
    | st.text(max_size=9999),
    lambda children: (
        st.lists(children, max_size=999) | st.dictionaries(st.text(min_size=1, max_size=9999), children, max_size=99)
    ),
    max_leaves=50,
)


@given(payload=valid_json_st)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_payload_bounds_fuzz_valid_space(payload: Any) -> None:
    """
    AGENT INSTRUCTION: Fuzz the valid structural space using hypothesis.
    Mathematically prove that any permutation falling UNDER the tripwires is strictly accepted.
    """
    # 1. Direct Function Fuzzing
    result = _validate_payload_bounds(payload)
    assert result == payload

    # 2. Pydantic Manifest Projection
    if isinstance(payload, dict):
        manifest = StateHydrationManifest(
            epistemic_coordinate="session-123",
            crystallized_ledger_cids=["a" * 64],
            working_context_variables=payload,
            max_retained_tokens=4000,
        )
        assert manifest.working_context_variables == payload


def test_payload_bounds_recursion_depth_exceeded() -> None:
    # Create a nested dictionary of depth 11 (max is 10)
    nested_payload: Any = "leaf"
    for _ in range(11):
        nested_payload = {"key": nested_payload}

    with pytest.raises(ValueError, match="Payload exceeds maximum recursion depth of 10"):
        _validate_payload_bounds(nested_payload)


def test_payload_bounds_dict_keys_exceeded() -> None:
    # Create a dictionary with 101 keys (max is 100)
    large_dict: dict[str, Any] = {f"key_{i}": i for i in range(101)}

    with pytest.raises(ValueError, match="Dictionary exceeds maximum key count of 100"):
        _validate_payload_bounds(cast("JsonPrimitiveState", large_dict))


def test_payload_bounds_list_items_exceeded() -> None:
    # Create a list with 1001 items (max is 1000)
    large_list: list[Any] = list(range(1001))

    with pytest.raises(ValueError, match="List exceeds maximum item count of 1000"):
        _validate_payload_bounds(cast("JsonPrimitiveState", large_list))


def test_payload_bounds_string_length_exceeded() -> None:
    # Create a string of length 10001 (max is 10000)
    large_string = "a" * 10001

    with pytest.raises(ValueError, match="String exceeds max length of 10000"):
        _validate_payload_bounds(large_string)


def test_payload_bounds_dict_key_length_exceeded() -> None:
    # Create a dictionary with a key of length 10001 (max string length is 10000)
    large_key = "a" * 10001
    bad_dict: dict[str, Any] = {large_key: "value"}

    with pytest.raises(ValueError, match="Dictionary key exceeds max string length of 10000"):
        _validate_payload_bounds(cast("JsonPrimitiveState", bad_dict))


def test_payload_bounds_dict_key_not_string() -> None:
    # JSON standard allows only string keys for dictionaries
    bad_dict: dict[Any, Any] = {42: "value"}

    with pytest.raises(ValueError, match="Dictionary keys must be strings"):
        _validate_payload_bounds(cast("JsonPrimitiveState", bad_dict))


def test_payload_bounds_invalid_type() -> None:
    # A non-JSON primitive object should fail validation
    class CustomObj:
        pass

    with pytest.raises(ValueError, match="Payload value must be a valid JSON primitive, got CustomObj"):
        _validate_payload_bounds(CustomObj())  # type: ignore


def test_payload_bounds_invalid_type_nested() -> None:
    # A non-JSON primitive object deeply nested should fail validation
    class CustomObj:
        pass

    payload = {"valid": 1, "invalid": [1, 2, CustomObj()]}

    with pytest.raises(ValueError, match="Payload value must be a valid JSON primitive, got CustomObj"):
        _validate_payload_bounds(payload)  # type: ignore
