from enum import StrEnum
from typing import Any

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.compute.velocity import (
    ComputeIntent,
    VelocityAConfig,
    VelocityBConfig,
)


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    CREDITS = "CREDITS"


class PricingUnit(StrEnum):
    TOKEN_1K = "TOKEN_1K"  # noqa: S105
    TOKEN_1M = "TOKEN_1M"  # noqa: S105
    REQUEST = "REQUEST"


class RateCard(CoreasonModel):
    input_cost: float = Field(..., ge=0.0, description="Cost for input processing per unit.", examples=[0.01])
    output_cost: float = Field(..., ge=0.0, description="Cost for output generation per unit.", examples=[0.03])
    reasoning_cost: float | None = Field(
        None,
        ge=0.0,
        description="Cost specifically for internal reasoning or thinking tokens per unit.",
        examples=[0.05],
    )
    unit: PricingUnit = Field(
        default=PricingUnit.TOKEN_1M, description="The unit of measurement for the cost.", examples=["TOKEN_1M"]
    )


class ModelProfile(CoreasonModel):
    provider: str = Field(..., description="The provider of the model.", examples=["openai", "anthropic"])
    model_id: str = Field(..., description="The unique identifier of the model.", examples=["o1-preview", "gpt-4o"])
    pricing: RateCard | None = Field(None, description="The rate card associated with the model's pricing.")


class IntentRouter:
    """
    Dynamically slices workloads into distinct SLA profiles based on intent.
    Routes tasks to appropriate compute hardware tiers (Velocity A vs B).
    """

    def route(self, task_def: Any, intent: ComputeIntent) -> VelocityAConfig | VelocityBConfig:  # noqa: ARG002
        """
        Evaluate task intent and generate the strict SLA configuration.
        """
        if intent == ComputeIntent.REALTIME_SYNC:
            # Velocity A: User-facing, latency matters, bursting mode.
            return VelocityAConfig(
                max_latency_seconds=60,
                allow_model_downgrade=True,
                target_compute_tier="serverless_burst",
            )
        if intent == ComputeIntent.BATCH_BACKGROUND:
            # Velocity B: Data-lake, throughput matters, preemptible node.
            return VelocityBConfig(
                max_retries=-1,
                preemption_safe=True,
                target_compute_tier="spot_fleet",
            )
        raise ValueError(f"Unknown compute intent: {intent}")


async def provision_compute(intent: ComputeIntent, task_def: Any = None) -> VelocityAConfig | VelocityBConfig:
    """
    Mock method to simulate requesting hardware from the orchestrator.
    Evaluates routing and returns the provisioned velocity configuration profile.
    """
    router = IntentRouter()
    return router.route(task_def, intent)
