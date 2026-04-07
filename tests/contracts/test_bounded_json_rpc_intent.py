# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BoundedJSONRPCIntent

# 1. Define the Valid Mathematical Space for BoundedJSONRPCIntent params
scalar_st = (
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.integers()
    | st.text(max_size=9999)
)

valid_params_st = st.dictionaries(
    keys=st.text(min_size=1, max_size=999),
    values=st.recursive(
        scalar_st,
        lambda children: (
            st.lists(children, max_size=999) | st.dictionaries(st.text(min_size=1, max_size=999), children, max_size=99)
        ),
        max_leaves=10,
    ),
    max_size=99,
)


@given(params=st.one_of(st.none(), valid_params_st))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_bounded_json_rpc_intent_fuzz_valid_space(params: dict[str, Any] | None) -> None:
    """
    AGENT INSTRUCTION: Fuzz the valid structural space using hypothesis.
    Mathematically prove that any params payload falling UNDER the topological
    tripwires is strictly accepted without false positives.
    """
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="fuzzed_method", params=params, id=1)

    # BoundedJSONRPCIntent no longer normalizes None to {}
    expected_params = None if params is None else params
    assert intent.params == expected_params


# --- RETAIN ALL ATOMIC BOUNDARY TESTS BELOW THIS LINE ---


def test_json_rpc_intent_max_depth() -> None:
    params: dict[str, Any] = {}
    current = params
    for _i in range(11):
        current["key"] = {}
        current = current["key"]

    with pytest.raises(ValidationError, match="Payload exceeds maximum recursion depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_dict_keys() -> None:
    # Build a dictionary large enough to exceed the 10000 limit
    params: dict[str, Any] = {f"key_{i}": i for i in range(10001)}

    with pytest.raises(ValidationError, match="Payload volume exceeds absolute hardware limit of 10000 nodes"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_dict_key_length() -> None:
    params: dict[str, Any] = {"k" * 10001: "value"}

    with pytest.raises(ValidationError, match="Volumetric Boundary Breach: Dictionary key string geometry exceeds absolute maximum topological length of 10000."):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_list_elements() -> None:
    params: dict[str, Any] = {"list": [1] * 10001}

    with pytest.raises(ValidationError, match="Payload volume exceeds absolute hardware limit of 10000 nodes"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_max_string_length() -> None:
    params: dict[str, Any] = {"key": "v" * 10001}

    with pytest.raises(ValidationError, match="String exceeds max length of 10000"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=params, id=1)


def test_json_rpc_intent_params_not_dict() -> None:
    with pytest.raises(ValidationError, match="Input should be a valid dictionary"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method", params=[1, 2, 3], id=1)  # type: ignore[arg-type]
