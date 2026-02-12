from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.spec.core.governance import ConstitutionalScope

# =========================================================================
#  TYPE DEFINITIONS & ALIASES
# =========================================================================

RoutingStrategy = Literal["lowest_cost", "lowest_latency", "performance", "balanced"]
RoutingMode = Literal["single", "fallback", "round_robin", "broadcast"]
ModelCapability = Literal["vision", "coding", "json_mode", "function_calling"]
ComplianceStandard = Literal["hipaa", "gdpr", "eu_residency", "fedramp"]

AttentionMode = Literal["rephrase", "extract"]
BoTLearningStrategy = Literal["read_only", "append_new", "refine_existing"]
FastComparisonMode = Literal["embedding", "lexical", "hybrid"]
VerificationMode = Literal["ambiguous_only", "always", "never"]
AggregationStrategy = Literal["majority_vote", "strongest_judge", "union"]
AttackStrategy = Literal["crescendo", "refusal_suppression", "payload_splitting", "goat", "emergence_boosting"]
InteractionMode = Literal["native_os", "browser_dom", "hybrid"]
AllowedAction = Literal["click", "type", "scroll", "screenshot", "drag", "hover", "hotkey"]
CoordinateSystem = Literal["absolute_px", "normalized_0_1"]
GraphRetrievalMode = Literal["local", "global", "hybrid"]
GuidedDecodingMode = Literal["json_schema", "regex", "grammar", "none"]


# =========================================================================
#  1. SEMANTIC MODEL ROUTING ("The Hardware")
# =========================================================================


class ModelCriteria(BaseModel):
    """
    Defines 'What kind of model' is needed.
    Supports Multi-Model Routing for reliability (Fallback) or scale (Round Robin).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    strategy: RoutingStrategy = Field("balanced", description="Optimization target for model selection.")
    min_context: int | None = Field(None, description="Minimum required context window (tokens).")
    capabilities: list[ModelCapability] | None = Field(None, description="Hard technical requirements.")
    compliance: list[ComplianceStandard] | None = Field(None, description="Regulatory constraints.")
    max_cost_per_m_tokens: float | None = Field(None, description="FinOps circuit breaker.")

    # Multi-Model Routing
    routing_mode: RoutingMode = Field("single", description="How to handle multiple matching models.")

    provider_whitelist: list[str] | None = None
    specific_models: list[str] | None = Field(None, description="Explicit list of model IDs to route between.")


# Type alias: A model can be a hardcoded ID ("gpt-4") OR a semantic policy
ModelRef = str | ModelCriteria


# =========================================================================
#  2. COGNITIVE ARCHITECTURES ("The Software")
# =========================================================================


class BaseReasoning(BaseModel):
    """Base configuration for System 2 cognitive processes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: ModelRef = Field(..., description="The primary model responsible for execution.")
    temperature: float = Field(0.0, description="Sampling temperature.")
    max_tokens: int | None = Field(None, description="Hard limit on output tokens.")

    # *** FIX 3: GUIDED DECODING ***
    # Enforces syntax constraints at the token level (SOTA reliability)
    guided_decoding: GuidedDecodingMode = Field(
        "none", description="If set, restricts the model to output valid syntax only."
    )

    # *** UPGRADE: CONSTITUTIONAL AI ***
    constitution: ConstitutionalScope | None = Field(None, description="Intrinsic safety constraints.")

    def required_capabilities(self) -> list[str]:
        """Returns capabilities required by this engine."""
        return []


class StandardReasoning(BaseReasoning):
    """Linear Chain-of-Thought (CoT) / ROMA."""

    type: Literal["standard"] = "standard"
    thoughts_max: int = Field(5, description="Max sequential reasoning steps.")
    min_confidence: float = Field(0.7, description="Minimum confidence score to proceed.")
    forcing_function: str | None = Field(None, description="Force the start of the assistant's response.")


