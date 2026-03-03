from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import Field, HttpUrl, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.primitives.types import CoercibleStringList, RiskLevel, ToolID


class Dependency(CoreasonModel):
    """Dependency definition for a tool."""

    name: str = Field(..., description="Name of the package.", examples=["requests", "pandas"])
    version: str | None = Field(None, description="Version constraint string.", examples=["^2.0.0", ">=1.0"])
    manager: Literal["pip", "npm", "apt", "mcp"] = Field(..., description="Package manager to use.", examples=["pip"])
    integrity_hash: Annotated[
        str | None,
        Field(pattern=r"^sha(?:256|384|512):[a-f0-9]+$", description="Cryptographic hash of the upstream package."),
    ] = None
    sbom_ref: str | None = Field(None, description="URI or path to a CycloneDX/SPDX JSON Document.")


class LoadStrategy(StrEnum):
    EAGER = "eager"
    LAZY = "lazy"


class BaseTool(CoreasonModel):
    name: ToolID = Field(..., description="Unique identifier for the tool.", examples=["calculator"])
    risk_level: RiskLevel = Field(
        RiskLevel.STANDARD, description="Risk classification for governance.", examples=["safe"]
    )
    description: str | None = Field(
        None, description="Human-readable description of what the tool does.", examples=["Performs basic arithmetic."]
    )
    requires_approval: bool = Field(False, description="If True, human approval is required before execution.")
    # Architectural Note: Strict URL validation
    url: HttpUrl | None = Field(
        None, description="Documentation or endpoint URL.", examples=["https://example.com/docs"]
    )

    load_strategy: LoadStrategy = Field(LoadStrategy.EAGER, description="How the tool is mounted.")
    trigger_intent: str | None = Field(
        None,
        description=(
            "Dense semantic string embedded by the runtime for Tool-RAG discovery. "
            "(e.g., 'Extract patient phenotypes from unstructured clinical notes')"
        ),
    )
    lazy_routing_threshold: float = Field(
        0.75, ge=0.0, le=1.0, description="Minimum vector similarity score required to mount this tool dynamically."
    )

    @model_validator(mode="after")
    def validate_critical_description(self) -> "BaseTool":
        """Enforce that critical tools have a description."""
        if self.risk_level == "critical" and not self.description:
            raise ValueError(
                f"Tool '{self.name}' is Critical but lacks a description. Critical tools must be documented."
            )
        return self

    @model_validator(mode="after")
    def validate_lazy_loading(self) -> "BaseTool":
        """Enforce that lazy loading requires a trigger_intent."""
        if self.load_strategy == LoadStrategy.LAZY and (not self.trigger_intent or not self.trigger_intent.strip()):
            raise ValueError(
                "A valid, non-empty 'trigger_intent' is required for vector discovery when load_strategy is LAZY."
            )
        return self


class ToolCapability(BaseTool):
    """
    Definition of a tool's capabilities and risk profile.
    Mandate 3: Semantic Tool Governance.
    """

    type: Literal["capability"] = Field("capability", description="Discriminator for polymorphic tools.")


class MCPResourceTemplate(CoreasonModel):
    """Template for MCP resources."""

    uri_template: str = Field(description="The URI template for the resource.")
    name: str = Field(description="The name of the template.")
    description: str | None = Field(default=None, description="Description of the template.")
    mime_type: str | None = Field(default=None, description="The MIME type of the resource.")


class MCPPrompt(CoreasonModel):
    """Template for MCP prompts."""

    name: str = Field(description="The name of the prompt.")
    description: str | None = Field(default=None, description="Description of the prompt.")
    arguments: list[dict[str, Any]] | None = Field(default_factory=list, description="Arguments for the prompt.")


class MCPTool(BaseTool):
    """
    Definition of a remote Model Context Protocol (MCP) tool server.
    """

    type: Literal["mcp_tool"] = Field("mcp_tool", description="Discriminator for MCP tools.")
    server_uri: HttpUrl = Field(..., description="The connection URI for the MCP server.")
    mcp_version: str = Field(..., description="The MCP version supported by the server.")
    supported_capabilities: list[str] = Field(
        default_factory=list, description="List of capability flags (e.g., 'resources', 'prompts', 'logging')."
    )
    prompts: list[MCPPrompt] = Field(default_factory=list, description="List of exposed MCP prompts.")
    resource_templates: list[MCPResourceTemplate] = Field(
        default_factory=list, description="List of exposed MCP resource templates."
    )


# Polymorphic Tool Type (Extensible for future)
AnyTool = Annotated[ToolCapability | MCPTool, Field(discriminator="type")]


class ToolPack(CoreasonModel):
    """A bundle of tools."""

    kind: Literal["ToolPack"] = "ToolPack"
    namespace: str = Field(..., description="Namespace prefix for tools in this pack.", examples=["std_utils"])
    tools: list[AnyTool] = Field(
        ...,
        description="List of tool capabilities provided by this pack.",
        examples=[[{"name": "calc", "type": "capability"}]],
    )
    dependencies: list[Dependency] = Field(
        default_factory=list,
        description="External package dependencies.",
        examples=[[{"name": "numpy", "manager": "pip"}]],
    )
    env_vars: CoercibleStringList = Field(
        default_factory=list, description="Required environment variables.", examples=[["API_KEY"]]
    )
