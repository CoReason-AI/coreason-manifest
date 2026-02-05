# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Dict, Optional

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel


class AdapterHints(CoReasonBaseModel):
    """Metadata for external transpilers/adapters."""

    model_config = ConfigDict(frozen=True)

    target: str = Field(..., description="Target runtime/framework (e.g. 'langchain', 'autogen').")
    version: Optional[str] = Field(None, description="Target version compatibility.")
    config: Dict[str, str] = Field(default_factory=dict, description="Adapter-specific configuration.")


class AgentRuntimeConfig(CoReasonBaseModel):
    """Configuration for the agent runtime environment."""

    model_config = ConfigDict(frozen=True)

    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables to set.")
    adapter_hints: Optional[AdapterHints] = Field(None, description="Hints for external adapters.")
