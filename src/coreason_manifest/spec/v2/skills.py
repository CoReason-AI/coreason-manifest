# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.spec.common_base import CoReasonBaseModel


class LoadStrategy(StrEnum):
    """Strategy for loading the skill."""

    EAGER = "eager"
    LAZY = "lazy"
    USER = "user"


class SkillDependency(CoReasonBaseModel):
    """Dependency required by a skill."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    ecosystem: Literal["python", "node", "system", "mcp"] = Field(..., description="The ecosystem of the dependency.")
    package: str = Field(..., description="The package name or command.")
    version_constraint: str | None = Field(None, description="Optional version constraint.")


class SkillDefinition(CoReasonBaseModel):
    """Definition of an Agent Skill (Procedural Knowledge)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    type: Literal["skill"] = "skill"
    id: str = Field(..., description="Unique ID for the skill.")
    name: str = Field(..., description="Human-readable name of the skill.")
    version: str = Field("1.0.0", description="Semantic version of the skill.")

    # Discovery
    description: str = Field(..., description="Human-readable summary.")
    trigger_intent: str | None = Field(
        None, description="Dense, semantic description used for vector routing. Critical for lazy loading."
    )

    # Content
    instructions: str | None = Field(None, description="Inline system prompt/instructions.")
    instructions_uri: str | None = Field(None, description="Path to external SKILL.md file.")

    # Execution
    scripts: dict[str, str] = Field(default_factory=dict, description="Map of script names to file paths.")
    dependencies: list[SkillDependency] = Field(
        default_factory=list, description="List of dependencies required by the skill."
    )

    # Lifecycle
    load_strategy: LoadStrategy = Field(LoadStrategy.LAZY, description="Strategy for loading the skill instructions.")

    @model_validator(mode="after")
    def validate_consistency(self) -> "SkillDefinition":
        # 1. Validate Load Strategy vs Trigger Intent
        if self.load_strategy == LoadStrategy.LAZY and not self.trigger_intent:
            raise ValueError("Lazy loading requires a `trigger_intent` for discovery.")

        # 2. Validate Instructions (XOR)
        has_instructions = self.instructions is not None
        has_uri = self.instructions_uri is not None

        if has_instructions and has_uri:
            raise ValueError("Cannot specify both `instructions` and `instructions_uri`.")
        if not has_instructions and not has_uri:
            raise ValueError("Must specify either `instructions` or `instructions_uri`.")

        return self
