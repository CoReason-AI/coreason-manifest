from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# =========================================================================
#  1. SEMANTIC MODEL ROUTING ("The Hardware")
# =========================================================================


class ModelCriteria(BaseModel):
    """
    Defines 'What kind of model' is needed.
    Supports Multi-Model Routing for reliability (Fallback) or scale (Round Robin).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

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

    # Multi-Model Routing
    routing_mode: Literal["single", "fallback", "round_robin", "broadcast"] = Field(
        "single", description="How to handle multiple matching models."
    )

    provider_whitelist: list[str] | None = None
    specific_models: list[str] | None = Field(
        None, description="Explicit list of model IDs to route between (e.g. ['gpt-4', 'claude-3'])."
    )


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


class AttentionReasoning(BaseReasoning):
    """
    System 2 Attention (S2A).
    Filters and rewrites the input context to remove irrelevant information
    (noise/bias) BEFORE reasoning begins.
    """

    type: Literal["attention"] = "attention"

    attention_mode: Literal["rephrase", "extract"] = Field(
        "rephrase", description="Method for sanitizing input context."
    )
    # The model used to filter the noise (can be smaller/faster than the main reasoning model)
    focus_model: ModelRef | None = Field(None, description="Model used for the S2A filtering step.")


class BufferReasoning(BaseReasoning):
    """
    Buffer of Thoughts (BoT).
    Retrieves a high-level 'Thought Template' from a meta-buffer (vector store)
    to guide the reasoning process, rather than generating from scratch.
    """

    type: Literal["buffer"] = "buffer"

    max_templates: int = Field(3, description="Max number of templates to retrieve.")
    similarity_threshold: float = Field(0.75, description="Min cosine similarity for a template match.")
    template_collection: str = Field(..., description="Name of the vector collection containing thought templates.")


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
    Multi-Model Consensus with Cascading Verification.
    Executes parallel queries and uses a hybrid fast/slow path to verify agreement.
    NOTE: disagreement_threshold < 0.6 is a strong signal of emergent instability.
    """

    type: Literal["ensemble"] = "ensemble"

    # --- 1. Cascading Verification Strategy ---

    # Fast Path: How to calculate the initial cheap score.
    # 'embedding': Vector cosine similarity (Default).
    # 'lexical': Jaccard/Token overlap (Zero cost, good for strict code/math).
    # 'hybrid': Average of both.
    fast_comparison_mode: Literal["embedding", "lexical", "hybrid"] = Field(
        "embedding", description="Method for initial cheap agreement check."
    )

    # Thresholds for the Fast Path
    # Score > agreement_threshold -> Auto-Accept as Same.
    # Score < disagreement_threshold -> Auto-Reject as Different.
    # Between -> Ambiguous (Trigger Slow Path).
    agreement_threshold: float = Field(0.85, description="High confidence match threshold.")
    disagreement_threshold: float = Field(0.60, description="Low confidence mismatch threshold.")

    # Slow Path Trigger
    # 'ambiguous_only': Trigger LLM check only if score is in the grey zone (0.60-0.85).
    # 'always': Always double-check with LLM (Paranoid mode).
    # 'never': Trust the fast path implicitly (Fastest).
    verification_mode: Literal["ambiguous_only", "always", "never"] = Field(
        "ambiguous_only", description="When to trigger the deep similarity_model check."
    )

    similarity_model: ModelRef | None = Field(
        None, description="The LLM used for deep semantic verification if triggered."
    )

    # --- 2. Consensus & Tie-Breaking ---
    aggregation: Literal["majority_vote", "strongest_judge", "union"] = "majority_vote"

    # Tie-Breaker: If models disagree, this judge decides.
    judge_model: ModelRef | None = Field(None, description="The 'Supreme Court' model that resolves conflicts.")


class RedTeamingReasoning(BaseReasoning):
    """
    Agentic Red Teaming (ART).
    Proactive adversarial simulation engine.
    Uses an 'Attacker' model to run multi-turn attacks against a 'Target' model
    to discover vulnerabilities, hallucinations, or policy failures.
    """

    type: Literal["red_teaming"] = "red_teaming"

    # The adversarial agent (Red Team)
    attacker_model: ModelRef = Field(..., description="The model configured to generate attack vectors.")

    # The victim agent (Blue Team). If None, the agent attacks itself (Self-Correction).
    target_model: ModelRef | None = Field(None, description="The target model under evaluation.")

    # SOTA Attack Vectors (2025/2026)
    # crescendo: Multi-turn context escalation.
    # refusal_suppression: Rhetorical constraints to prevent standard refusals.
    # payload_splitting: Breaking malicious payloads across tokens.
    # goat: Generative Offensive Agent Tester (Tree-based planning).
    # emergence_boosting: Pressure testing to elicit latent behaviors.
    attack_strategy: Literal["crescendo", "refusal_suppression", "payload_splitting", "goat", "emergence_boosting"] = (
        Field("crescendo", description="The algorithmic protocol for generating attacks.")
    )

    max_turns: int = Field(5, description="Maximum conversation depth/trajectory.")
    success_criteria: str = Field(
        ..., description="Natural language definition of a successful break (e.g. 'PII Leakage')."
    )


class ComputerUseReasoning(BaseReasoning):
    """
    Computer Use / GUI Automation.
    Enables 'Operator Agents' that can view a screen and perform mouse/keyboard actions.
    Uses Vision-Language-Action (VLA) models to interact with GUIs.
    """

    type: Literal["computer_use"] = "computer_use"

    # Environment Configuration
    screen_resolution: tuple[int, int] | None = Field(
        None, description="Target display dimensions (width, height). If None, auto-detected."
    )

    # Interaction Protocol
    # native_os: Uses XY coordinates and OS events (clicks, hotkeys).
    # browser_dom: Uses HTML selectors and JS events (Playwright style).
    # hybrid: Allows switching between OS and DOM interaction.
    interaction_mode: Literal["native_os", "browser_dom", "hybrid"] = Field(
        "native_os", description="The layer at which the agent perceives and acts."
    )

    # Safety Governance
    allowed_actions: list[Literal["click", "type", "scroll", "screenshot", "drag", "hover", "hotkey"]] = Field(
        default=["click", "type", "scroll", "screenshot"],
        description="Allow-list of permitted GUI operations.",
    )

    screenshot_frequency_ms: int = Field(1000, description="Delay between visual observation frames (in milliseconds).")


# -------------------------------------------------------------------------
# POLYMORPHIC UNION
# -------------------------------------------------------------------------
ReasoningConfig = Annotated[
    StandardReasoning
    | AttentionReasoning
    | BufferReasoning
    | TreeSearchReasoning
    | AtomReasoning
    | CouncilReasoning
    | EnsembleReasoning
    | RedTeamingReasoning
    | ComputerUseReasoning,
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
