# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import Enum
from typing import Dict, List, Optional

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.base import CoReasonBaseModel, StrictUri


class ResourceRiskLevel(str, Enum):
    """Risk level for the resource."""

    SAFE = "SAFE"
    STANDARD = "STANDARD"
    CRITICAL = "CRITICAL"


class SidecarResource(CoReasonBaseModel):
    """Represents a container that runs alongside the agent.

    Attributes:
        name: Name of the sidecar.
        image: Docker image (e.g., 'redis:alpine').
        env_vars: Environment variables for the sidecar.
        ports: Ports to expose.
        command: Command to run.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Name of the sidecar.")
    image: str = Field(..., description="Docker image (e.g., 'redis:alpine').")
    env_vars: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables for the sidecar."
    )
    ports: Optional[List[int]] = Field(default=None, description="Ports to expose.")
    command: Optional[List[str]] = Field(default=None, description="Command to run.")


class RemoteServiceResource(CoReasonBaseModel):
    """Represents an external API or MCP server.

    Attributes:
        name: Name of the remote service.
        uri: The service URI.
        scopes: List of required scopes/permissions.
        connection_secret_env: Name of the env var holding the API key.
        risk_level: Risk level of the resource.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Name of the remote service.")
    uri: StrictUri = Field(..., description="The service URI.")
    scopes: Optional[List[str]] = Field(
        default=None, description="List of required scopes/permissions."
    )
    connection_secret_env: Optional[str] = Field(
        default=None, description="Name of the env var holding the API key."
    )
    risk_level: ResourceRiskLevel = Field(..., description="Risk level of the resource.")
