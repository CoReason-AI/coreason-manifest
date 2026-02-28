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

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel


class AllocationRule(CoreasonModel):
    """Dynamic task allocation rule."""

    condition: str = Field(..., description="Expression to evaluate, e.g., 'confidence < 0.8'.")
    target_queue: str = Field(..., description="The human oracle queue to route the task to.")


class BoundedAutonomyConfig(CoreasonModel):
    """Configuration for bounded autonomy and time-boxed interventions."""

    intervention_window_seconds: int = Field(..., description="Time to wait for supervisory input.")
    timeout_behavior: Literal["proceed", "escalate", "fail"] = Field(
        ..., description="System behavior if the intervention window expires."
    )


class MixedInitiativePolicy(CoreasonModel):
    """Mixed-Initiative Control System policy for Human-AI interaction."""

    enable_shadow_telemetry: bool = Field(
        default=False, description="Broadcast live state to observers without blocking execution (HOTL)."
    )
    bounded_autonomy: BoundedAutonomyConfig | None = Field(default=None, description="Time-boxed authorization limits.")
    dynamic_allocation_rules: list[AllocationRule] = Field(
        default_factory=list, description="Exception-based routing to human supervisors."
    )
