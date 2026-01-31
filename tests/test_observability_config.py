import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import ObservabilityConfig, TraceLevel


def test_observability_config_valid() -> None:
    """Test creating a valid ObservabilityConfig."""
    obs = ObservabilityConfig(
        trace_level=TraceLevel.METADATA_ONLY, retention_policy="90_days", encryption_key_id="key-123"
    )
    assert obs.trace_level == TraceLevel.METADATA_ONLY
    assert obs.retention_policy == "90_days"
    assert obs.encryption_key_id == "key-123"


def test_observability_config_defaults() -> None:
    """Test defaults for ObservabilityConfig."""
    obs = ObservabilityConfig()
    assert obs.trace_level == TraceLevel.FULL
    assert obs.retention_policy == "30_days"
    assert obs.encryption_key_id is None


def test_observability_config_invalid_trace_level() -> None:
    """Test invalid trace level."""
    with pytest.raises(ValidationError):
        ObservabilityConfig(trace_level="invalid")  # type: ignore
