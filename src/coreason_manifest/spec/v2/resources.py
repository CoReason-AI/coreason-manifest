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


class PricingUnit(StrEnum):
    """Unit of measurement for pricing."""

    TOKEN_1K = "TOKEN_1K"
    TOKEN_1M = "TOKEN_1M"
    REQUEST = "REQUEST"
    SECOND = "SECOND"


class Currency(StrEnum):
    """Currency for pricing."""

    USD = "USD"
    EUR = "EUR"


class RateCard(CoReasonBaseModel):
    """Pricing details for a resource."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    unit: PricingUnit = Field(PricingUnit.TOKEN_1M, description="Unit of pricing.")
    currency: Currency = Field(Currency.USD, description="Currency.")
    input_cost: float = Field(..., description="Cost per unit for input/prompt.")
    output_cost: float = Field(..., description="Cost per unit for output/completion.")
    fixed_cost_per_request: float = Field(0.0, description="Optional base fee.")


class ResourceConstraints(CoReasonBaseModel):
    """Technical limitations and constraints."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    context_window_size: int = Field(..., ge=0, description="Total tokens supported.")
    max_output_tokens: int | None = Field(None, ge=0, description="Limit on generation.")
    rate_limit_rpm: int | None = Field(None, ge=0, description="Requests per minute.")
    rate_limit_tpm: int | None = Field(None, ge=0, description="Tokens per minute.")


class ModelProfile(CoReasonBaseModel):
    """Resource profile describing hardware, pricing, and operational constraints."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    provider: str = Field(..., description="Provider name (e.g. openai).")
    model_id: str = Field(..., description="The technical ID (e.g. gpt-4).")
    pricing: RateCard | None = Field(None, description="Financials.")
    constraints: ResourceConstraints | None = Field(None, description="Technical limits.")
