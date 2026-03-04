# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class PrivacyMaskingZone(CoreasonBaseModel):
    """
    A schema defining application bounds or coordinate boxes that the ambient listener must completely ignore.

    This forms a crucial part of the 2026 Zero-UI and Edge Privacy architecture, ensuring that
    sensitive contexts (e.g., password managers, messaging apps) are strictly excluded from
    environmental exhaust telemetry.
    """

    app_name_regex: str | None = Field(
        default=None,
        description="Optional regex to match application names that should be masked.",
    )
    bounding_box_coordinates: list[int] | None = Field(
        default=None,
        description="Optional list of integers representing the [x, y, width, height] of the masking zone.",
    )
    is_strict_enforce: bool = Field(
        ...,
        description="If true, enforcement of the mask is mandatory and failure to mask will drop the telemetry frame.",
    )


class MultimodalTelemetryStream(CoreasonBaseModel):
    """
    A schema extending standard text-based telemetry to include passive environmental exhaust.

    In the 2026 Zero-UI architecture, this contract allows external clients to stream
    multimodal (audio/screen) context to the orchestrator while adhering to strict
    privacy and performance constraints.
    """

    audio_exhaust_enabled: bool = Field(
        ...,
        description="Whether background speech-to-text environmental exhaust is active.",
    )
    screen_capture_framerate: float = Field(
        ...,
        le=1.0,
        description="The FPS of semantic screen extraction. Must be strictly <= 1.0 FPS to prevent battery drain.",
    )
    privacy_masking_zones: list[PrivacyMaskingZone] = Field(
        default_factory=list,
        description="List of zones that must be masked out of the screen capture before processing.",
    )
