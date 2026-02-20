from typing import Annotated, Literal

from pydantic import ConfigDict, Field, HttpUrl, model_validator

from coreason_manifest.spec.core_base import ObservableModel


class Dependency(ObservableModel):
    """Dependency definition for a tool."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: str | None = None
    manager: Literal["pip", "npm", "apt", "mcp"]


class ToolBase(ObservableModel):
    """
    Base definition of a tool's capabilities and risk profile.
    Mandate 3: Semantic Tool Governance.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    risk_level: Literal["safe", "standard", "critical"] = "standard"
    description: str | None = None
    requires_approval: bool = False

    @model_validator(mode="after")
    def validate_critical_description(self) -> "ToolBase":
        if self.risk_level == "critical" and not self.description:
            raise ValueError(
                f"Tool '{self.name}' is Critical but lacks a description. Critical tools must be documented."
            )
        return self


class ApiTool(ToolBase):
    """Tool that calls an external API."""
    type: Literal["api"] = "api"
    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"


class FunctionTool(ToolBase):
    """Tool that executes a local function."""
    type: Literal["function"] = "function"
    entrypoint: str  # e.g. "my_module.my_function"


class McpTool(ToolBase):
    """Tool exposed via Model Context Protocol."""
    type: Literal["mcp"] = "mcp"
    server_name: str

class ToolCapability(ToolBase):
    """
    Legacy/Abstract tool capability for governance checks.
    Preserved for backward compatibility in tests.
    """
    type: Literal["capability"] = "capability"
    url: HttpUrl | None = None


AnyTool = Annotated[ApiTool | FunctionTool | McpTool | ToolCapability, Field(discriminator="type")]


class ToolPack(ObservableModel):
    """A bundle of tools."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["ToolPack"]
    namespace: str
    tools: list[AnyTool]
    dependencies: list[Dependency]
    env_vars: list[str]
