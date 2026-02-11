from typing import Literal

from pydantic import BaseModel, ConfigDict


class Dependency(BaseModel):
    """Dependency definition for a tool."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: str | None = None
    manager: Literal["pip", "npm", "apt", "mcp"]


class ToolPack(BaseModel):
    """A bundle of tools."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kind: Literal["ToolPack"]
    namespace: str
    tools: list[str]
    dependencies: list[Dependency]
    env_vars: list[str]
