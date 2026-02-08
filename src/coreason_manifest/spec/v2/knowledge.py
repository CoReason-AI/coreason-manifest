# src/coreason_manifest/spec/v2/knowledge.py

from enum import StrEnum
from typing import Any
from pydantic import ConfigDict, Field
from coreason_manifest.spec.common_base import CoReasonBaseModel

class RetrievalStrategy(StrEnum):
    """The algorithm used to fetch relevant context."""
    DENSE = "dense"             # Vector similarity search
    SPARSE = "sparse"           # Keyword/BM25 search
    HYBRID = "hybrid"           # Combination of Dense + Sparse with RRF
    GRAPH = "graph"             # Knowledge Graph traversal
    GRAPH_RAG = "graph_rag"     # Hybrid Vector + Graph

class KnowledgeScope(StrEnum):
    """The boundary of the memory access."""
    SHARED = "shared"           # Global organization knowledge
    USER = "user"               # User-specific private memory
    SESSION = "session"         # Ephemeral conversation context

class RetrievalConfig(CoReasonBaseModel):
    """Configuration for the RAG engine."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    strategy: RetrievalStrategy = Field(RetrievalStrategy.HYBRID, description="Search algorithm.")
    collection_name: str = Field(..., description="The ID of the vector/graph collection to query.")
    top_k: int = Field(5, ge=1, description="Number of chunks to retrieve.")
    score_threshold: float | None = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score.")
    scope: KnowledgeScope = Field(KnowledgeScope.SHARED, description="Access control scope.")
