import pytest
from pydantic import ValidationError

from coreason_manifest.telemetry.ambient_schemas import (
    MultimodalTelemetryStream,
    PrivacyMaskingZone,
)


def test_privacy_masking_zone_valid() -> None:
    """Test valid instantiation of PrivacyMaskingZone."""
    zone = PrivacyMaskingZone(
        app_name_regex="^1Password$",
        bounding_box_coordinates=[0, 0, 100, 100],
        is_strict_enforce=True,
    )
    assert zone.app_name_regex == "^1Password$"
    assert zone.bounding_box_coordinates == [0, 0, 100, 100]
    assert zone.is_strict_enforce is True


def test_multimodal_telemetry_stream_valid() -> None:
    """Test valid instantiation of MultimodalTelemetryStream."""
    zone = PrivacyMaskingZone(
        app_name_regex="^1Password$",
        bounding_box_coordinates=None,
        is_strict_enforce=True,
    )
    stream = MultimodalTelemetryStream(
        audio_exhaust_enabled=True,
        screen_capture_framerate=0.5,
        privacy_masking_zones=[zone],
    )
    assert stream.audio_exhaust_enabled is True
    assert stream.screen_capture_framerate == 0.5
    assert len(stream.privacy_masking_zones) == 1
    assert stream.privacy_masking_zones[0].app_name_regex == "^1Password$"


def test_multimodal_telemetry_stream_invalid_framerate() -> None:
    """Test that a screen capture framerate higher than 1.0 raises a ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        MultimodalTelemetryStream(
            audio_exhaust_enabled=False,
            screen_capture_framerate=1.5,
            privacy_masking_zones=[],
        )

    assert "Input should be less than or equal to 1" in str(excinfo.value)
