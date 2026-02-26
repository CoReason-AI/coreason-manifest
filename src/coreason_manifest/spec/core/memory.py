# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel

# =========================================================================
#  MEMORY SUBSYSTEM CONFIGURATION
# =========================================================================

MemoryRetentionPolicy = Literal["forever", "session_only", "lru", "ttl"]
MemoryTier = Literal["working", "episodic", "semantic", "procedural"]


class MemoryConfig(CoreasonModel):
    """Configuration for a specific memory tier."""

    enabled: bool = Field(True, description="Whether this memory tier is active.")
    retention: MemoryRetentionPolicy = Field("forever", description="How long to keep memories in this tier.")
    max_items: Annotated[int | None, Field(description="Maximum number of items to store.")] = None
    ttl_seconds: Annotated[int | None, Field(description="Time-to-live in seconds for TTL retention policy.")] = None


class WorkingMemory(MemoryConfig):
    """
    Short-term context window management.
    Handles immediate task context and scratchpad.
    """

    context_window_size: int = Field(4096, description="Maximum tokens allocated for working memory.")


class EpisodicMemory(MemoryConfig):
    """
    Long-term storage of past experiences and execution traces.
    Used for retrieving successful plans and avoiding past failures.
    """

    collection_name: str = Field(..., description="Vector database collection name for episodes.")
    similarity_threshold: float = Field(0.75, description="Minimum similarity score for retrieval.")


class SemanticMemory(MemoryConfig):
    """
    Knowledge base and fact storage.
    Used for RAG (Retrieval Augmented Generation) over domain knowledge.
    """

    knowledge_base_id: str = Field(..., description="Identifier for the knowledge base or graph.")
    retrieval_k: int = Field(5, description="Number of documents to retrieve.")


class ProceduralMemory(MemoryConfig):
    """
    Skill library and tool usage patterns.
    Stores 'how-to' knowledge for executing specific actions.
    """

    skill_library_id: str = Field(..., description="Identifier for the skill library.")


class MemorySubsystem(CoreasonModel):
    """
    The 4-tier OS-style memory architecture.
    Integrates all memory types into a cohesive system for the agent.
    """

    working: WorkingMemory | None = Field(None, description="Short-term working memory configuration.")
    episodic: EpisodicMemory | None = Field(None, description="Long-term episodic memory configuration.")
    semantic: SemanticMemory | None = Field(None, description="Domain knowledge semantic memory configuration.")
    procedural: ProceduralMemory | None = Field(None, description="Skill-based procedural memory configuration.")

    shared_namespace: str | None = Field(None, description="Namespace for sharing memory across agents/sessions.")
