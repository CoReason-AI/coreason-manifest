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
from typing import Literal

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel, StrictUri


class ResourceScheme(StrEnum):
    """Supported URI schemes for MCP resources."""

    FILE = "file"
    HTTP = "http"
    HTTPS = "https"
    MEM = "mem"


class MCPResourceDefinition(CoReasonBaseModel):
    """Defines a passive data source exposed by this agent via MCP."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["mcp_resource"] = "mcp_resource"
    name: str = Field(..., description="Human-readable name of the resource.")
    uri: StrictUri = Field(..., description="The strictly formatted URI of the resource.")
    mimeType: str | None = Field(None, description="MIME type of the resource content.")
    description: str | None = Field(None, description="Description of the resource content.")
    is_template: bool = Field(False, description="Whether the URI is a template.")
    size_bytes: int | None = Field(None, description="Estimated size in bytes.")
