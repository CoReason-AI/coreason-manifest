from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    CoreasonBaseState,
    InformationClassificationProfile,
    RiskLevelPolicy,
    _validate_payload_bounds,
)


class DummyState(CoreasonBaseState):
    a: int
    b: str
    c: list[int]
    d: dict[str, int]


@given(
    a=st.sampled_from(list(InformationClassificationProfile)),
    b=st.sampled_from(list(InformationClassificationProfile)),
)
def test_information_classification_profile_comparisons(
    a: InformationClassificationProfile, b: InformationClassificationProfile
) -> None:
    assert (a < b) == (a.clearance_level < b.clearance_level)
    assert (a <= b) == (a.clearance_level <= b.clearance_level)
    assert (a > b) == (a.clearance_level > b.clearance_level)
    assert (a >= b) == (a.clearance_level >= b.clearance_level)

    # Test NotImplemented paths manually
    assert a.__lt__("string") is NotImplemented
    assert a.__le__("string") is NotImplemented
    assert a.__gt__("string") is NotImplemented
    assert a.__ge__("string") is NotImplemented


@given(st.integers(), st.text(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers()))
def test_coreason_base_state_hash(a: int, b: str, c: list[int], d: dict[str, int]) -> None:
    obj = DummyState(a=a, b=b, c=c, d=d)

    # Check that initial hash accesses model_dump_canonical and caches
    h1 = hash(obj)

    # Check that second hash returns cached value
    h2 = hash(obj)
    assert h1 == h2

    # Verify cached attribute exists
    assert hasattr(obj, "_cached_hash")
    assert obj._cached_hash == h1


@given(st.integers(), st.text(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers()))
def test_model_dump_canonical(a: int, b: str, c: list[int], d: dict[str, int]) -> None:
    obj1 = DummyState(a=a, b=b, c=c, d=d)

    # Dictionary keys might be unsorted initially if we bypassed Pydantic's internal checks
    # But DummyState's model_dump_canonical should always sort dictionary keys
    canonical_bytes1 = obj1.model_dump_canonical()

    # Same inputs should produce identical canonical bytes
    obj2 = DummyState(a=a, b=b, c=c, d=d)
    canonical_bytes2 = obj2.model_dump_canonical()

    assert canonical_bytes1 == canonical_bytes2


@given(
    st.recursive(
        st.none()
        | st.booleans()
        | st.floats(allow_nan=False, allow_infinity=False)
        | st.integers()
        | st.text(max_size=10000),
        lambda children: (
            st.lists(children, max_size=10) | st.dictionaries(st.text(max_size=10000), children, max_size=10)
        ),
        max_leaves=10,
    )
)
def test_validate_payload_bounds_valid(payload: Any) -> None:
    # Should not raise any exceptions
    _validate_payload_bounds(payload)


def test_validate_payload_bounds_invalid_type() -> None:
    with pytest.raises(ValueError, match="Payload value must be a valid JSON primitive"):
        _validate_payload_bounds(object())  # type: ignore[arg-type]


def test_validate_payload_bounds_invalid_dict_key() -> None:
    with pytest.raises(ValueError, match="Dictionary keys must be strings"):
        _validate_payload_bounds({1: "test"})  # type: ignore[dict-item]


def test_validate_payload_bounds_invalid_dict_key_length() -> None:
    with pytest.raises(ValueError, match="Dictionary key exceeds max string length"):
        _validate_payload_bounds({"a" * 10001: "test"})


def test_validate_payload_bounds_invalid_string_length() -> None:
    with pytest.raises(ValueError, match="String exceeds max length"):
        _validate_payload_bounds("a" * 10001)


def test_validate_payload_bounds_invalid_depth() -> None:
    payload: Any = "test"
    for _ in range(12):
        payload = {"key": payload}
    with pytest.raises(ValueError, match="Payload exceeds maximum recursion depth"):
        _validate_payload_bounds(payload)


def test_validate_payload_bounds_invalid_list_length() -> None:
    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit of 10000 nodes"):
        _validate_payload_bounds([1] * 10001)


def test_validate_payload_bounds_invalid_dict_length() -> None:
    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit of 10000 nodes"):
        _validate_payload_bounds({str(i): 1 for i in range(10001)})


@given(
    a=st.sampled_from(list(RiskLevelPolicy)),
    b=st.sampled_from(list(RiskLevelPolicy)),
)
def test_risk_level_policy_comparisons(a: RiskLevelPolicy, b: RiskLevelPolicy) -> None:
    assert (a < b) == (a.weight < b.weight)
    assert (a <= b) == (a.weight <= b.weight)
    assert (a > b) == (a.weight > b.weight)
    assert (a >= b) == (a.weight >= b.weight)

    # Test NotImplemented paths manually
    assert a.__lt__("string") is NotImplemented
    assert a.__le__("string") is NotImplemented
    assert a.__gt__("string") is NotImplemented
    assert a.__ge__("string") is NotImplemented
