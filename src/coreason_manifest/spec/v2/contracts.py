# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class InterfaceDefinition(CoReasonBaseModel):
    """
    Defines the input/output contract.

    Attributes:
        inputs (dict[str, Any]): JSON Schema definitions for arguments.
        outputs (dict[str, Any]): JSON Schema definitions for return values.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    inputs: dict[str, Any] = Field(default_factory=dict, description="JSON Schema definitions for arguments.")
    outputs: dict[str, Any] = Field(default_factory=dict, description="JSON Schema definitions for return values.")


class StateDefinition(CoReasonBaseModel):
    """
    Defines the conversation memory/context structure.

    Attributes:
        memory_schema (dict[str, Any]): The structure of the conversation memory/context.
        backend (str | None): Backend storage type (e.g., 'redis', 'memory').
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    memory_schema: dict[str, Any] = Field(
        default_factory=dict, description="The structure of the conversation memory/context."
    )
    backend: str | None = Field(None, description="Backend storage type (e.g., 'redis', 'memory').")


class PolicyDefinition(CoReasonBaseModel):
    """
    Defines execution policy and governance rules.

    Attributes:
        max_steps (int | None): Execution limit on number of steps.
        max_retries (int): Maximum number of retries. (Default: 3).
        timeout (int | None): Timeout in seconds.
        human_in_the_loop (bool): Whether to require human approval. (Default: False).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    max_steps: int | None = Field(None, description="Execution limit on number of steps.")
    max_retries: int = Field(3, description="Maximum number of retries.")
    timeout: int | None = Field(None, description="Timeout in seconds.")
    human_in_the_loop: bool = Field(False, description="Whether to require human approval.")
