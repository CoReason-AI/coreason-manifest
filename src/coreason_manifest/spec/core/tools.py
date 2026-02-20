from typing import Annotated, Literal

from pydantic import Field, HttpUrl, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import CoercibleStringList, ToolID


class Dependency(CoreasonModel):
    """Dependency definition for a tool."""

    name: str = Field(..., description="Name of the package.", examples=["requests", "pandas"])
    version: str | None = Field(None, description="Version constraint string.", examples=["^2.0.0", ">=1.0"])
    manager: Literal["pip", "npm", "apt", "mcp"] = Field(..., description="Package manager to use.", examples=["pip"])


class ToolCapability(CoreasonModel):
    """
    Definition of a tool's capabilities and risk profile.
    Mandate 3: Semantic Tool Governance.
    """

    type: Literal["capability"] = Field("capability", description="Discriminator for polymorphic tools.")
    name: ToolID = Field(..., description="Unique identifier for the tool.", examples=["calculator"])
    risk_level: Literal["safe", "standard", "critical"] = Field(
        "standard", description="Risk classification for governance.", examples=["safe"]
    )
    description: str | None = Field(
        None, description="Human-readable description of what the tool does.", examples=["Performs basic arithmetic."]
    )
    requires_approval: bool = Field(False, description="If True, human approval is required before execution.")
    # SOTA Fix: Strict URL validation
    url: HttpUrl | None = Field(
        None, description="Documentation or endpoint URL.", examples=["https://example.com/docs"]
    )

    @model_validator(mode="after")
    def validate_critical_description(self) -> "ToolCapability":
        if self.risk_level == "critical" and not self.description:
            raise ValueError(
                f"Tool '{self.name}' is Critical but lacks a description. Critical tools must be documented."
            )
        return self


# Polymorphic Tool Type (Extensible for future)
AnyTool = Annotated[ToolCapability, Field(discriminator="type")]


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
