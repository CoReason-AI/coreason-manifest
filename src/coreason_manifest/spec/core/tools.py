from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator


class Dependency(BaseModel):
    """Dependency definition for a tool."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: str | None = None
    manager: Literal["pip", "npm", "apt", "mcp"]


class ToolCapability(BaseModel):
    """
    Definition of a tool's capabilities and risk profile.
    Mandate 3: Semantic Tool Governance.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    risk_level: Literal["safe", "standard", "critical"] = "standard"
    description: str | None = None
    requires_approval: bool = False
    # SOTA Fix: Strict URL validation
    url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_critical_description(self) -> "ToolCapability":
        if self.risk_level == "critical" and not self.description:
            raise ValueError(
                f"Tool '{self.name}' is Critical but lacks a description. Critical tools must be documented."
            )
        return self


class ToolPack(BaseModel):
    """A bundle of tools."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["ToolPack"]
    namespace: str
    tools: list[ToolCapability]
    dependencies: list[Dependency]
    env_vars: list[str]
