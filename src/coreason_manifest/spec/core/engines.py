from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
#  1. SEMANTIC MODEL ROUTING ("The Hardware")
# =========================================================================

class ModelCriteria(BaseModel):
    """
    Defines 'What kind of model' is needed, rather than 'Which specific model'.
    Allows the runtime to route dynamically based on health, cost, or policy.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    strategy: Literal["lowest_cost", "lowest_latency", "performance", "balanced"] = Field(
        "balanced", description="Optimization target for model selection."
    )
    min_context: int | None = Field(None, description="Minimum required context window (tokens).")
    capabilities: list[Literal["vision", "coding", "json_mode", "function_calling"]] | None = Field(
        None, description="Hard technical requirements for the model."
    )
    compliance: list[Literal["hipaa", "gdpr", "eu_residency", "fedramp"]] | None = Field(
        None, description="Regulatory and data residency constraints."
    )
    max_cost_per_m_tokens: float | None = Field(
        None, description="FinOps circuit breaker for input/output cost."
    )
    provider_whitelist: list[str] | None = Field(
        None, description="Restrict selection to specific providers (e.g. ['azure', 'bedrock'])."
    )


# Type alias: A model can be a hardcoded ID ("gpt-4") OR a semantic policy
ModelRef = Union[str, ModelCriteria]


# =========================================================================
#  2. COGNITIVE ARCHITECTURES ("The Software")
# =========================================================================

class BaseReasoning(BaseModel):
    """Base configuration for System 2 cognitive processes."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # UPDATED: Accepts ModelRef (str | Criteria)
    model: ModelRef = Field(..., description="The model (or policy) responsible for this reasoning loop.")

    temperature: float = Field(0.0, description="Sampling temperature.")
    max_tokens: int | None = Field(None, description="Hard limit on output tokens.")


class StandardReasoning(BaseReasoning):
    """Linear Chain-of-Thought (CoT) / ROMA."""
    type: Literal["standard"] = "standard"
    thoughts_max: int = Field(..., description="Max sequential reasoning steps.")
    min_confidence: float = Field(0.7, description="Minimum confidence score to proceed.")


class TreeSearchReasoning(BaseReasoning):
    """
    Language Agent Tree Search (LATS).
    Uses Monte Carlo Tree Search (MCTS) to simulate and score paths.
    """
    type: Literal["tree_search"] = "tree_search"

    depth: int = Field(3, description="Max tree depth.")
    branching_factor: int = Field(3, description="Options per node.")
    simulations: int = Field(5, description="MCTS simulation budget.")
    exploration_weight: float = Field(1.41, description="UCT exploration term (default 1.41).")

    # UPDATED: The evaluator can also use Semantic Routing (e.g., strategy="performance")
    evaluator_model: ModelRef | None = Field(None, description="Model used to score leaf nodes.")


class AtomReasoning(BaseReasoning):
    """
    Atom of Thoughts (AoT).
    Efficient DAG-based reasoning with context contraction.
    """
    type: Literal["atom"] = "atom"

    decomposition_breadth: int = Field(..., description="Max parallel atoms.")
    contract_every_steps: int = Field(2, description="Frequency of context condensation.")
    global_context_window: int = Field(4096, description="Rolling window size for the active atom path.")


class CouncilReasoning(BaseReasoning):
    """
    Multi-Persona Consensus (SPIO).
    Orchestrates a voting protocol among diverse personas.
    """
    type: Literal["council"] = "council"

    personas: list[str] = Field(..., description="List of system prompts.")
    proposal_count: int = Field(1, description="Proposals per persona.")
    voting_mode: Literal["unanimous", "majority", "weighted"] = "majority"
    rounds: int = Field(1, description="Max debate rounds before forced voting.")

    # UPDATED: Tie-breaker can use a specific high-intelligence model
    tie_breaker_model: ModelRef | None = None


# -------------------------------------------------------------------------
# POLYMORPHIC UNION
# -------------------------------------------------------------------------
ReasoningConfig = Annotated[
    Union[StandardReasoning, TreeSearchReasoning, AtomReasoning, CouncilReasoning],
    Field(discriminator="type"),
]


# =========================================================================
#  3. SYSTEM 1 & OVERSIGHT
# =========================================================================

class Reflex(BaseModel):
    """Configuration for System 1 (Fast) reactions."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: ModelRef  # <--- Updated to allow routing
    timeout_ms: int
    caching: bool = True


class Supervision(BaseModel):
    """Fault tolerance and adversarial oversight."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    strategy: Literal["resume", "restart", "escalate", "degrade", "adversarial"]
    max_retries: int
    fallback: str | None

    # Critic can be routed semantically
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
