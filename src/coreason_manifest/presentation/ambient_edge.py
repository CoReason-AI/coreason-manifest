# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from coreason_manifest.presentation.ambient import AmbientListenerConfig
from coreason_manifest.telemetry.ambient_schemas import MultimodalTelemetryStream


class EdgeSLMProcessor(BaseModel):
    """
    A schema configuring the local Small Language Model (running on the user's device).

    This processor is responsible for extracting semantic triplets from the raw
    `MultimodalTelemetryStream` locally to preserve privacy and reduce latency
    in our 2026 Zero-UI architecture.
    """

    model_quantization: Literal["int4", "int8", "fp16"] = Field(
        ...,
        description="The quantization level of the SLM deployed on the edge device.",
    )
    max_latency_ms: int = Field(
        ...,
        description="Hard constraint for edge processing. Must be < 250ms to guarantee zero UI blocking.",
    )
    local_feature_extraction_only: bool = Field(
        ...,
        description=(
            "If true, prevents raw telemetry from *ever* leaving the local device, "
            "only transmitting the extracted semantic embeddings to the cloud."
        ),
    )

    @model_validator(mode="after")
    def validate_max_latency_ms(self) -> "EdgeSLMProcessor":
        if self.max_latency_ms >= 250:
            raise ValueError("max_latency_ms must be < 250ms to guarantee zero UI blocking.")
        return self


class AutonomousPrecomputeIntent(BaseModel):
    """
    A schema representing a 'shadow task' in the 2026 Zero-UI architecture.

    When the `EdgeSLMProcessor` predicts what the user is about to do, it emits
    this intent to pre-warm the cache or run heavy database queries silently
    in the background.
    """

    predicted_query_hash: str = Field(
        ...,
        description="Unique identifier for the anticipated task to pre-compute.",
    )
    confidence_score: float = Field(
        ...,
        description="Prediction confidence from 0.0 to 1.0.",
    )
    background_resource_allocation_mb: int = Field(
        ...,
        description="Max memory the shadow task can consume in megabytes.",
    )
    auto_inject_ui_target: str | None = Field(
        default=None,
        description="A DOM or application pointer where the results should be streamed if prediction is correct.",
    )

    @model_validator(mode="after")
    def validate_confidence_score(self) -> "AutonomousPrecomputeIntent":
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0.")
        return self


class EdgeNativeAmbientListener(BaseModel):
    """
    The composite schema that an application mounts on startup for Edge-Native ambient observation.

    It binds the base listener config, telemetry stream, local SLM config,
    and thresholds to orchestrate the next-generation Zero-UI experience.
    """

    base_config: AmbientListenerConfig = Field(
        ...,
        description="Base configuration for ambient listening triggers.",
    )
    telemetry_stream: MultimodalTelemetryStream = Field(
        ...,
        description="Configuration for the multimodal passive environmental exhaust.",
    )
    edge_processor: EdgeSLMProcessor = Field(
        ...,
        description="Local Small Language Model configuration.",
    )
    precompute_threshold: float = Field(
        ...,
        description="The minimum confidence_score required to trigger an AutonomousPrecomputeIntent.",
    )
