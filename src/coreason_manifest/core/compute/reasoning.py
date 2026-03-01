from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.core.compute.resources import ModelProfile
from coreason_manifest.core.primitives.constants import NodeCapability
from coreason_manifest.core.primitives.registry import register_engine, resolve_engine_union
from coreason_manifest.core.primitives.types import WasiCapability

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

    strategy: Annotated[RoutingStrategy, Field(description="Optimization target for model selection.")] = "balanced"
    min_context: Annotated[int | None, Field(description="Minimum required context window (tokens).")] = None
    capabilities: Annotated[list[ModelCapability] | None, Field(description="Hard technical requirements.")] = None
    compliance: Annotated[list[ComplianceStandard] | None, Field(description="Regulatory constraints.")] = None
    max_cost_per_m_tokens: Annotated[float | None, Field(description="FinOps circuit breaker.")] = None

    # Multi-Model Routing
    routing_mode: Annotated[RoutingMode, Field(description="How to handle multiple matching models.")] = "single"

    provider_whitelist: list[str] | None = None
    specific_models: Annotated[list[str] | None, Field(description="Explicit list of model IDs to route between.")] = (
        None
    )
    primary_profile: ModelProfile | None = Field(
        None,
        description="Explicit profile of the main model to use.",
        examples=[{"provider": "openai", "model_id": "gpt-4o"}],
    )
    escalation_profile: ModelProfile | None = Field(
        None,
        description="Explicit profile of the fallback model to use.",
        examples=[{"provider": "openai", "model_id": "o1-preview"}],
    )


# Type alias: A model can be a hardcoded ID ("gpt-4") OR a semantic policy
ModelRef = str | ModelCriteria


# =========================================================================
#  2. COGNITIVE ARCHITECTURES ("The Software")
# =========================================================================


class ReviewStrategy(StrEnum):
    NONE = "none"
    BASIC = "basic"
    ADVERSARIAL = "adversarial"
    CAUSAL = "causal"
    CONSENSUS = "consensus"


class AdversarialConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    persona: str = "skeptic"
    attack_vectors: list[str] = Field(default_factory=list)


class GapScanConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    enabled: bool = False
    confidence_threshold: float = 0.8


class ConstitutionalScope(BaseModel):
    """
    Defines the ethical and safety boundaries for the cognitive process.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    principles: list[str] = Field(..., description="List of safety principles.")
    enforcement: Literal["warning", "block", "correction"] = Field(..., description="Action on violation.")
    inject_into_system_prompt: Annotated[bool, Field(description="Whether to prepend principles to the prompt.")] = True


class BaseReasoning(BaseModel):
    """Base configuration for System 2 cognitive processes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: Annotated[ModelRef, Field(description="The primary model responsible for execution.")]
    temperature: Annotated[float, Field(description="Sampling temperature.")] = 0.0
    max_tokens: Annotated[int | None, Field(description="Hard limit on output tokens.")] = None

    # *** FIX 3: GUIDED DECODING ***
    # Enforces syntax constraints at the token level (SOTA reliability)
    guided_decoding: Annotated[
        GuidedDecodingMode, Field(description="If set, restricts the model to output valid syntax only.")
    ] = "none"

    # *** UPGRADE: CONSTITUTIONAL AI ***
    constitution: Annotated[ConstitutionalScope | None, Field(description="Intrinsic safety constraints.")] = None

    review_strategy: ReviewStrategy = Field(default=ReviewStrategy.NONE)
    adversarial_config: AdversarialConfig | None = None
    gap_scan: GapScanConfig | None = None
    max_revisions: int = 1

    @model_validator(mode="after")
    def _validate_adversarial(self) -> "BaseReasoning":
        if self.review_strategy == ReviewStrategy.ADVERSARIAL and self.adversarial_config is None:
            raise ValueError("adversarial_config is required when review_strategy is ADVERSARIAL")
        return self

    def required_capabilities(self) -> list[str]:
        """Returns a list of high-risk capabilities required by this engine."""
        return []


