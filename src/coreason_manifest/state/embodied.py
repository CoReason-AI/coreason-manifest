# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable embodied state schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
monotonic logic, standard CRUD database paradigms, or kinetic execution parameters. These models represent computable
geometric graphs of cognition and causal inference."""

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class EmbodiedSensoryVector(CoreasonBaseModel):
    sensory_modality: Literal["video", "audio", "spatial_telemetry"] = Field(
        description="Multimodal Sensor Fusion and Spatial-Temporal Bindings representing Proprioceptive State and "
        "Exteroceptive Vectors."
    )
    bayesian_surprise_score: float = Field(
        ge=0.0,
        description="The calculated KL divergence between the prior belief and the incoming structural evidence.",
    )
    temporal_duration_ms: int = Field(
        gt=0,
        le=86400000,
        description="The exact length of the timeline encapsulated by this observation.",
    )
    salience_threshold_breached: bool = Field(
        default=True, description="Continuous-to-Discrete Crystallization threshold being crossed."
    )
