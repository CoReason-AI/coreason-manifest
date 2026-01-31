# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from enum import Enum

from pydantic import Field

from .base import CoReasonBaseModel


class DataSensitivity(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PII = "PII"
    GXP_LOCKED = "GXP_LOCKED"


class SourceManifest(CoReasonBaseModel):
    """Defines a data source for the Catalog."""

    urn: str = Field(..., pattern=r"^urn:coreason:mcp:[a-z0-9_]+$")
    name: str
    description: str
    endpoint_url: str
    geo_location: str
    sensitivity: DataSensitivity
    access_policy: str  # Rego code string for OPA
