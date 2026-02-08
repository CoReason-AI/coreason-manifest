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


class LawCategory(StrEnum):
    """Classification of the law."""

    UNIVERSAL = "universal"  # Applies to all agents (e.g., "Do not be racist")
    DOMAIN = "domain"  # Specific to the business domain (e.g., "Do not give medical advice")
    TENANT = "tenant"  # Specific to the customer/tenant


class LawSeverity(StrEnum):
    """The impact level if this law is broken."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Law(CoReasonBaseModel):
    """A semantic rule that the agent must follow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., description="Unique identifier for the law.")
    text: str = Field(..., description="The natural language rule.")
    category: LawCategory = Field(LawCategory.DOMAIN, description="Scope of the law.")
    severity: LawSeverity = Field(LawSeverity.HIGH, description="Impact of violation.")
    reference_url: str | None = Field(None, description="Link to policy document.")


class SentinelRule(CoReasonBaseModel):
    """A hard regex pattern that triggers an immediate block."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., description="Unique identifier.")
    pattern: str = Field(..., description="Regex pattern to match.")
    description: str = Field(..., description="Why this pattern is blocked.")


class Constitution(CoReasonBaseModel):
    """Structured Governance configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    laws: list[Law] = Field(default_factory=list, description="Semantic laws for the LLM Judge.")
    sentinel_rules: list[SentinelRule] = Field(default_factory=list, description="Hard regex rules for the Sentinel.")
