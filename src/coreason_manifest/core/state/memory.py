from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class ScreeningPhase(StrEnum):
    DEDUPLICATION = "deduplication"
    TITLE_ABSTRACT_SCREEN = "title_abstract_screen"
    FULL_TEXT_RETRIEVAL = "full_text_retrieval"
    FULL_TEXT_SCREEN = "full_text_screen"


class ExclusionReason(StrEnum):
    WRONG_POPULATION = "wrong_population"
    WRONG_INTERVENTION = "wrong_intervention"
    WRONG_COMPARATOR = "wrong_comparator"
    WRONG_OUTCOME = "wrong_outcome"
    WRONG_STUDY_DESIGN = "wrong_study_design"
    ANIMAL_IN_VITRO = "animal_in_vitro"
    LANGUAGE = "language"
    DUPLICATE = "duplicate"
    FULL_TEXT_UNAVAILABLE = "full_text_unavailable"


class AttritionEvent(CoreasonModel):
    """An immutable record of a document's transition through the screening pipeline."""

    document_id: Annotated[str, Field(description="The unique identifier of the paper (e.g., PMID or DOI).")]
    phase: Annotated[ScreeningPhase, Field(description="The screening phase where this event occurred.")]
    status: Annotated[Literal["included", "excluded"], Field(description="The outcome of the screening phase.")]
    reason: Annotated[
        ExclusionReason | None, Field(description="Strict ontology-mapped reason. Mandatory if status is 'excluded'.")
    ] = None
    agent_id: Annotated[str, Field(description="The ID of the Agent or Swarm that made the decision.")]

    @model_validator(mode="after")
    def validate_exclusion_reason(self) -> "AttritionEvent":
        """Mathematically enforce that an exclusion event MUST provide a clinical reason."""
        if self.status == "excluded" and self.reason is None:
            raise ValueError("An exclusion event MUST provide a strictly typed ExclusionReason.")
        return self


class PRISMAAttritionLedger(CoreasonModel):
    """Cryptographic state machine for generating PRISMA 2020 flow diagrams."""

    events: Annotated[
        list[AttritionEvent],
        Field(default_factory=list, description="Append-only log of all document filtering events."),
    ]


class WorkingMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's short-term working memory (RAM).
    """

    max_tokens: int = Field(..., gt=0, description="Maximum token limit for the working memory context window.")
    enable_active_paging: bool = Field(
        ...,
        description=("If true, the runtime engine equips the agent with tools to load/evict context pages explicitly."),
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
    EPISTEMIC = "epistemic"


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
    )
    consolidation_interval_turns: int | None = Field(
        None,
        gt=0,
        description=(
            "Number of conversation turns before the background loop compresses the journal. "
            "None means no auto-consolidation."
        ),
    )
    consolidation_strategy: ConsolidationStrategy = Field(default=ConsolidationStrategy.SESSION_CLOSE)


class ProvenanceLevel(StrEnum):
    DOCUMENT_HASH = "document_hash"
    TEXT_SNIPPET = "text_snippet"
    VISUAL_BOUNDING_BOX = "visual_bounding_box"


class ProvenanceConfig(CoreasonModel):
    """
    Configuration for cryptographic and visual traceability of extracted data.
    Ensures 100% 'Glass Box' auditability for regulatory submissions.
    """

    required_level: ProvenanceLevel = Field(
        default=ProvenanceLevel.VISUAL_BOUNDING_BOX,
        description=(
            "The minimum level of provenance required. "
            "'visual_bounding_box' forces precise PDF pixel coordinate tracking."
        ),
    )
    enforce_cryptographic_trace: bool = Field(
        default=True,
        description=(
            "If true, requires an immutable hash chain linking extracted data "
            "to its original source binary (e.g., 21 CFR Part 11 compliance)."
        ),
    )


class SemanticMemoryConfig(CoreasonModel):
    """
    Configuration for the agent's semantic knowledge graph (Knowledge Graph).
    """

    graph_namespace: str = Field(..., description="Namespace identifier for the knowledge graph partition.")
    epistemic_tracking: bool = Field(
        False,
        description=(
            "If true, requires the runtime to track Bayesian confidence scores "
            "and falsification counts for every node in the graph, enabling scientific peer-validation."
        ),
    )
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
    retrieval_strategy: RetrievalStrategy = Field(
        RetrievalStrategy.HYBRID,
        description=(
            "The algorithmic approach required by this agent. "
            "(e.g., GRAPH_RAG for multi-hop clinical ontology traversal)"
        ),
    )
    scope: KnowledgeScope = Field(
        ...,
        description=(
            "The epistemic boundary of the knowledge access. "
            "Must be explicitly declared to prevent cross-tenant data leaks."
        ),
    )
    min_score_threshold: float = Field(
        0.75, ge=0.0, le=1.0, description="Minimum confidence score for the runtime to inject the context."
    )
    provenance: ProvenanceConfig | None = Field(
        None,
        description=(
            "Strict provenance requirements for ensuring extracted evidence is mathematically and visually grounded."
        ),
    )

    @model_validator(mode="after")
    def validate_epistemic_strategy(self) -> "SemanticMemoryConfig":
        """Enforce that epistemic retrieval strategy requires epistemic tracking."""
        if self.retrieval_strategy == RetrievalStrategy.EPISTEMIC and not self.epistemic_tracking:
            raise ValueError("If retrieval_strategy is set to EPISTEMIC, epistemic_tracking must be True.")
        return self


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
    procedural: ProceduralMemoryConfig | None = Field(None, description="Configuration for Procedural Memory (Skills).")
    prisma_ledger: PRISMAAttritionLedger | None = Field(
        None, description="Append-only ledger for tracking PRISMA document attrition and generating flow diagrams."
    )
