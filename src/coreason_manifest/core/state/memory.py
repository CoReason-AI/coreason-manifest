from enum import StrEnum

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel


class WorkingMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's short-term working memory (RAM).
    """

    max_tokens: int = Field(
        ..., gt=0, description="Maximum token limit for the working memory context window.", examples=[4096]
    )
    enable_active_paging: bool = Field(
        ...,
        description=("If true, the runtime engine equips the agent with tools to load/evict context pages explicitly."),
        examples=[True],
    )


class ConsolidationStrategy(StrEnum):
    NONE = "none"
    SUMMARY_WINDOW = "summary_window"
    SEMANTIC_CLUSTER = "semantic_cluster"
    SESSION_CLOSE = "session_close"


class RetrievalStrategy(StrEnum):
    DENSE = "dense"
    HYBRID = "hybrid"
    GRAPH = "graph"
    GRAPH_RAG = "graph_rag"


class KnowledgeScope(StrEnum):
    SHARED = "shared"
    USER = "user"
    SESSION = "session"


class EpisodicMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's long-term episodic memory (Journal).
    """

    salience_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum importance score (0.0-1.0) for a memory to be retained in long-term storage.",
        examples=[0.75],
    )
    consolidation_interval_turns: int | None = Field(
        None,
        gt=0,
        description=(
            "Number of conversation turns before the background loop compresses the journal. "
            "None means no auto-consolidation."
        ),
        examples=[10],
    )
    consolidation_strategy: ConsolidationStrategy = Field(
        default=ConsolidationStrategy.SESSION_CLOSE,
        description="The strategy to use for memory consolidation.",
        examples=[ConsolidationStrategy.SESSION_CLOSE],
    )


class SemanticMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's semantic knowledge graph (Knowledge Graph).
    """

    graph_namespace: str = Field(
        ..., description="Namespace identifier for the knowledge graph partition.", examples=["global_knowledge_base"]
    )
    bitemporal_tracking: bool = Field(
        ...,
        description=(
            "If true, requires the runtime to track both 'valid_from' (business time) "
            "and 'recorded_at' (system time) metadata."
        ),
        examples=[True],
    )
    allowed_entity_types: list[str] | None = Field(
        None,
        description="List of allowed entity types for the graph. If None, all types are allowed.",
        examples=[["Person", "Organization"]],
    )
    retrieval_strategy: RetrievalStrategy = Field(
        RetrievalStrategy.HYBRID,
        description=(
            "The algorithmic approach required by this agent. "
            "(e.g., GRAPH_RAG for multi-hop clinical ontology traversal)"
        ),
        examples=[RetrievalStrategy.GRAPH_RAG],
    )
    scope: KnowledgeScope = Field(
        ...,
        description=(
            "The epistemic boundary of the knowledge access. "
            "Must be explicitly declared to prevent cross-tenant data leaks."
        ),
        examples=[KnowledgeScope.USER],
    )
    min_score_threshold: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for the runtime to inject the context.",
        examples=[0.85],
    )


class ProceduralMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's procedural memory (Skills).
    """

    skill_library_ref: str | None = Field(
        None,
        description="Pointer to a global registry or library of procedural tool execution rules.",
        examples=["company_skill_library_v1"],
    )


class MemorySubsystem(CoreasonModel):
    """
    The master blueprint for the agent's 4-tier hierarchical memory system.
    """

    working: WorkingMemoryConfig | None = Field(
        None,
        description="Configuration for Working Memory (RAM).",
        examples=[{"max_tokens": 4096, "enable_active_paging": True}],
    )
    episodic: EpisodicMemoryConfig | None = Field(
        None,
        description="Configuration for Episodic Memory (Journal).",
        examples=[
            {"salience_threshold": 0.5, "consolidation_interval_turns": 5, "consolidation_strategy": "session_close"}
        ],
    )
    semantic: SemanticMemoryConfig | None = Field(
        None,
        description="Configuration for Semantic Memory (Knowledge Graph).",
        examples=[
            {
                "graph_namespace": "tenant_123",
                "bitemporal_tracking": False,
                "allowed_entity_types": None,
                "retrieval_strategy": "hybrid",
                "scope": "session",
                "min_score_threshold": 0.8,
            }
        ],
    )
    procedural: ProceduralMemoryConfig | None = Field(
        None,
        description="Configuration for Procedural Memory (Skills).",
        examples=[{"skill_library_ref": "global_skills"}],
    )
