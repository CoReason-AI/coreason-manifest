# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""
Native Model Context Protocol (MCP) Integration for the CoReason Manifest.

This module defines the core MCP connection primitives and pure, passive contracts.
"""

import re
from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, HttpUrl, field_validator

from coreason_manifest.core.base import CoreasonBaseModel


class MCPClientMessage(CoreasonBaseModel):
    """Strict JSON-RPC 2.0 structure for MCP client messages."""

    jsonrpc: Literal["2.0"] = Field(default="2.0", description="JSON-RPC version.")
    method: Literal["mcp.ui.emit_intent"] = Field(..., description="Method for intent bubbling.")
    params: dict[str, Any] = Field(default_factory=dict, description="Payload parameters.")
    id: str | int = Field(..., description="Unique request identifier.")


class StdioTransportConfig(CoreasonBaseModel):
    """Configuration for local Stdio-based MCP transport."""

    type: Literal["stdio"] = Field(default="stdio", description="Type of transport.")
    command: str = Field(..., description="The command executable to run (e.g., 'node', 'python').")
    args: list[str] = Field(default_factory=list, description="List of arguments to pass to the command.")
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables required by the transport."
    )


class SSETransportConfig(CoreasonBaseModel):
    """Configuration for remote SSE-based MCP transport."""

    type: Literal["sse"] = Field(default="sse", description="Type of transport.")
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the SSE connection.")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers, e.g., for authentication.")


type MCPTransport = StdioTransportConfig | SSETransportConfig


class MCPServerConfig(CoreasonBaseModel):
    """Configuration definition for connecting to an MCP Server."""

    server_id: str = Field(..., description="A unique identifier for this server instance.")
    transport: MCPTransport = Field(..., discriminator="type", description="Polymorphic transport configuration.")
    required_capabilities: list[str] = Field(
        default_factory=lambda: ["tools", "resources", "prompts"],
        description="A list of capabilities required from the MCP server.",
    )


class MCPResourceList(CoreasonBaseModel):
    """A collection of Semantic Memory resource URIs provided by a specific MCP server."""

    server_id: str = Field(..., description="The ID of the MCP server providing these resources.")
    uris: list[str] = Field(default_factory=list, description="List of resource URIs available to the agent.")


class MCPPromptRef(CoreasonBaseModel):
    """A dynamic reference to an MCP-provided prompt template."""

    server_id: str = Field(..., description="The ID of the MCP server providing this prompt.")
    prompt_name: str = Field(..., description="The name of the prompt template.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments to fill the prompt template.")
    fallback_persona: str | None = Field(default=None, description="A fallback persona if the prompt fails to load.")
    prompt_hash: str | None = Field(default=None, description="Cryptographic hash for prompt integrity verification.")


class OMOPDomain(StrEnum):
    """
    Standard OMOP domains for resource types.
    """

    CONCEPT = "CONCEPT"
    COHORT_DEFINITION = "COHORT_DEFINITION"
    CONCEPT_ANCESTOR = "CONCEPT_ANCESTOR"
    PHENOTYPE_EVALUATION = "PHENOTYPE_EVALUATION"


class OMOPResourceTemplate(CoreasonBaseModel):
    """
    Represents an MCP Resource Template exposing OMOP standard constructs to an AI agent securely.
    """

    uri_template: str = Field(
        ...,
        description="The URI template for the resource, matching an omop:// protocol pattern.",
    )
    resource_type: OMOPDomain = Field(
        ...,
        description="The standard OMOP domain for the resource.",
    )
    description: str = Field(
        ...,
        description="Documents exactly what epidemiological data this resource yields.",
    )

    @field_validator("uri_template")
    @classmethod
    def validate_uri_template(cls, v: str) -> str:
        """Ensure the URI template strictly matches the omop:// protocol pattern."""
        if not re.match(r"^omop://(?:[a-zA-Z0-9_/-]+|/\{[a-zA-Z0-9_]+\})+$", v):
            raise ValueError("uri_template must follow the 'omop://' protocol pattern")
        return v


class CohortDiagnosticsRequest(CoreasonBaseModel):
    """
    Declarative input contract for an MCP Tool wrapping OHDSI CohortDiagnostics software.
    """

    inclusion_rules: list[str | Mapping[str, Any]] = Field(
        ...,
        description="Array of heavily typed JSON-logic or criteria string representations.",
    )
    target_cohort_ids: list[int] = Field(
        ...,
        description="List of target cohort IDs.",
    )
    comparator_cohort_ids: list[int] | None = Field(
        default=None,
        description="Optional list of comparator cohort IDs.",
    )
    evaluation_windows: list[int] = Field(
        ...,
        description="List of integers representing days (e.g., [0, 30, 365]).",
    )
    diagnostic_flags: dict[str, bool] = Field(
        ...,
        description="Mapping of string flags to booleans, matching the R package's execution parameters.",
    )


class EpistemicPromptManifest(CoreasonBaseModel):
    """
    MCP Prompt specifically bounded for phenotype development and clinical reasoning.
    """

    prompt_id: str = Field(
        ...,
        description="The unique identifier for the prompt.",
    )
    version: str = Field(
        ...,
        description="The version string of the prompt.",
    )
    instruction_template: str = Field(
        ...,
        description="The core LLM directive.",
    )
    citation_requirement_schema: str | None = Field(
        default=None,
        description="If populated, this maps to the SyntaxTreeCitationAnchor defined in the uncertainty module.",
    )
    expected_output_schema: str = Field(
        ...,
        description="Reference to the Pydantic model the LLM must return.",
    )
    reproducibility_hash: str = Field(
        ...,
        description="Cryptographically locks the exact phrasing of the prompt for peer-reviewed publication tracking.",
    )
