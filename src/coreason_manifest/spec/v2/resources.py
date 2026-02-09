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

from coreason_manifest.spec.common_base import ManifestBaseModel


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


class RateCard(ManifestBaseModel):
    """
    Pricing details for a resource.

    Attributes:
        unit (PricingUnit): Unit of pricing. (Default: TOKEN_1M).
        currency (Currency): Currency. (Default: USD).
        input_cost (float): Cost per unit for input/prompt.
        output_cost (float): Cost per unit for output/completion.
        fixed_cost_per_request (float): Optional base fee. (Default: 0.0).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    unit: PricingUnit = Field(PricingUnit.TOKEN_1M, description="Unit of pricing.")
    currency: Currency = Field(Currency.USD, description="Currency.")
    input_cost: float = Field(..., description="Cost per unit for input/prompt.")
    output_cost: float = Field(..., description="Cost per unit for output/completion.")
    fixed_cost_per_request: float = Field(0.0, description="Optional base fee.")


class ResourceConstraints(ManifestBaseModel):
    """
    Technical limitations and constraints.

    Attributes:
        context_window_size (int): Total tokens supported. (Constraint: >= 0).
        max_output_tokens (int | None): Limit on generation. (Constraint: >= 0).
        rate_limit_rpm (int | None): Requests per minute. (Constraint: >= 0).
        rate_limit_tpm (int | None): Tokens per minute. (Constraint: >= 0).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    context_window_size: int = Field(..., ge=0, description="Total tokens supported.")
    max_output_tokens: int | None = Field(None, ge=0, description="Limit on generation.")
    rate_limit_rpm: int | None = Field(None, ge=0, description="Requests per minute.")
    rate_limit_tpm: int | None = Field(None, ge=0, description="Tokens per minute.")


class ModelProfile(ManifestBaseModel):
    """
    Resource profile describing hardware, pricing, and operational constraints.

    Attributes:
        provider (str): Provider name (e.g. openai).
        model_id (str): The technical ID (e.g. gpt-4).
        pricing (RateCard | None): Financials.
        constraints (ResourceConstraints | None): Technical limits.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    provider: str = Field(..., description="Provider name (e.g. openai).")
    model_id: str = Field(..., description="The technical ID (e.g. gpt-4).")
    pricing: RateCard | None = Field(None, description="Financials.")
    constraints: ResourceConstraints | None = Field(None, description="Technical limits.")


class ToolParameter(ManifestBaseModel):
    """
    Parameter definition for a tool.

    Attributes:
        name (str): Parameter name.
        type (str): Data type of the parameter.
        description (str): Parameter description.
        required (bool): Whether the parameter is required. (Default: True).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Parameter name.")
    type: str = Field(..., description="Data type of the parameter.")
    description: str = Field(..., description="Parameter description.")
    required: bool = Field(True, description="Whether the parameter is required.")


class ToolDefinition(ManifestBaseModel):
    """
    Static definition of an MCP tool capability.

    Attributes:
        name (str): The tool name (e.g., 'brave_search').
        description (str): What the tool does.
        parameters (dict[str, Any]): JSON Schema of inputs.
        is_consequential (bool): If True, coreason-mcp MUST require human approval before execution. (Default: False).
        namespace (str | None): Expected MCP server namespace (e.g., 'github').
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="The tool name (e.g., 'brave_search').")
    description: str = Field(..., description="What the tool does.")
    parameters: dict[str, Any] = Field(..., description="JSON Schema of inputs.")
    is_consequential: bool = Field(
        False, description="If True, coreason-mcp MUST require human approval before execution."
    )
    namespace: str | None = Field(None, description="Expected MCP server namespace (e.g., 'github').")


class McpServerRequirement(ManifestBaseModel):
    """
    Declares that this recipe needs a specific MCP server available.

    Attributes:
        name (str): Server name.
        required_tools (list[str]): List of required tools.
        version_constraint (str | None): Version constraint.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="Server name.")
    required_tools: list[str] = Field(default_factory=list, description="List of required tools.")
    version_constraint: str | None = Field(None, description="Version constraint.")


class RuntimeEnvironment(ManifestBaseModel):
    """
    The infrastructure requirements for the recipe.

    Attributes:
        mcp_servers (list[McpServerRequirement]): Required MCP servers.
        python_version (str | None): Required Python version. (Default: "3.12").
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    mcp_servers: list[McpServerRequirement] = Field(default_factory=list, description="Required MCP servers.")
    python_version: str | None = Field("3.12", description="Required Python version.")


class RoutingStrategy(StrEnum):
    """How the Arbitrage Engine selects a model."""

    PRIORITY = "priority"  # Use the first available model in the list
    LOWEST_COST = "lowest_cost"  # Cheapest model meeting constraints
    LOWEST_LATENCY = "lowest_latency"  # Fastest model (based on historical stats)
    PERFORMANCE = "performance"  # Strongest model (based on benchmarks)
    ROUND_ROBIN = "round_robin"  # Distribute load evenly


class ComplianceTier(StrEnum):
    """Data residency and compliance requirements."""

    STANDARD = "standard"  # No specific requirements
    EU_RESIDENCY = "eu_residency"
    HIPAA = "hipaa"
    FEDRAMP = "fedramp"


class ModelSelectionPolicy(ManifestBaseModel):
    """
    Configuration for dynamic model routing (Arbitrage).

    Attributes:
        strategy (RoutingStrategy): Selection algorithm. (Default: PRIORITY).
        min_context_window (int | None): Minimum required context size.
        max_input_cost_per_m (float | None): Max allowed input cost ($/1M tokens).
        compliance (list[ComplianceTier]): Required compliance certifications.
        provider_whitelist (list[str]): Allowed providers (e.g. ['azure', 'anthropic']).
        allow_fallback (bool): If primary selection fails, try others? (Default: True).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    strategy: RoutingStrategy = Field(RoutingStrategy.PRIORITY, description="Selection algorithm.")

    # Constraints
    min_context_window: int | None = Field(None, description="Minimum required context size.")
    max_input_cost_per_m: float | None = Field(None, description="Max allowed input cost ($/1M tokens).")
    compliance: list[ComplianceTier] = Field(default_factory=list, description="Required compliance certifications.")
    provider_whitelist: list[str] = Field(
        default_factory=list, description="Allowed providers (e.g. ['azure', 'anthropic'])."
    )

    # Fallback
    allow_fallback: bool = Field(True, description="If primary selection fails, try others?")
