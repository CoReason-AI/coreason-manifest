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
from typing import Dict

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.base import CoReasonBaseModel


class Protocol(str, Enum):
    """The communication protocol used to serve the agent."""

    HTTP_SSE = "http_sse"
    WEBSOCKET = "websocket"
    GRPC = "grpc"


class DeploymentConfig(CoReasonBaseModel):
    """Configuration for hosting the agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol: Protocol = Field(
        default=Protocol.HTTP_SSE, description="The communication protocol used to serve the agent."
    )
    port: int = Field(default=8000, description="The port to bind to.")
    route_prefix: str = Field(default="/assist", description="URL prefix for the agent endpoints.")
    scaling_min_instances: int = Field(default=0, description="Minimum number of replicas.")
    scaling_max_instances: int = Field(default=1, description="Maximum number of replicas.")
    timeout_seconds: int = Field(default=60, description="Request timeout.")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Static environment variables.")
