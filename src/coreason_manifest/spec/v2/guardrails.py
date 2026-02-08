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
    """Scope for the Circuit Breaker."""

    AGENT = "agent"
    RECIPE = "recipe"
    GLOBAL = "global"


class CircuitBreakerConfig(CoReasonBaseModel):
    """Configuration for automated stoppage rules."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    failure_rate_threshold: float = Field(..., ge=0.0, le=1.0, description="Error rate to trigger break.")
    window_seconds: int = Field(..., ge=1, description="Time window for error calculation.")
    recovery_timeout_seconds: int = Field(..., ge=1, description="Time to wait before retry.")
    scope: BreakerScope = Field(BreakerScope.AGENT, description="Scope of the breaker.")


class DriftConfig(CoReasonBaseModel):
    """Configuration for semantic drift detection."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    input_drift_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Max allowed input semantic drift.")
    output_drift_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Max allowed output semantic drift.")
    baseline_dataset_id: str | None = Field(None, description="Dataset ID for baseline comparison.")


class GuardrailsConfig(CoReasonBaseModel):
    """Active Defense configuration."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    circuit_breaker: CircuitBreakerConfig | None = Field(None, description="Circuit breaker settings.")
    drift_check: DriftConfig | None = Field(None, description="Drift detection settings.")
    spot_check_rate: float | None = Field(None, ge=0.0, le=1.0, description="Probability of human spot check.")
