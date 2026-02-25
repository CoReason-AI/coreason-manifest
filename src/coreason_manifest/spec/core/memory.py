# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel


class WorkingMemory(CoreasonModel):
    """Ephemeral, per-run state."""

    variables: dict[str, Any] = Field(
        default_factory=dict, description="Variables available in the current execution context."
    )
    max_tokens: int | None = Field(None, description="Maximum tokens allowed in working memory.")


class EpisodicMemory(CoreasonModel):
    """Configuration for cross-session database persistence."""

    retention_policy: str = Field(
        "forever", description="Policy for retaining episodic memories.", examples=["forever", "30_days"]
    )
    vector_store_ref: str | None = Field(
        None, description="Reference to a vector store for semantic search.", examples=["pinecone_store"]
    )
    collection_name: str | None = Field(
        None, description="Name of the collection in the vector store.", examples=["project_memories"]
    )


class SemanticMemory(CoreasonModel):
    """Configuration for read-only knowledge grounding."""

    knowledge_base_ref: str | None = Field(
        None, description="Reference to a knowledge base.", examples=["corporate_wiki"]
    )
    update_frequency: Literal["static", "dynamic"] = Field(
        "static", description="Frequency of updates to the semantic memory."
    )


class MemorySubsystem(CoreasonModel):
    """Hierarchical memory subsystem configuration."""

    working: WorkingMemory = Field(default_factory=WorkingMemory, description="Working memory configuration.")
    episodic: EpisodicMemory | None = Field(None, description="Episodic memory configuration.")
    semantic: SemanticMemory | None = Field(None, description="Semantic memory configuration.")
