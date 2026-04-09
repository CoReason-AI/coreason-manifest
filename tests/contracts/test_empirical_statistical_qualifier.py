import pytest
from pydantic import ValidationError
from coreason_manifest.spec.ontology import EmpiricalStatisticalQualifier

def test_valid_empirical_statistical_qualifier():
    q = EmpiricalStatisticalQualifier(
        qualifier_type="probability_value",
        algebraic_operator="le",
        value=0.05,
        lower_bound=0.01,
        upper_bound=0.1
    )
    assert q.value == 0.05

def test_invalid_interval_geometry():
    with pytest.raises(ValidationError) as exc_info:
        EmpiricalStatisticalQualifier(
            qualifier_type="confidence_interval",
            algebraic_operator="eq",
            value=0.95,
            lower_bound=0.5,
            upper_bound=0.2
        )
    assert "lower_bound must be strictly less than upper_bound" in str(exc_info.value)
