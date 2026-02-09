# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import TYPE_CHECKING, Literal, Union

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import ManifestBaseModel, StrictUri
from coreason_manifest.spec.v2.skills import SkillDefinition

if TYPE_CHECKING:
    from coreason_manifest.spec.v2.definitions import AgentDefinition, ToolDefinition


class PackAuthor(ManifestBaseModel):
    """Author information for a pack."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str | None = Field(None, description="Author name.")
    email: str | None = Field(None, description="Author email.")
    url: StrictUri | None = Field(None, description="Author website.")


class PackMetadata(ManifestBaseModel):
    """Metadata for a Tool Pack."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Name of the pack (kebab-case).")
    version: str = Field("0.1.0", description="Semantic version.")
    description: str = Field(..., description="Short description.")
    author: str | PackAuthor = Field(..., description="Author name or contact info.")
    homepage: StrictUri | None = Field(None, description="Homepage URL.")


class MCPServerDefinition(ManifestBaseModel):
    """Definition of an MCP Server process."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["mcp_server"] = "mcp_server"
    name: str = Field(..., description="Name of the server.")
    command: str = Field(..., description="Command to execute.")
    args: list[str] = Field(default_factory=list, description="Arguments for the command.")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables.")


class MCPResourceDefinition(ManifestBaseModel):
    """Definition of an MCP Resource (passive data stream)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["resource"] = "resource"
    uri: StrictUri = Field(..., description="URI of the resource.")
    name: str = Field(..., description="Name of the resource.")
    mime_type: str | None = Field(None, description="MIME type.")
    description: str | None = Field(None, description="Description.")


class ToolPackDefinition(ManifestBaseModel):
    """A distributable bundle of capabilities (Tools, Skills, Agents)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["tool_pack"] = "tool_pack"
    id: str = Field(..., description="Unique ID for the pack.")
    namespace: str | None = Field(None, description="Namespace prefix for components.")
    metadata: PackMetadata = Field(..., description="Metadata.")

    agents: list[Union["AgentDefinition", str]] = Field(default_factory=list, description="List of Agents or IDs.")
    skills: list[SkillDefinition | str] = Field(default_factory=list, description="List of Skills or IDs.")
    tools: list[Union["ToolDefinition", str]] = Field(default_factory=list, description="List of Tools or IDs.")
    mcp_servers: list[MCPServerDefinition] = Field(default_factory=list, description="List of MCP Servers.")
