# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class EmbodiedSensoryVector(CoreasonBaseModel):
    sensory_modality: Literal["video", "audio", "spatial_telemetry"] = Field(
        description="The continuous data stream being monitored."
    )
    bayesian_surprise_score: float = Field(
        ge=0.0,
        description="The calculated KL divergence between the agent's prior belief and the incoming sensory evidence.",
    )
    temporal_duration_ms: int = Field(
        gt=0,
        le=86400000,
        description="The exact length of the continuous stream segment encapsulated by this observation.",
    )
    salience_threshold_breached: bool = Field(
        default=True, description="Mathematical proof that the anomaly was severe enough to warrant a memory snapshot."
    )
