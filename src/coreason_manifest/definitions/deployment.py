# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import List, Literal, Optional

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel


class SecretReference(CoReasonBaseModel):
    """Reference to a required secret/environment variable.

    Attributes:
        key: The environment variable name.
        description: Human-readable explanation of why this secret is needed.
        required: Whether the secret is mandatory.
        provider_hint: Optional hint for the secret provider.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(..., description="The environment variable name, e.g., 'OPENAI_API_KEY'.")
    description: str = Field(..., description="Human-readable explanation of why this secret is needed.")
    required: bool = Field(default=True, description="Whether the secret is mandatory.")
    provider_hint: Optional[str] = Field(
        None, description="Optional hint for the secret provider, e.g., 'aws-secrets-manager'."
    )


class ResourceLimits(CoReasonBaseModel):
    """Hardware constraints for the deployment.

    Attributes:
        cpu_cores: CPU cores limit.
        memory_mb: RAM limit in Megabytes.
        timeout_seconds: Execution time limit.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    cpu_cores: Optional[float] = Field(None, description="CPU cores limit, e.g., 0.5 or 2.0.")
    memory_mb: Optional[int] = Field(None, description="RAM in Megabytes.")
    timeout_seconds: Optional[int] = Field(60, description="Execution time limit. Default 60.")


class DeploymentConfig(CoReasonBaseModel):
    """Runtime deployment settings.

    Attributes:
        env_vars: List of required secrets/vars.
        resources: Hardware constraints.
        scaling_strategy: Strategy for scaling (serverless or dedicated).
        concurrency_limit: Max simultaneous requests.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    env_vars: List[SecretReference] = Field(..., description="List of required secrets/vars.")
    resources: Optional[ResourceLimits] = Field(None, description="Hardware constraints.")
    scaling_strategy: Literal["serverless", "dedicated"] = Field(
        default="serverless", description="Strategy for scaling."
    )
    concurrency_limit: Optional[int] = Field(None, description="Max simultaneous requests.")
