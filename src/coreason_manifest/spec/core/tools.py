from typing import Literal

from pydantic import BaseModel, ConfigDict


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
    # From prompt description: "If risk_level == critical, strictly enforce..."
    # Code snippet in prompt showed `requires_approval` too.
    requires_approval: bool = False


class ToolPack(BaseModel):
    """A bundle of tools."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["ToolPack"]
    namespace: str
    tools: list[ToolCapability]  # Replaces list[str]
    dependencies: list[Dependency]
    env_vars: list[str]
