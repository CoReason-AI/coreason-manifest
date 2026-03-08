# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the tooling schemas. This is a STRICTLY KINETIC BOUNDARY.
These schemas represent friction, hardware limits, and physical execution. This boundary governs probabilistic
tensor logic, VRAM geometries, and exogenous spatial actuation."""

from typing import Any

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class SideEffectProfile(CoreasonBaseModel):
    """
    Profile for describing the side effects and idempotency of a tool.
    """

    is_idempotent: bool = Field(
        description=(
            "True if the tool can be safely retried multiple times without altering state beyond the first call."
        )
    )
    mutates_state: bool = Field(description="True if the tool performs write operations or side-effects.")


class PermissionBoundary(CoreasonBaseModel):
    """
    Zero-trust security boundaries for tool execution.
    """

    network_access: bool = Field(description="Whether the tool is permitted to make external network requests.")
    allowed_domains: list[str] | None = Field(
        default=None, description="Whitelist of allowed network domains if network access is true."
    )
    file_system_read_only: bool = Field(description="True if the tool is strictly forbidden from writing to the disk.")
    auth_requirements: list[str] | None = Field(
        default=None,
        description="An explicit list of authentication protocol identifiers "
        "(e.g., 'oauth2:github', 'mtls:internal') the orchestrator "
        "must negotiate before allocating compute.",
    )


class ExecutionSLA(CoreasonBaseModel):
    """
    Service Level Agreement (limits) for executing a tool.
    """

    max_execution_time_ms: int = Field(
        gt=0,
        description="The Kinetic Execution Bounds time limit before the orchestrator kills the process.",
    )
    max_memory_mb: int | None = Field(
        default=None,
        gt=0,
        description="The Kinetic Execution Bounds maximum memory footprint limiting the Blast Radius "
        "of the tool's execution sandbox.",
    )


class ToolDefinition(CoreasonBaseModel):
    """
    Declarative mathematical definition of an Exogenous Actuator.
    """

    tool_name: str = Field(description="The exact identifier of the Exogenous Actuator.")
    description: str = Field(
        description="Semantic description of what the Exogenous Actuator does, used by the LLM for selection."
    )
    input_schema: dict[str, Any] = Field(
        description="The strict Schema dictionary defining the required parameters."
    )
    side_effects: SideEffectProfile = Field(
        description="The declarative side-effect and idempotency profile of the tool."
    )
    permissions: PermissionBoundary = Field(description="The zero-trust security boundaries for the tool's execution.")
    sla: ExecutionSLA | None = Field(default=None, description="Execution limits for the tool.")
    is_preemptible: bool = Field(
        default=False,
        description="If True, the orchestrator is authorized to send a SIGINT to abort this tool's execution "
        "mid-flight if a BargeInInterruptEvent occurs.",
    )