class AdaptiveReasoning(BaseReasoning):
    """
    Adaptive Reasoning (Test-Time Scaling).
    Dynamically expands the reasoning trace until confidence is met or budget is exhausted.
    """

    type: Literal["adaptive"] = "adaptive"

    max_compute_tokens: int = Field(..., gt=0, description="Maximum tokens allocated for internal reasoning.")
    max_duration_seconds: float = Field(..., gt=0.0, description="Time budget for reasoning.")
    scaling_mode: Literal["depth_first", "breadth_first", "hybrid"] = Field(..., description="Scaling strategy.")

    min_confidence_score: float = Field(..., ge=0.0, le=1.0, description="Threshold to halt reasoning (0.0 - 1.0).")
    verifier_model: ModelRef = Field(..., description="External judge model to score thoughts.")

    # Fallback
    halt_on_budget_exhaustion: bool = Field(
        True, description="If True, return best guess when budget fails. If False, error."
    )


class AttentionReasoning(BaseReasoning):
    """
    System 2 Attention (S2A).
    Filters and rewrites input context to maximize signal-to-noise ratio.
    """

    type: Literal["attention"] = "attention"

    attention_mode: AttentionMode = Field("rephrase", description="Method for sanitizing input.")
    # The model used to filter the noise (can be smaller/faster than the main reasoning model)
    focus_model: ModelRef | None = Field(None, description="Model used for the S2A filtering step.")


class BufferReasoning(BaseReasoning):
    """
    Buffer of Thoughts (BoT).
    Retrieves and STORES thought templates to solve routine problems.
    """

    type: Literal["buffer"] = "buffer"

    max_templates: int = Field(3, description="Max templates to retrieve.")
    similarity_threshold: float = Field(0.75, description="Min cosine similarity.")
    template_collection: str = Field(..., description="Vector collection name.")

    # *** FIX 1: LEARNING STRATEGY ***
    # Allows the agent to contribute new knowledge back to the buffer
    learning_strategy: BoTLearningStrategy = Field(
        "read_only", description="Whether to save successful executions back to the buffer."
    )


class TreeSearchReasoning(BaseReasoning):
    """Language Agent Tree Search (LATS) with MCTS."""

    type: Literal["tree_search"] = "tree_search"

    depth: int = Field(3, description="Max tree depth.")
    branching_factor: int = Field(3, description="Options per node.")
    simulations: int = Field(5, description="MCTS simulation budget.")
    exploration_weight: float = Field(1.41, description="UCT exploration term.")

    evaluator_model: ModelRef | None = Field(None, description="Model used to score leaf nodes.")


class DecompositionReasoning(BaseReasoning):
    """Decomposition (Atom of Thoughts) DAG splitting."""

    type: Literal["decomposition"] = "decomposition"

    decomposition_breadth: int = 3
    contract_every_steps: int = 2
    global_context_window: int = 4096


