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

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class RetrievalStrategy(StrEnum):
    """The algorithm used to fetch relevant context."""

    DENSE = "dense"  # Vector similarity search
    SPARSE = "sparse"  # Keyword/BM25 search
    HYBRID = "hybrid"  # Combination of Dense + Sparse with RRF
    GRAPH = "graph"  # Knowledge Graph traversal
    GRAPH_RAG = "graph_rag"  # Hybrid Vector + Graph


class KnowledgeScope(StrEnum):
    """The boundary of the memory access."""

    SHARED = "shared"  # Global organization knowledge
    USER = "user"  # User-specific private memory
    SESSION = "session"  # Ephemeral conversation context


class RetrievalConfig(CoReasonBaseModel):
    """Configuration for the RAG engine."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    strategy: RetrievalStrategy = Field(RetrievalStrategy.HYBRID, description="Search algorithm.")
    collection_name: str = Field(..., description="The ID of the vector/graph collection to query.")
    top_k: int = Field(5, ge=1, description="Number of chunks to retrieve.")
    score_threshold: float | None = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score.")
    scope: KnowledgeScope = Field(KnowledgeScope.SHARED, description="Access control scope.")


class ConsolidationStrategy(StrEnum):
    """How short-term context is moved to long-term memory (Harvested from Cortex)."""

    NONE = "none"  # Forget everything after session
    SUMMARY_WINDOW = "summary_window"  # Summarize every N turns
    SEMANTIC_CLUSTER = "semantic_cluster"  # Group related turns by topic
    SESSION_CLOSE = "session_close"  # Crystallize only when session ends


class MemoryWriteConfig(CoReasonBaseModel):
    """Configuration for the Cortex Crystallizer (Memory Writer)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: ConsolidationStrategy = Field(
        ConsolidationStrategy.SESSION_CLOSE, description="When to persist memories."
    )
    frequency_turns: int = Field(
        10, description="If strategy is SUMMARY_WINDOW, how many turns trigger a write."
    )
    destination_collection: str | None = Field(
        None,
        description="Target vector store collection. If None, uses the primary retrieval collection.",
    )
