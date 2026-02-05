# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict, List

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel


class AdapterHints(CoReasonBaseModel):
    """Configuration for external framework transpilers."""

    model_config = ConfigDict(frozen=True)

    framework: str = Field(..., description="Target framework, e.g. 'langgraph', 'autogen'")
    adapter_type: str = Field(..., description="The class/construct to generate, e.g. 'ReActNode'")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Framework-specific configuration")


class AgentRuntimeConfig(CoReasonBaseModel):
    """Runtime configuration and adapter hints for an agent."""

    model_config = ConfigDict(frozen=True)

    adapters: List[AdapterHints] = Field(
        default_factory=list, description="List of adapter configurations for different runtimes"
    )
