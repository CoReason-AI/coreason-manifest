from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel


class WorkingMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's short-term working memory (RAM).
    """

    max_tokens: int = Field(
        ..., gt=0, description="Maximum token limit for the working memory context window."
    )
    enable_active_paging: bool = Field(
        ...,
        description=(
            "If true, the runtime engine equips the agent with tools to load/evict "
            "context pages explicitly."
        ),
    )


class EpisodicMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's long-term episodic memory (Journal).
    """

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


class SemanticMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's semantic knowledge graph (Knowledge Graph).
    """

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
    """
    Configuration for the agent's procedural memory (Skills).
    """

    skill_library_ref: str | None = Field(
        None, description="Pointer to a global registry or library of procedural tool execution rules."
    )


class MemorySubsystem(CoreasonModel):
    """
    The master blueprint for the agent's 4-tier hierarchical memory system.
    """

    working: WorkingMemoryConfig | None = Field(None, description="Configuration for Working Memory (RAM).")
    episodic: EpisodicMemoryConfig | None = Field(None, description="Configuration for Episodic Memory (Journal).")
    semantic: SemanticMemoryConfig | None = Field(
        None, description="Configuration for Semantic Memory (Knowledge Graph)."
    )
    procedural: ProceduralMemoryConfig | None = Field(
        None, description="Configuration for Procedural Memory (Skills)."
    )
