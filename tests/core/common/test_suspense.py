import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.suspense import SkeletonType, SuspenseConfig
from coreason_manifest.core.telemetry.suspense_envelope import StreamSuspenseEnvelope


def test_skeleton_type_enum():
    """Test that all required fallback types are correctly defined."""
    assert SkeletonType.TEXT_SHIMMER == "text_shimmer"
    assert SkeletonType.MEDIA_BLOCK == "media_block"
    assert SkeletonType.CHART_PULSE == "chart_pulse"
    assert SkeletonType.TABLE_ROWS == "table_rows"
    assert SkeletonType.SPINNER == "spinner"


def test_suspense_config_defaults():
    """Test default initialization of SuspenseConfig."""
    config = SuspenseConfig()
    assert config.fallback_type == SkeletonType.SPINNER
    assert config.estimated_duration_ms is None
    assert config.reserved_height is None


@pytest.mark.parametrize("valid_height", ["100px", "2.5rem", "1em", "50vh", "100vw", "10%"])
def test_suspense_config_valid_reserved_height(valid_height):
    """Test SuspenseConfig accepts valid CSS dimensions for reserved_height."""
    config = SuspenseConfig(reserved_height=valid_height)
    assert config.reserved_height == valid_height


@pytest.mark.parametrize("invalid_height", ["tall", "100", "px", "100abc", "10.0.0px"])
def test_suspense_config_invalid_reserved_height(invalid_height):
    """Test SuspenseConfig rejects invalid CSS dimensions."""
    with pytest.raises(ValidationError):
        SuspenseConfig(reserved_height=invalid_height)


def test_stream_suspense_envelope_valid():
    """Test successful initialization of StreamSuspenseEnvelope."""
    config = SuspenseConfig(fallback_type=SkeletonType.TEXT_SHIMMER, estimated_duration_ms=500, reserved_height="200px")

    envelope = StreamSuspenseEnvelope(op="suspense_mount", p=config, target_node_id="node_123", timestamp=123456789.0)

    assert envelope.op == "suspense_mount"
    assert envelope.p == config
    assert envelope.target_node_id == "node_123"
    assert envelope.timestamp == 123456789.0


def test_stream_suspense_envelope_invalid_op():
    """Test that StreamSuspenseEnvelope rejects invalid operations."""
    config = SuspenseConfig()

    with pytest.raises(ValidationError):
        StreamSuspenseEnvelope(
            op="invalid_mount",  # type: ignore
            p=config,
            timestamp=123456789.0,
        )
