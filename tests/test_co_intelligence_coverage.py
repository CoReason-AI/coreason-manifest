import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.co_intelligence import EscalationCriteria
from coreason_manifest.spec.core.nodes import SteeringConfig
from coreason_manifest.spec.interop.exceptions import ManifestError


def test_escalation_criteria_validation_syntax_error() -> None:
    """Test that invalid python syntax in condition raises ValueError."""
    with pytest.raises(ValidationError) as excinfo:
        EscalationCriteria(condition="this is not valid python", role="supervisor")
    assert "Invalid Python expression syntax" in str(excinfo.value)


def test_escalation_criteria_validation_security_violation_call() -> None:
    """Test that function calls are forbidden in condition."""
    with pytest.raises(ValidationError) as excinfo:
        EscalationCriteria(condition="print('evil')", role="supervisor")
    assert "Security Violation" in str(excinfo.value)


def test_steering_config_empty_allowed_targets() -> None:
    """
    Test that allowed_targets cannot be empty if mutation is allowed.
    This targets line 181 in nodes.py.
    """
    with pytest.raises(ManifestError) as excinfo:
        SteeringConfig(allow_variable_mutation=True, allowed_targets=[])

    error = excinfo.value
    # Fix: Access error_code via fault object
    assert error.fault.error_code == "CRSN-VAL-HUMAN-STEERING"
    assert "allowed_targets cannot be empty" in error.fault.message