@register_engine
class StandardReasoning(BaseReasoning):
    """Linear Chain-of-Thought (CoT) / ROMA."""

    type: Literal["standard"] = "standard"
    thoughts_max: Annotated[int, Field(description="Max sequential reasoning steps.")] = 5
    min_confidence: Annotated[float, Field(description="Minimum confidence score to proceed.")] = 0.7
    forcing_function: Annotated[str | None, Field(description="Force the start of the assistant's response.")] = None


@register_engine
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
    halt_on_budget_exhaustion: Annotated[
        bool, Field(description="If True, return best guess when budget fails. If False, error.")
    ] = True


@register_engine
class AttentionReasoning(BaseReasoning):
    """
    System 2 Attention (S2A).
    Filters and rewrites input context to maximize signal-to-noise ratio.
    """

    type: Literal["attention"] = "attention"

    attention_mode: Annotated[AttentionMode, Field(description="Method for sanitizing input.")] = "rephrase"
    # The model used to filter the noise (can be smaller/faster than the main reasoning model)
    focus_model: Annotated[ModelRef | None, Field(description="Model used for the S2A filtering step.")] = None


@register_engine
class BufferReasoning(BaseReasoning):
    """
    Buffer of Thoughts (BoT).
    Retrieves and STORES thought templates to solve routine problems.
    """

    type: Literal["buffer"] = "buffer"

    max_templates: Annotated[int, Field(description="Max templates to retrieve.")] = 3
    similarity_threshold: Annotated[float, Field(description="Min cosine similarity.")] = 0.75
    template_collection: Annotated[str, Field(description="Vector collection name.")]

    # *** FIX 1: LEARNING STRATEGY ***
    # Allows the agent to contribute new knowledge back to the buffer
    learning_strategy: Annotated[
        BoTLearningStrategy, Field(description="Whether to save successful executions back to the buffer.")
    ] = "read_only"


@register_engine
class TreeSearchReasoning(BaseReasoning):
    """Language Agent Tree Search (LATS) with MCTS."""

    type: Literal["tree_search"] = "tree_search"

    depth: Annotated[int, Field(description="Max tree depth.")] = 3
    branching_factor: Annotated[int, Field(description="Options per node.")] = 3
    simulations: Annotated[int, Field(description="MCTS simulation budget.")] = 5
    exploration_weight: Annotated[float, Field(description="UCT exploration term.")] = 1.41

    evaluator_model: Annotated[ModelRef | None, Field(description="Model used to score leaf nodes.")] = None


@register_engine
class DecompositionReasoning(BaseReasoning):
    """Decomposition (Atom of Thoughts) DAG splitting."""

    type: Literal["decomposition"] = "decomposition"

    decomposition_breadth: int = 3
    contract_every_steps: int = 2
    global_context_window: int = 4096


@register_engine
class CouncilReasoning(BaseReasoning):
    """Multi-Persona Consensus."""

    type: Literal["council"] = "council"

    personas: list[str] = Field(..., description="List of system prompts.")
    proposal_count: int = 1
    voting_mode: Literal["unanimous", "majority", "weighted"] = "majority"
    rounds: int = 1
    tie_breaker_model: ModelRef | None = None


