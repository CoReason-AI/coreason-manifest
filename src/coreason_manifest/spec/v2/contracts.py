# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict, Optional

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class InterfaceDefinition(CoReasonBaseModel):
    """Defines the input/output contract."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    inputs: dict[str, Any] = Field(default_factory=dict, description="JSON Schema definitions for arguments.")
    outputs: dict[str, Any] = Field(default_factory=dict, description="JSON Schema definitions for return values.")


class StateDefinition(CoReasonBaseModel):
    """Defines the conversation memory/context structure."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: dict[str, Any] = Field(
        default_factory=dict, alias="schema", description="The structure of the conversation memory/context."
    )
    backend: str | None = Field(None, description="Backend storage type (e.g., 'redis', 'memory').")


class PolicyDefinition(CoReasonBaseModel):
    """Defines execution policy and governance rules."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    max_steps: int | None = Field(None, description="Execution limit on number of steps.")
    max_retries: int = Field(3, description="Maximum number of retries.")
    timeout: int | None = Field(None, description="Timeout in seconds.")
    human_in_the_loop: bool = Field(False, description="Whether to require human approval.")
