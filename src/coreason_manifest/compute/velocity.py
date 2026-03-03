from enum import StrEnum

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


class ComputeIntent(StrEnum):
    """Execution intent profiles that drive hardware routing decisions."""

    REALTIME_SYNC = "REALTIME_SYNC"
    BATCH_BACKGROUND = "BATCH_BACKGROUND"


class VelocityAConfig(CoreasonModel):
    """
    Velocity A: Real-Time execution profile.
    Optimized for low-latency, user-facing interactions. Enables serverless burst and allows fallback
    to smaller models (graceful epistemic degradation) to preserve SLAs.
    """

    max_latency_seconds: int = Field(
        default=60,
        description="Strict latency budget. Exceeding this triggers a LatencySLAExceededError.",
    )
    allow_model_downgrade: bool = Field(
        ...,
        description="Whether to permit Graceful Epistemic Degradation to preserve SLA.",
    )
    target_compute_tier: str = Field(
        ...,
        description="Expected compute tier, e.g., 'serverless_burst'.",
    )


class VelocityBConfig(CoreasonModel):
    """
    Velocity B: Background/Batch execution profile.
    Optimized for throughput over latency. Uses spot/preemptible fleets to maximize cost efficiency.
    Fault-tolerant design ensures preemption interrupts do not break data lineage.
    """

    max_retries: int = Field(
        default=-1,
        description="Number of retries for interrupted executions. -1 indicates infinite retries.",
    )
    preemption_safe: bool = Field(
        ...,
        description="Must be True to explicitly acknowledge fault-tolerance requirements.",
    )
    target_compute_tier: str = Field(
        ...,
        description="Expected compute tier, e.g., 'spot_fleet'.",
    )