class CouncilReasoning(BaseReasoning):
    """Multi-Persona Consensus."""

    type: Literal["council"] = "council"

    personas: list[str] = Field(..., description="List of system prompts.")
    proposal_count: int = 1
    voting_mode: Literal["unanimous", "majority", "weighted"] = "majority"
    rounds: int = 1
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
    fast_comparison_mode: FastComparisonMode = Field(
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
    verification_mode: VerificationMode = Field(
        "ambiguous_only", description="When to trigger the deep similarity_model check."
    )

    similarity_model: ModelRef | None = Field(
        None, description="The LLM used for deep semantic verification if triggered."
    )

    # --- 2. Consensus & Tie-Breaking ---
    aggregation: AggregationStrategy = "majority_vote"

    # Tie-Breaker: If models disagree, this judge decides.
    judge_model: ModelRef | None = Field(None, description="The 'Supreme Court' model that resolves conflicts.")


class RedTeamingReasoning(BaseReasoning):
    """
    Agentic Red Teaming (ART).
    Proactive adversarial simulation engine.
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
    attack_strategy: AttackStrategy = Field("crescendo", description="The algorithmic protocol for generating attacks.")

    max_turns: int = Field(5, description="Maximum conversation depth/trajectory.")
    success_criteria: str = Field(
        ..., description="Natural language definition of a successful break (e.g. 'PII Leakage')."
    )


class ComputerUseReasoning(BaseReasoning):
    """
    Computer Use / GUI Automation.
    Enables 'Operator Agents' to control desktop environments.
    """

    type: Literal["computer_use"] = "computer_use"

    # Environment Configuration
    screen_resolution: tuple[int, int] | None = Field(
        None, description="Target display dimensions (width, height). If None, auto-detected."
    )

    # *** FIX 2: COORDINATE SYSTEM ***
    # Critical for model portability across screen sizes
    coordinate_system: CoordinateSystem = Field("normalized_0_1", description="Coordinate format (pixels vs relative).")

    # Interaction Protocol
    # native_os: Uses XY coordinates and OS events (clicks, hotkeys).
    # browser_dom: Uses HTML selectors and JS events (Playwright style).
    # hybrid: Allows switching between OS and DOM interaction.
    interaction_mode: InteractionMode = Field(
        "native_os", description="The layer at which the agent perceives and acts."
    )

    # Safety Governance
    allowed_actions: list[AllowedAction] = Field(
        default=["click", "type", "scroll", "screenshot"],
        description="Allow-list of permitted GUI operations.",
    )

    screenshot_frequency_ms: int = Field(1000, description="Delay between visual observation frames (in milliseconds).")

    def required_capabilities(self) -> list[str]:
        return ["computer_use"]


class GraphReasoning(BaseReasoning):
    """
    GraphRAG (Graph-based Retrieval Augmented Generation).
    Performs retrieval over a Knowledge Graph to capture structural relationships
    and multi-hop reasoning paths that Vector RAG misses.
    """

    type: Literal["graph"] = "graph"

    # 1. The Database Connection
    graph_store: str = Field(..., description="Identifier for the Knowledge Graph (e.g. 'neo4j-prod').")

    # 2. The Model acting as the 'Graph Navigator'
    # Used to generate Cypher/Gremlin queries or extract entity keywords from the prompt.
    extraction_model: ModelRef | None = Field(
        None, description="Model used to translate user prompt into graph queries."
    )

    # 3. SOTA Retrieval Strategies
    # local: "Entity-Centric". Good for "Who is X?" or "How are X and Y related?"
    # global: "Corpus-Centric". Good for "What are the themes?" (uses pre-computed community summaries).
    # hybrid: The best of both worlds.
    retrieval_mode: GraphRetrievalMode = Field("local", description="Strategy for traversing the graph.")

    # Local Mode Constraints
    max_hops: int = Field(2, description="Traversal depth for local neighbor search.")

    # Global Mode Constraints
    # GraphRAG builds hierarchical communities (Level 0 = Root, Level 1 = Broad Clusters, Level 2 = Specifics).
    community_level: int = Field(1, description="For global search: which level of community summaries to query.")


# -------------------------------------------------------------------------
# POLYMORPHIC UNION
# -------------------------------------------------------------------------
ReasoningConfig = Annotated[
    StandardReasoning
    | AdaptiveReasoning
    | AttentionReasoning
    | BufferReasoning
    | TreeSearchReasoning
    | DecompositionReasoning
    | CouncilReasoning
    | EnsembleReasoning
    | RedTeamingReasoning
    | ComputerUseReasoning
    | GraphReasoning,
    Field(discriminator="type"),
]


# =========================================================================
#  3. SYSTEM 1 & OVERSIGHT
# =========================================================================


class FastPath(BaseModel):
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


__all__ = [
    "AdaptiveReasoning",
    "AttentionReasoning",
    "BaseReasoning",
    "BufferReasoning",
    "ComputerUseReasoning",
    "ConstitutionalScope",
    "CouncilReasoning",
    "DecompositionReasoning",
    "EnsembleReasoning",
    "FastPath",
    "GraphReasoning",
    "ModelCriteria",
    "ModelRef",
    "Optimizer",
    "ReasoningConfig",
    "RedTeamingReasoning",
    "StandardReasoning",
    "Supervision",
    "TreeSearchReasoning",
]
