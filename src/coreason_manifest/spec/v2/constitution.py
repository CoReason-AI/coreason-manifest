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

    UNIVERSAL = "Universal"  # e.g. "No hate speech"
    DOMAIN = "Domain"  # e.g. "GxP Compliance"
    TENANT = "Tenant"  # e.g. "Acme Corp Policy"


class LawSeverity(StrEnum):
    """Impact of violating the law."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Law(CoReasonBaseModel):
    """A specific rule or principle the AI must follow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier (e.g., 'GCP.4').")
    category: LawCategory = Field(LawCategory.DOMAIN, description="Category of the law.")
    text: str = Field(..., min_length=1, description="The content of the law/principle.")
    severity: LawSeverity = Field(LawSeverity.MEDIUM, description="Consequence of violation.")
    reference_url: str | None = Field(None, description="Source of truth (e.g. FDA citation).")


class SentinelRule(CoReasonBaseModel):
    """A hard Regex pattern for immediate blocking (Red Line)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., description="Rule ID.")
    pattern: str = Field(..., description="Regex pattern to match.")
    description: str = Field(..., description="Why this pattern is blocked.")


class Constitution(CoReasonBaseModel):
    """A collection of laws that govern an agent's behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    laws: list[Law] = Field(default_factory=list, description="Principles for semantic critique.")
    sentinel_rules: list[SentinelRule] = Field(default_factory=list, description="Patterns for hard filtering.")
