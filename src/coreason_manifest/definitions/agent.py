# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


from typing import Literal

from pydantic import ConfigDict, Field, constr

from .base import CoReasonBaseModel


class AgentManifest(CoReasonBaseModel):
    """
    Defines the configuration for a CoReason Agent.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_version: Literal["1.0"] = "1.0"
    name: constr(pattern=r"^[a-z0-9-]+$") = Field(  # type: ignore
        ..., description="Kebab-case strict name"
    )
    version: constr(pattern=r"^\d+\.\d+\.\d+$") = Field(  # type: ignore
        ..., description="SemVer strict version"
    )
    model_config_id: str = Field(
        ...,
        alias="model_config",
        description="Must match allowlist in Manifest",
    )
    max_cost_limit: float = Field(gt=0.0, description="Maximum cost limit in dollars")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature setting (0.0 to 1.0)")
    topology: str = Field(..., min_length=1, description="Path to the topology definition file")