@register_engine
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
    fast_comparison_mode: Annotated[
        FastComparisonMode, Field(description="Method for initial cheap agreement check.")
    ] = "embedding"

    # Thresholds for the Fast Path
    # Score > agreement_threshold -> Auto-Accept as Same.
    # Score < disagreement_threshold -> Auto-Reject as Different.
    # Between -> Ambiguous (Trigger Slow Path).
    agreement_threshold: Annotated[float, Field(description="High confidence match threshold.")] = 0.85
    disagreement_threshold: Annotated[float, Field(description="Low confidence mismatch threshold.")] = 0.60

    # Slow Path Trigger
    # 'ambiguous_only': Trigger LLM check only if score is in the grey zone (0.60-0.85).
    # 'always': Always double-check with LLM (Paranoid mode).
    # 'never': Trust the fast path implicitly (Fastest).
    verification_mode: Annotated[
        VerificationMode, Field(description="When to trigger the deep similarity_model check.")
    ] = "ambiguous_only"

    similarity_model: Annotated[
        ModelRef | None, Field(description="The LLM used for deep semantic verification if triggered.")
    ] = None

    # --- 2. Consensus & Tie-Breaking ---
    aggregation: AggregationStrategy = "majority_vote"

    # Tie-Breaker: If models disagree, this judge decides.
    judge_model: Annotated[ModelRef | None, Field(description="The 'Supreme Court' model that resolves conflicts.")] = (
        None
    )

    @model_validator(mode="after")
    def validate_verification_model(self) -> "EnsembleReasoning":
        if self.verification_mode in ("always", "ambiguous_only") and self.similarity_model is None:
            raise ValueError(
                f"A 'similarity_model' is strictly required when verification_mode is '{self.verification_mode}'."
            )
        return self


@register_engine
class RedTeamingReasoning(BaseReasoning):
    """
    Agentic Red Teaming (ART).
    Proactive adversarial simulation engine.
    """

    type: Literal["red_teaming"] = "red_teaming"

    # The adversarial agent (Red Team)
    attacker_model: Annotated[ModelRef, Field(description="The model configured to generate attack vectors.")]

    # The victim agent (Blue Team). If None, the agent attacks itself (Self-Correction).
    target_model: Annotated[ModelRef | None, Field(description="The target model under evaluation.")] = None

    # SOTA Attack Vectors (2025/2026)
    # crescendo: Multi-turn context escalation.
    # refusal_suppression: Rhetorical constraints to prevent standard refusals.
    # payload_splitting: Breaking malicious payloads across tokens.
    # goat: Generative Offensive Agent Tester (Tree-based planning).
    # emergence_boosting: Pressure testing to elicit latent behaviors.
    attack_strategy: Annotated[
        AttackStrategy, Field(description="The algorithmic protocol for generating attacks.")
    ] = "crescendo"

    max_turns: Annotated[int, Field(description="Maximum conversation depth/trajectory.")] = 5
    success_criteria: Annotated[
        str, Field(description="Natural language definition of a successful break (e.g. 'PII Leakage').")
    ]

    @property
    def to_node_model(self) -> Any:
        return None


@register_engine
class ComputerUseReasoning(BaseReasoning):
    """
    Computer Use / GUI Automation.
    Enables 'Operator Agents' to control desktop environments.
    """

    type: Literal["computer_use"] = "computer_use"

    # Environment Configuration
    screen_resolution: Annotated[
        tuple[int, int] | None, Field(description="Target display dimensions (width, height). If None, auto-detected.")
    ] = None

    # *** FIX 2: COORDINATE SYSTEM ***
    # Critical for model portability across screen sizes
    coordinate_system: Annotated[CoordinateSystem, Field(description="Coordinate format (pixels vs relative).")] = (
        "normalized_0_1"
    )

    # Interaction Protocol
    # native_os: Uses XY coordinates and OS events (clicks, hotkeys).
    # browser_dom: Uses HTML selectors and JS events (Playwright style).
    # hybrid: Allows switching between OS and DOM interaction.
    interaction_mode: Annotated[
        InteractionMode, Field(description="The layer at which the agent perceives and acts.")
    ] = "native_os"

    # Safety Governance
    allowed_actions: Annotated[list[AllowedAction], Field(description="Allow-list of permitted GUI operations.")] = [
        "click",
        "type",
        "scroll",
        "screenshot",
    ]

    screenshot_frequency_ms: Annotated[
        int, Field(description="Delay between visual observation frames (in milliseconds).")
    ] = 1000

    def required_capabilities(self) -> list[str]:
        return [NodeCapability.COMPUTER_USE.value]


