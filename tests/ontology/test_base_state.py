# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for CoreasonBaseState fundamentals: hashing, canonical serialization, payload bounds."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    EpistemicProxyState,
    GradingCriterionProfile,
    _canonicalize_payload,
    _validate_payload_bounds,
)

# ---------------------------------------------------------------------------
# _validate_payload_bounds
# ---------------------------------------------------------------------------


class TestValidatePayloadBounds:
    """Exercise all branches of _validate_payload_bounds."""

    @given(st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=20, deadline=None)
    def test_integer_passes(self, v: int) -> None:
        assert _validate_payload_bounds(v) == v

    @given(st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=20, deadline=None)
    def test_float_passes(self, v: float) -> None:
        assert _validate_payload_bounds(v) == v

    @given(st.booleans())
    @settings(max_examples=2, deadline=None)
    def test_bool_passes(self, v: bool) -> None:
        assert _validate_payload_bounds(v) == v

    def test_none_passes(self) -> None:
        assert _validate_payload_bounds(None) is None

    @given(st.text(max_size=100))
    @settings(max_examples=20, deadline=None)
    def test_short_string_passes(self, v: str) -> None:
        assert _validate_payload_bounds(v) == v

    def test_string_exceeds_max_length(self) -> None:
        long_str = "x" * 10001
        with pytest.raises(ValueError, match="max length"):
            _validate_payload_bounds(long_str)

    def test_dict_key_exceeds_max_length(self) -> None:
        long_key = "k" * 10001
        with pytest.raises(ValueError, match="max string length"):
            _validate_payload_bounds({long_key: "v"})

    def test_dict_key_not_string(self) -> None:
        with pytest.raises(ValueError, match="Dictionary keys must be strings"):
            _validate_payload_bounds({123: "v"})  # type: ignore[dict-item]

    def test_exceeds_max_recursion_depth(self) -> None:
        nested: dict = {"a": None}  # type: ignore[type-arg]
        current = nested
        for _ in range(15):
            child: dict = {"a": None}  # type: ignore[type-arg]
            current["a"] = child
            current = child
        with pytest.raises(ValueError, match="recursion depth"):
            _validate_payload_bounds(nested)

    def test_exceeds_max_nodes(self) -> None:
        # Build a flat list exceeding 10000 nodes
        big_list = list(range(10002))
        with pytest.raises(ValueError, match="hardware limit"):
            _validate_payload_bounds(big_list)  # type: ignore[arg-type]

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError, match="valid JSON primitive"):
            _validate_payload_bounds(object())  # type: ignore[arg-type]

    def test_nested_dict_validates_recursively(self) -> None:
        payload = {"a": {"b": {"c": [1, "two", True, None]}}}
        result = _validate_payload_bounds(payload)  # type: ignore[arg-type]
        assert result == payload

    def test_list_with_nested_content(self) -> None:
        payload = [{"key": "val"}, [1, 2, 3], "hello"]
        result = _validate_payload_bounds(payload)  # type: ignore[arg-type]
        assert result == payload


# ---------------------------------------------------------------------------
# _canonicalize_payload
# ---------------------------------------------------------------------------


class TestCanonicalizePayload:
    """Exercise all branches of _canonicalize_payload."""

    def test_removes_none_from_dict(self) -> None:
        assert _canonicalize_payload({"a": 1, "b": None, "c": "x"}) == {"a": 1, "c": "x"}

    def test_preserves_list_order(self) -> None:
        assert _canonicalize_payload([3, None, 1]) == [3, None, 1]

    def test_nested_dict_none_removal(self) -> None:
        result = _canonicalize_payload({"a": {"b": None, "c": 1}})
        assert result == {"a": {"c": 1}}

    def test_primitive_passthrough(self) -> None:
        assert _canonicalize_payload(42) == 42
        assert _canonicalize_payload("hello") == "hello"
        assert _canonicalize_payload(True) is True


# ---------------------------------------------------------------------------
# CoreasonBaseState.__hash__ and model_dump_canonical
# ---------------------------------------------------------------------------


class TestCoreasonBaseStateHashing:
    """Verify deterministic hashing and caching."""

    def test_hash_is_deterministic(self) -> None:
        obj = GradingCriterionProfile(criterion_cid="test-1", description="desc", weight=1.0)
        h1 = hash(obj)
        h2 = hash(obj)
        assert h1 == h2

    def test_hash_cached(self) -> None:
        obj = GradingCriterionProfile(criterion_cid="test-2", description="desc", weight=2.0)
        h1 = hash(obj)
        h2 = hash(obj)
        assert h1 == h2

    def test_canonical_dump_cached(self) -> None:
        obj = GradingCriterionProfile(criterion_cid="test-3", description="desc", weight=3.0)
        dump1 = obj.model_dump_canonical()
        dump2 = obj.model_dump_canonical()
        assert dump1 == dump2
        assert isinstance(dump1, bytes)

    def test_canonical_dump_is_bytes(self) -> None:
        obj = GradingCriterionProfile(criterion_cid="test-4", description="desc", weight=0.5)
        result = obj.model_dump_canonical()
        assert isinstance(result, bytes)

    @given(
        cid=st.from_regex(r"[a-zA-Z0-9_.:-]{1,30}", fullmatch=True),
        weight=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    )
    @settings(max_examples=20, deadline=None)
    def test_equal_objects_have_equal_hash(self, cid: str, weight: float) -> None:
        obj1 = GradingCriterionProfile(criterion_cid=cid, description="d", weight=weight)
        obj2 = GradingCriterionProfile(criterion_cid=cid, description="d", weight=weight)
        assert hash(obj1) == hash(obj2)


# ---------------------------------------------------------------------------
# EpistemicProxyState
# ---------------------------------------------------------------------------


class TestEpistemicProxyState:
    """Test the generic proxy state."""

    def test_valid_proxy(self) -> None:
        proxy = EpistemicProxyState(proxy_cid="test.proxy:1", structural_type="List[str]")  # type: ignore[var-annotated]
        assert proxy.proxy_cid == "test.proxy:1"

    def test_invalid_proxy_cid_pattern(self) -> None:
        with pytest.raises(ValidationError):
            EpistemicProxyState(proxy_cid="invalid chars!!", structural_type="str")
