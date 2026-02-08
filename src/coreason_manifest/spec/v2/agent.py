# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import IntEnum
from typing import Any

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel
from coreason_manifest.spec.v2.knowledge import MemoryWriteConfig, RetrievalConfig
from coreason_manifest.spec.v2.reasoning import ReasoningConfig, ReflexConfig


class ComponentPriority(IntEnum):
    """Priority levels for token optimization (harvested from Weaver)."""

    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


class ContextDependency(CoReasonBaseModel):
    """A reference to a context module (e.g. 'hipaa_context')."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(..., description="The registry name of the context component.")
    priority: ComponentPriority = Field(ComponentPriority.MEDIUM, description="Token optimization priority.")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Variables to inject into the context.")


class CognitiveProfile(CoReasonBaseModel):
    """The configuration for the Weaver to assemble a Prompt."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    # 1. Identity (Who)
    role: str = Field(..., description="The specific Role/Persona (e.g., 'safety_scientist').")

    # 2. Mode (How)
    reasoning_mode: str | None = Field("standard", description="The thinking style (e.g., 'six_hats', 'socratic').")

    # --- Reasoning Capabilities ---
    reasoning: ReasoningConfig | None = Field(
        None,
        description="System 2: Deep reasoning configuration (Episteme)."
    )
    reflex: ReflexConfig | None = Field(
        None,
        description="System 1: Fast response configuration (Cortex)."
    )

    # 3. Environment (Where)
    knowledge_contexts: list[ContextDependency] = Field(
        default_factory=list, description="Dynamic context modules to inject."
    )

    # --- Memory Capabilities ---
    memory_read: list[RetrievalConfig] = Field(
        default_factory=list,
        alias="memory",
        description="Sources to read from (RAG)."
    )
    memory_write: MemoryWriteConfig | None = Field(
        None,
        description="Rules for saving new memories (Crystallization)."
    )

    # 4. Task (What) - Maps to StructuredPrimitive
    task_primitive: str | None = Field(
        None, description="The logic primitive to apply (e.g., 'extract', 'classify', 'cohort')."
    )

    @property
    def memory(self) -> list[RetrievalConfig]:
        """Alias for memory_read to maintain backward compatibility."""
        return self.memory_read