@register_engine
class CodeExecutionReasoning(BaseReasoning):
    """
    Executes Python code in a sandboxed environment.
    """

    type: Literal["code_execution"] = "code_execution"

    # Environment
    allow_network: Annotated[bool, Field(description="Allow external network access.")] = False
    timeout_seconds: Annotated[float, Field(description="Max execution time.")] = 30.0

    def required_capabilities(self) -> list[str]:
        return [NodeCapability.CODE_EXECUTION.value]


@register_engine
class GraphReasoning(BaseReasoning):
    """
    GraphRAG (Graph-based Retrieval Augmented Generation).
    Performs retrieval over a Knowledge Graph to capture structural relationships
    and multi-hop reasoning paths that Vector RAG misses.
    """

    type: Literal["graph"] = "graph"

    # 1. The Database Connection
    graph_store: Annotated[str, Field(description="Identifier for the Knowledge Graph (e.g. 'neo4j-prod').")]

    # 2. The Model acting as the 'Graph Navigator'
    # Used to generate Cypher/Gremlin queries or extract entity keywords from the prompt.
    extraction_model: Annotated[
        ModelRef | None, Field(description="Model used to translate user prompt into graph queries.")
    ] = None

    # 3. SOTA Retrieval Strategies
    # local: "Entity-Centric". Good for "Who is X?" or "How are X and Y related?"
    # global: "Corpus-Centric". Good for "What are the themes?" (uses pre-computed community summaries).
    # hybrid: The best of both worlds.
    retrieval_mode: Annotated[GraphRetrievalMode, Field(description="Strategy for traversing the graph.")] = "local"

    # Local Mode Constraints
    max_hops: Annotated[int, Field(description="Traversal depth for local neighbor search.")] = 2

    # Global Mode Constraints
    # GraphRAG builds hierarchical communities (Level 0 = Root, Level 1 = Broad Clusters, Level 2 = Specifics).
    community_level: Annotated[
        int, Field(description="For global search: which level of community summaries to query.")
    ] = 1


@register_engine
class WasmExecutionReasoning(BaseReasoning):
    """
    Executes tasks in an isolated WebAssembly (Wasm) sandbox.
    """

    type: Literal["wasm_execution"] = "wasm_execution"

    memory_limit_mb: Annotated[int, Field(gt=0, description="Memory limit for the Wasm sandbox in megabytes.")]
    imported_host_functions: Annotated[
        list[str], Field(default_factory=list, description="List of allowed host functions the Wasm module can call.")
    ]
    wasi_capabilities: Annotated[
        list[WasiCapability],
        Field(default_factory=list, description="List of enabled WASI capabilities (e.g., 'network', 'fs_read')."),
    ]

    def required_capabilities(self) -> list[str]:
        return [NodeCapability.WASM_EXECUTION.value]


# -------------------------------------------------------------------------
# POLYMORPHIC UNION
# -------------------------------------------------------------------------
ReasoningConfig: Any = resolve_engine_union()


# =========================================================================
#  3. SYSTEM 1 & OVERSIGHT
# =========================================================================


class FastPath(BaseModel):
    """Configuration for System 1 (Fast) reactions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: ModelRef
    timeout_ms: int
    caching: bool = True


class Optimizer(BaseModel):
    """Self-Improvement / DSPy-style optimization."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    teacher_model: str
    metric: str
    max_demonstrations: int


__all__ = [
    "AdaptiveReasoning",
    "AdversarialConfig",
    "AttentionReasoning",
    "BaseReasoning",
    "BufferReasoning",
    "CodeExecutionReasoning",
    "ComputerUseReasoning",
    "ConstitutionalScope",
    "CouncilReasoning",
    "DecompositionReasoning",
    "EnsembleReasoning",
    "FastPath",
    "GapScanConfig",
    "GraphReasoning",
    "ModelCriteria",
    "ModelRef",
    "Optimizer",
    "ReasoningConfig",
    "RedTeamingReasoning",
    "ReviewStrategy",
    "StandardReasoning",
    "TreeSearchReasoning",
    "WasmExecutionReasoning",
]
