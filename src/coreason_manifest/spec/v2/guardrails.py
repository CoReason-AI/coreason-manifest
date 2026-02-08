# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum
from pydantic import ConfigDict, Field
from coreason_manifest.spec.common_base import CoReasonBaseModel

class BreakerScope(StrEnum):
    """What gets locked when the breaker trips."""
    AGENT = "agent"             # Only this specific agent is disabled
    RECIPE = "recipe"           # The entire workflow is paused
    GLOBAL = "global"           # The entire system pauses (rare)

class CircuitBreakerConfig(CoReasonBaseModel):
    """Rules for stopping execution when error rates spike."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    failure_rate_threshold: float = Field(
        0.5,
        ge=0.0, le=1.0,
        description="Trigger if error rate exceeds this (e.g. 0.5 = 50%)."
    )
    window_seconds: int = Field(60, description="Time window to calculate the rate.")
    recovery_timeout_seconds: int = Field(300, description="How long to block before testing recovery.")
    scope: BreakerScope = Field(BreakerScope.AGENT, description="Blast radius of the breaker.")

class DriftConfig(CoReasonBaseModel):
    """Configuration for semantic drift detection."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    input_drift_threshold: float | None = Field(
        None,
        description="Max allowed distance from baseline for inputs. Lower is stricter."
    )
    output_drift_threshold: float | None = Field(
        None,
        description="Max allowed distance from baseline for outputs."
    )
    baseline_dataset_id: str | None = Field(
        None,
        description="Reference to the dataset used as the 'normal' baseline."
    )

class GuardrailsConfig(CoReasonBaseModel):
    """Container for active defense settings."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    circuit_breaker: CircuitBreakerConfig | None = Field(None, description="Automated stoppage rules.")
    drift_check: DriftConfig | None = Field(None, description="OOD (Out of Distribution) detection rules.")
    spot_check_rate: float = Field(
        0.0,
        ge=0.0, le=1.0,
        description="Percentage of traces to flag for human review (0.0 to 1.0)."
    )
