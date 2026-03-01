from enum import StrEnum

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel


class WorkingMemoryConfig(CoreasonModel):
    max_tokens: int = Field(..., gt=0, description="Maximum token limit for the working memory context window.")
    enable_active_paging: bool = Field(
        ...,
        description="If true, the runtime engine equips the agent with tools to load/evict context pages explicitly.",
    )


class ConsolidationStrategy(StrEnum):
    NONE = "none"
    SUMMARY_WINDOW = "summary_window"
    SEMANTIC_CLUSTER = "semantic_cluster"
    SESSION_CLOSE = "session_close"


class EpisodicMemoryConfig(CoreasonModel):
    salience_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum importance score (0.0-1.0) for a memory to be retained in long-term storage.",
    )
    consolidation_interval_turns: int | None = Field(
        None,
        gt=0,
        description=(
            "Number of conversation turns before the background loop compresses the journal. "
            "None means no auto-consolidation."
        ),
    )
    consolidation_strategy: ConsolidationStrategy = Field(
        default=ConsolidationStrategy.SESSION_CLOSE,
        description="Strategy for memory consolidation.",
    )


class SemanticMemoryConfig(CoreasonModel):
    graph_namespace: str = Field(..., description="Namespace identifier for the knowledge graph partition.")
    bitemporal_tracking: bool = Field(
        ...,
        description=(
            "If true, requires the runtime to track both 'valid_from' (business time) "
            "and 'recorded_at' (system time) metadata."
        ),
    )
    allowed_entity_types: list[str] | None = Field(
        None, description="List of allowed entity types for the graph. If None, all types are allowed."
    )


class ProceduralMemoryConfig(CoreasonModel):
    skill_library_ref: str | None = Field(
        None, description="Pointer to a global registry or library of procedural tool execution rules."
    )


class MemorySubsystem(CoreasonModel):
    working: WorkingMemoryConfig | None = Field(None, description="Configuration for Working Memory (RAM).")
    episodic: EpisodicMemoryConfig | None = Field(None, description="Configuration for Episodic Memory (Journal).")
    semantic: SemanticMemoryConfig | None = Field(
        None, description="Configuration for Semantic Memory (Knowledge Graph)."
    )
    procedural: ProceduralMemoryConfig | None = Field(None, description="Configuration for Procedural Memory (Skills).")
