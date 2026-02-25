from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import CoercibleStringList, RiskLevel


class Dependency(CoreasonModel):
    """Dependency definition for a tool."""

    name: str = Field(..., description="Name of the package.", examples=["requests", "pandas"])
    version: str | None = Field(None, description="Version constraint string.", examples=["^2.0.0", ">=1.0"])
    manager: Literal["pip", "npm", "apt", "mcp"] = Field(..., description="Package manager to use.", examples=["pip"])


class MCPTool(CoreasonModel):
    """Native Model Context Protocol (MCP) Tool definition."""

    type: Literal["mcp_tool"] = "mcp_tool"
    name: str = Field(..., description="The name of the tool.")
    description: str | None = Field(None, description="A description of the tool.")
    input_schema: dict[str, Any] = Field(..., description="JSON Schema for the tool's input arguments.")

    # Governance extensions
    risk_level: RiskLevel = Field(RiskLevel.STANDARD, description="Risk classification.")
    requires_approval: bool = Field(False, description="If True, human approval is required.")

    @model_validator(mode="after")
    def validate_critical_description(self) -> "MCPTool":
        if self.risk_level == "critical" and not self.description:
            raise ValueError(
                f"Tool '{self.name}' is Critical but lacks a description. Critical tools must be documented."
            )
        return self


class MCPResource(CoreasonModel):
    """Native Model Context Protocol (MCP) Resource definition."""

    type: Literal["mcp_resource"] = "mcp_resource"
    uri: str = Field(..., description="The URI of the resource.")
    name: str = Field(..., description="The name of the resource.")
    description: str | None = Field(None, description="A description of the resource.")
    mime_type: str | None = Field(None, description="The MIME type of the resource.")

    # Governance
    risk_level: RiskLevel = Field(RiskLevel.STANDARD, description="Risk classification.")


class MCPPromptArgument(CoreasonModel):
    name: str = Field(..., description="The name of the argument.")
    description: str | None = Field(None, description="A description of the argument.")
    required: bool = Field(False, description="Whether the argument is required.")


class MCPPrompt(CoreasonModel):
    """Native Model Context Protocol (MCP) Prompt definition."""

    type: Literal["mcp_prompt"] = "mcp_prompt"
    name: str = Field(..., description="The name of the prompt.")
    description: str | None = Field(None, description="A description of the prompt.")
    arguments: list[MCPPromptArgument] = Field(default_factory=list, description="Arguments for the prompt.")

    # Governance
    risk_level: RiskLevel = Field(RiskLevel.STANDARD, description="Risk classification.")


# Polymorphic Tool Type
AnyTool = Annotated[MCPTool | MCPResource | MCPPrompt, Field(discriminator="type")]


class MCPServerConfig(CoreasonModel):
    """Configuration for an MCP Server connection and exposed tools."""

    kind: Literal["MCPServerConfig"] = "MCPServerConfig"
    namespace: str = Field(..., description="Namespace prefix for tools from this server.", examples=["std_utils"])
    tools: list[AnyTool] = Field(
        ...,
        description="List of tools/resources/prompts provided by this server.",
        examples=[[{"name": "calc", "type": "mcp_tool", "input_schema": {}}]],
    )
    dependencies: list[Dependency] = Field(
        default_factory=list,
        description="External package dependencies required to run the server.",
        examples=[[{"name": "numpy", "manager": "pip"}]],
    )
    env_vars: CoercibleStringList = Field(
        default_factory=list, description="Required environment variables for the server.", examples=[["API_KEY"]]
    )
