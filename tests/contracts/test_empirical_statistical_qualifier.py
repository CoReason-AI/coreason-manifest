import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import EmpiricalStatisticalQualifier


# Test valid cases where lower_bound is strictly less than upper_bound
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=0.01, max_value=100),
)
def test_valid_interval_geometry(lower, diff):
    upper = lower + diff
    q = EmpiricalStatisticalQualifier(
        qualifier_type="confidence_interval",
        algebraic_operator="le",
        value=lower + (diff / 2),
        lower_bound=lower,
        upper_bound=upper,
    )
    assert q.lower_bound < q.upper_bound


# Test invalid cases where lower_bound >= upper_bound
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=100),
)
def test_invalid_interval_geometry_hypothesis(upper, diff):
    lower = upper + diff  # This ensures lower >= upper
    with pytest.raises(ValidationError) as exc_info:
        EmpiricalStatisticalQualifier(
            qualifier_type="confidence_interval",
            algebraic_operator="eq",
            value=upper,
            lower_bound=lower,
            upper_bound=upper,
        )
    assert "lower_bound must be strictly less than upper_bound" in str(exc_info.value)
