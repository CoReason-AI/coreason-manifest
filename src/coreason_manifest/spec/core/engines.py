from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# =========================================================================
#  1. SEMANTIC MODEL ROUTING ("The Hardware")
# =========================================================================


class ModelCriteria(BaseModel):
    """
    Defines 'What kind of model' is needed.
    Now supports Multi-Model Routing for reliability (Fallback) or scale (Round Robin).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # --- Selection Constraints ---
    strategy: Literal["lowest_cost", "lowest_latency", "performance", "balanced"] = Field(
        "balanced", description="Optimization target for model selection."
    )
    min_context: int | None = Field(None, description="Minimum required context window (tokens).")
    capabilities: list[Literal["vision", "coding", "json_mode", "function_calling"]] | None = Field(
        None, description="Hard technical requirements."
    )
    compliance: list[Literal["hipaa", "gdpr", "eu_residency", "fedramp"]] | None = Field(
        None, description="Regulatory constraints."
    )
    max_cost_per_m_tokens: float | None = Field(None, description="FinOps circuit breaker.")

    # --- Multi-Model Routing ---
    # single: Use one model (default).
    # fallback: Try list in order until one works.
    # round_robin: Rotate between matching models.
    # broadcast: Send to ALL matching models (used by EnsembleReasoning).
    routing_mode: Literal["single", "fallback", "round_robin", "broadcast"] = Field(
        "single", description="How to handle multiple matching models."
    )

    # Explicit Definition (Optional)
    provider_whitelist: list[str] | None = None
    specific_models: list[str] | None = Field(
        None, description="Explicit list of model IDs to route between (e.g. ['gpt-4', 'claude-3'])."
    )


# Type alias: A model can be a hardcoded ID ("gpt-4") OR a semantic policy
ModelRef = str | ModelCriteria


# =========================================================================
#  2. COGNITIVE ARCHITECTURES ("The Software")
# =========================================================================


class BaseReasoning(BaseModel):
    """Base configuration for System 2 cognitive processes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: ModelRef = Field(..., description="The model (or policy) responsible for this reasoning loop.")
    temperature: float = Field(0.0, description="Sampling temperature.")
    max_tokens: int | None = Field(None, description="Hard limit on output tokens.")


class StandardReasoning(BaseReasoning):
    """Linear Chain-of-Thought (CoT) / ROMA."""

    type: Literal["standard"] = "standard"
    thoughts_max: int = Field(..., description="Max sequential reasoning steps.")
    min_confidence: float = Field(0.7, description="Minimum confidence score to proceed.")


class TreeSearchReasoning(BaseReasoning):
    """Language Agent Tree Search (LATS) with MCTS."""

    type: Literal["tree_search"] = "tree_search"

    depth: int = Field(3, description="Max tree depth.")
    branching_factor: int = Field(3, description="Options per node.")
    simulations: int = Field(5, description="MCTS simulation budget.")
    exploration_weight: float = Field(1.41, description="UCT exploration term.")

    evaluator_model: ModelRef | None = Field(None, description="Model used to score leaf nodes.")


class AtomReasoning(BaseReasoning):
    """Atom of Thoughts (AoT) DAG decomposition."""

    type: Literal["atom"] = "atom"

    decomposition_breadth: int = Field(..., description="Max parallel atoms.")
    contract_every_steps: int = Field(2, description="Frequency of context condensation.")
    global_context_window: int = Field(4096, description="Rolling window size.")


class CouncilReasoning(BaseReasoning):
    """Multi-Persona Consensus (Same Model, Different Personas)."""

    type: Literal["council"] = "council"

    personas: list[str] = Field(..., description="List of system prompts.")
    proposal_count: int = Field(1, description="Proposals per persona.")
    voting_mode: Literal["unanimous", "majority", "weighted"] = "majority"
    rounds: int = Field(1, description="Max debate rounds.")
    tie_breaker_model: ModelRef | None = None


class EnsembleReasoning(BaseReasoning):
    """
    *** NEW SOTA CAPABILITY ***
    Multi-Model Consensus (Same Persona, Different Models).
    Executes the query in parallel across multiple models and unifies the result.
    NOTE: The 'model' field should use routing_mode='broadcast'.
    """

    type: Literal["ensemble"] = "ensemble"

    # Semantic Analysis: Uses a model to determine if answers are functionally equivalent
    # This replaces simple cosine similarity with deeper semantic understanding
    similarity_model: ModelRef | None = Field(
        None, description="Model used to judge if two different answers are semantically equivalent."
    )

    # Consensus Strategy
    aggregation: Literal["majority_vote", "strongest_judge", "union"] = "majority_vote"

    # Tie-Breaker: If models disagree, this judge decides.
    judge_model: ModelRef | None = Field(None, description="The 'Supreme Court' model that resolves conflicts.")


# -------------------------------------------------------------------------
# POLYMORPHIC UNION
# -------------------------------------------------------------------------
ReasoningConfig = Annotated[
    StandardReasoning | TreeSearchReasoning | AtomReasoning | CouncilReasoning | EnsembleReasoning,
    Field(discriminator="type"),
]


# =========================================================================
#  3. SYSTEM 1 & OVERSIGHT
# =========================================================================


class Reflex(BaseModel):
    """Configuration for System 1 (Fast) reactions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: ModelRef
    timeout_ms: int
    caching: bool = True


class Supervision(BaseModel):
    """Fault tolerance and adversarial oversight."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    strategy: Literal["resume", "restart", "escalate", "degrade", "adversarial"]
    max_retries: int
    fallback: str | None

    critic_model: ModelRef | None = Field(None, description="Model for adversarial review.")
    critic_prompt: str | None = None

    retry_delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    default_payload: dict[str, Any] | None = None


class Optimizer(BaseModel):
    """Self-Improvement / DSPy-style optimization."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    teacher_model: str
    metric: str
    max_demonstrations: int
