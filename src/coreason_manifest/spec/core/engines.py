from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class BaseReasoning(BaseModel):
    """Base configuration for System 2 cognitive processes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: str = Field(..., description="The model ID responsible for this reasoning loop.")
    temperature: float = Field(0.0, description="Sampling temperature (0.0 for deterministic).")
    max_tokens: int | None = Field(None, description="Hard limit on reasoning tokens.")


class StandardReasoning(BaseReasoning):
    """Linear Chain-of-Thought (CoT) execution."""

    type: Literal["standard"] = "standard"
    thoughts_max: int = Field(..., description="Maximum number of sequential reasoning steps.")
    min_confidence: float = Field(0.7, description="Minimum confidence score to proceed.")


class TreeSearchReasoning(BaseReasoning):
    """
    Language Agent Tree Search (LATS) implementation.
    Uses Monte Carlo Tree Search (MCTS) to simulate outcomes before acting.
    """

    type: Literal["tree_search"] = "tree_search"

    depth: int = Field(3, description="Maximum depth of the search tree.")
    branching_factor: int = Field(3, description="Number of candidate actions to generate per node.")
    simulations: int = Field(5, description="Number of MCTS simulations to run.")
    exploration_weight: float = Field(1.41, description="UCT exploration term (default 1.41).")
    evaluator_model: str | None = Field(None, description="Model used to value/score leaf nodes.")


class AtomReasoning(BaseReasoning):
    """
    Atom of Thoughts (AoT) strategy.
    Decomposes problems into a DAG and iteratively 'contracts' context
    to maintain efficiency akin to a Markov process.
    """

    type: Literal["atom"] = "atom"

    decomposition_breadth: int = Field(..., description="Max parallel sub-thoughts to spawn.")
    contract_every_steps: int = Field(2, description="Frequency of condensing the active context.")
    global_context_window: int = Field(4096, description="Rolling window size for the active atom path.")


class CouncilReasoning(BaseReasoning):
    """
    Multi-Persona Consensus (SPIO) strategy.
    Orchestrates a debate or voting protocol among diverse personas.
    """

    type: Literal["council"] = "council"

    personas: list[str] = Field(..., description="List of system prompts/personas to comprise the council.")
    proposal_count: int = Field(1, description="Number of independent proposals each persona generates.")
    voting_mode: Literal["unanimous", "majority", "weighted"] = Field(
        "majority", description="Protocol for selecting the winning trajectory."
    )
    rounds: int = Field(1, description="Max debate rounds before forced voting.")


# -------------------------------------------------------------------------
# POLYMORPHIC UNION
# -------------------------------------------------------------------------
ReasoningConfig = Annotated[
    Union[StandardReasoning, TreeSearchReasoning, AtomReasoning, CouncilReasoning],
    Field(discriminator="type"),
]


class Reflex(BaseModel):
    """Configuration for System 1 (Fast) reactions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: str
    timeout_ms: int
    caching: bool = True


class Supervision(BaseModel):
    """Oversight and Fault Tolerance."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    strategy: Literal["resume", "restart", "escalate", "degrade", "adversarial"]
    max_retries: int
    fallback: str | None

    # Adversarial / Critic Configuration
    critic_model: str | None = Field(None, description="Model used for adversarial review if strategy='adversarial'.")
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
