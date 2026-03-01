from enum import StrEnum

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


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
