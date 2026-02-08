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
from typing import Any

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


class ToolParameter(CoReasonBaseModel):
    """Parameter definition for a tool."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Parameter name.")
    type: str = Field(..., description="Data type of the parameter.")
    description: str = Field(..., description="Parameter description.")
    required: bool = Field(True, description="Whether the parameter is required.")


class ToolDefinition(CoReasonBaseModel):
    """Static definition of an MCP tool capability."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="The tool name (e.g., 'brave_search').")
    description: str = Field(..., description="What the tool does.")
    parameters: dict[str, Any] = Field(..., description="JSON Schema of inputs.")
    is_consequential: bool = Field(
        False, description="If True, coreason-mcp MUST require human approval before execution."
    )
    namespace: str | None = Field(None, description="Expected MCP server namespace (e.g., 'github').")


class McpServerRequirement(CoReasonBaseModel):
    """Declares that this recipe needs a specific MCP server available."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Server name.")
    required_tools: list[str] = Field(default_factory=list, description="List of required tools.")
    version_constraint: str | None = Field(None, description="Version constraint.")


class RuntimeEnvironment(CoReasonBaseModel):
    """The infrastructure requirements for the recipe."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    mcp_servers: list[McpServerRequirement] = Field(default_factory=list, description="Required MCP servers.")
    python_version: str | None = Field("3.12", description="Required Python version.")
