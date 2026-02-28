from typing import Literal

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel


class AllocationRule(CoreasonModel):
    condition: str
    target_queue: str


class BoundedAutonomyConfig(CoreasonModel):
    intervention_window_seconds: int
    timeout_behavior: Literal["proceed", "escalate", "fail"]


class MixedInitiativePolicy(CoreasonModel):
    enable_shadow_telemetry: bool = False
    bounded_autonomy: BoundedAutonomyConfig | None = None
    dynamic_allocation_rules: list[AllocationRule] = Field(default_factory=list)
