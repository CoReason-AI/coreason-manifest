from __future__ import annotations

import ast
import hashlib
import ipaddress
import json
import math
import re
import urllib.parse
from enum import StrEnum
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, field_validator, model_validator


def _validate_payload_bounds(value: Any, current_depth: int = 0) -> Any:
    """
    AGENT INSTRUCTION: Mathematically bound recursive dictionary payloads
    to prevent OOM/CPU exhaustion during EpistemicLedger hashing.
    """
    max_depth = 10
    max_dict_keys = 100
    max_list_items = 1000
    max_str_len = 10000

    if current_depth > max_depth:
        raise ValueError(f"Payload exceeds maximum recursion depth of {max_depth}")

    if isinstance(value, dict):
        if len(value) > max_dict_keys:
            raise ValueError(f"Dictionary exceeds maximum key count of {max_dict_keys}")
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError("Dictionary keys must be strings")
            if len(k) > max_str_len:
                raise ValueError(f"Dictionary key exceeds max string length of {max_str_len}")
            _validate_payload_bounds(v, current_depth + 1)
    elif isinstance(value, list):
        if len(value) > max_list_items:
            raise ValueError(f"List exceeds maximum item count of {max_list_items}")
        for item in value:
            _validate_payload_bounds(item, current_depth + 1)
    elif isinstance(value, str):
        if len(value) > max_str_len:
            raise ValueError(f"String exceeds max length of {max_str_len}")

    return value


type AuctionType = Literal["sealed_bid", "dutch", "vickrey"]

type CausalInterval = Literal["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]

type CrossoverType = Literal["uniform_blend", "single_point", "heuristic"]


class InformationClassification(StrEnum):
    """
    Standardized Information Flow Control (IFC) lattice boundaries.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


type FaultType = Literal[
    "context_overload",
    "incorrect_context",
    "format_corruption",
    "latency_spike",
    "token_throttle",
    "network_degradation",
    "temporal_dilation",
    "dependency_blackout",
]

type GitSHA = Annotated[
    str,
    Field(
        pattern="^[a-f0-9]{40}$",
        description="A Tamper-evident provenance marker.",
        examples=["a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"],
        min_length=40,
        max_length=40,
    ),
]

type CognitiveTier = Literal["working", "episodic", "semantic"]

type NodeID = Annotated[
    str,
    Field(
        min_length=7,
        pattern="^did:[a-z0-9]+:[a-zA-Z0-9.\\-_:]+$",
        description="A Decentralized Identifier (DID) representing a cryptographically accountable principal within the swarm.",  # noqa: E501
    ),
]

type OptimizationDirection = Literal["maximize", "minimize"]

type PatchOperation = Literal["add", "remove", "replace", "copy", "move", "test"]

type ProfileID = Annotated[
    str,
    Field(
        pattern="^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="A deterministic cognitive routing boundary that defines the non-monotonic instruction set for the agent.",  # noqa: E501
        examples=["default_assistant", "code_expert"],
    ),
]


class RiskLevel(StrEnum):
    """
    Cryptographic risk classification for governance.
    Order matters: safe < standard < critical.
    """

    SAFE = "safe"
    STANDARD = "standard"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        """Return the numeric weight corresponding to the risk level."""
        if self == RiskLevel.SAFE:
            return 0
        if self == RiskLevel.STANDARD:
            return 1
        return 2


type SanitizationAction = Literal["redact", "hash", "drop_event", "trigger_quarantine"]

type SemanticVersion = Annotated[
    str,
    Field(
        pattern="^\\d+\\.\\d+\\.\\d+$",
        description="An Immutable structural checkpoint.",
        examples=["1.0.0", "0.1.0", "2.12.5"],
    ),
]

type SpanKind = Literal["client", "server", "producer", "consumer", "internal"]

type SpanStatusCode = Literal["unset", "ok", "error"]


class SystemRole(StrEnum):
    """
    Standardized Persona-Based Access Control (PBAC) authority delegation perimeters.
    """

    SYSTEM_ADMIN = "system_admin"
    TENANT_ADMIN = "tenant_admin"
    AGENT_BUILDER = "agent_builder"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    VIEWER = "viewer"
    MACHINE_SERVICE = "machine_service"


class TensorDType(StrEnum):
    """Mathematical data types for tensor payloads."""

    FLOAT32 = "float32"
    FLOAT64 = "float64"
    INT8 = "int8"
    UINT8 = "uint8"
    INT32 = "int32"
    INT64 = "int64"

    @property
    def bytes_per_element(self) -> int:
        """Returns the byte footprint per element."""
        mapping = {"float32": 4, "float64": 8, "int8": 1, "uint8": 1, "int32": 4, "int64": 8}
        return mapping[self.value]


type TieBreaker = Literal["lowest_cost", "lowest_latency", "highest_confidence", "random"]

type ToolID = Annotated[
    str,
    Field(
        pattern="^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="A cryptographically deterministic capability pointer binding the agent to a verifiable spatial environment.",  # noqa: E501
        examples=["calculator", "web_search"],
    ),
]

type TopologyHash = Annotated[
    str,
    Field(
        pattern="^[a-f0-9]{64}$",
        description="A strictly typed SHA-256 hash pointing to a historically executed topological state.",
    ),
]


class CoreasonBaseModel(BaseModel):
    """
    Base class for all domain models in the Coreason Manifest.

    This model guarantees deterministic serialization for Tamper-Evident Hash Chains and
    Merkle-Tree Attestations, preventing epistemic contamination.

    Enforces:
    1. Immutability (frozen=True) - Essential for distributed state consistency.
    2. Strict validation (strict=True) - No silent coercion.
    3. Forbidden extra fields (extra='forbid') - Schema strictness.
    4. Deterministic serialization - Keys are sorted for hash consistency.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_assignment=True, strict=True)

    def __hash__(self) -> int:
        try:
            h: int = object.__getattribute__(self, "_cached_hash")
            return h
        except AttributeError:
            h = hash(self.model_dump_canonical())
            object.__setattr__(self, "_cached_hash", h)
            return int(h)

    def model_dump_canonical(self) -> bytes:
        """Return a strictly sorted, canonical JSON serialization for cryptographic hashing."""
        raw_dict = self.model_dump(mode="json", exclude_none=True, by_alias=True)

        def _sort_collections(obj: Any) -> Any:
            """
            Recursively sorts dictionaries for canonical serialization while explicitly preserving
            RFC 8785 array ordering.
            """
            if isinstance(obj, dict):
                return {k: _sort_collections(v) for k, v in sorted(obj.items())}
            if isinstance(obj, list):
                return [_sort_collections(v) for v in obj]
            return obj

        canonical_dict = _sort_collections(raw_dict)
        return json.dumps(canonical_dict, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


class BoundingBox(CoreasonBaseModel):
    """A resolution-independent spatial region."""

    x_min: float = Field(ge=0.0, le=1.0, description="The left boundary.")
    y_min: float = Field(ge=0.0, le=1.0, description="The top boundary.")
    x_max: float = Field(ge=0.0, le=1.0, description="The right boundary.")
    y_max: float = Field(ge=0.0, le=1.0, description="The bottom boundary.")

    @model_validator(mode="after")
    def validate_geometry(self) -> Self:
        if self.x_min > self.x_max:
            raise ValueError("x_min cannot be strictly greater than x_max.")
        if self.y_min > self.y_max:
            raise ValueError("y_min cannot be strictly greater than y_max.")
        return self


class DynamicLayoutTemplate(CoreasonBaseModel):
    """Schema representing a template for dynamic grid layouts."""

    layout_tstring: str = Field(
        description="A Python 3.14 t-string template definition for dynamic UI grid evaluation."
    )

    @field_validator("layout_tstring", mode="after")
    @classmethod
    def validate_tstring(cls, v: str) -> str:
        """
        AGENT INSTRUCTION: Mathematically prove the absence of kinetic execution
        bleed by parsing the layout string into an Abstract Syntax Tree.
        """
        try:
            tree = ast.parse(v, mode="exec")
        except SyntaxError:
            pass
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    raise ValueError("Kinetic execution bleed detected: AST contains function calls.")
        return v


class ExecutionSLA(CoreasonBaseModel):
    """
    Service Level Agreement (limits) for executing a tool.
    """

    max_execution_time_ms: int = Field(
        gt=0,
        description="The maximum allowed execution time in milliseconds before the orchestrator kills the process.",
    )
    max_memory_mb: int | None = Field(
        default=None, gt=0, description="The maximum memory footprint allowed for the tool's execution sandbox."
    )


class FacetMatrix(CoreasonBaseModel):
    """Optional small-multiple faceting layout."""

    row_field: str | None = Field(default=None, description="The dataset field used to split the chart into rows.")
    column_field: str | None = Field(
        default=None, description="The dataset field used to split the chart into columns."
    )


class NormalizedCoordinate(CoreasonBaseModel):
    """A resolution-independent 2D spatial vector."""

    x: float = Field(ge=0.0, le=1.0, description="The normalized X-axis coordinate (0.0 = left, 1.0 = right).")
    y: float = Field(ge=0.0, le=1.0, description="The normalized Y-axis coordinate (0.0 = top, 1.0 = bottom).")


class RateCard(CoreasonBaseModel):
    """
    Economic constraints for liquid compute operations.
    """

    cost_per_million_input_tokens: float = Field(
        description="The cost per 1 million input tokens provided to the model."
    )
    cost_per_million_output_tokens: float = Field(
        description="The cost per 1 million output tokens generated by the model."
    )
    magnitude_unit: str = Field(description="The magnitude unit of the associated costs.")


class ScaleDefinition(CoreasonBaseModel):
    """The mathematical mapping constraint for a channel."""

    type: Literal["linear", "log", "time", "ordinal", "nominal"] = Field(
        description="The mathematical scale mapping data to pixels."
    )
    domain_min: float | None = Field(default=None, description="The optional minimum bound of the scale domain.")
    domain_max: float | None = Field(default=None, description="The optional maximum bound of the scale domain.")


class ChannelEncoding(CoreasonBaseModel):
    """The visual property being manipulated."""

    channel: Literal["x", "y", "color", "size", "opacity", "shape", "text"] = Field(
        description="The visual channel the data is mapped to."
    )
    field: str = Field(description="The exact column or field name from the dataset.")
    scale: ScaleDefinition | None = Field(
        default=None, description="Optional scale override for this specific channel."
    )


class SideEffectProfile(CoreasonBaseModel):
    """
    Profile for describing the side effects and idempotency of a tool.
    """

    is_idempotent: bool = Field(
        description="True if the tool can be safely retried multiple times without altering state beyond the first call."  # noqa: E501
    )
    mutates_state: bool = Field(description="True if the tool performs write operations or side-effects.")


class VerifiableEntropy(CoreasonBaseModel):
    """Passive cryptographic envelope for verifiable random functions."""

    vrf_proof: str = Field(
        min_length=10, description="The zero-knowledge cryptographic proof of fair random generation."
    )
    public_key: str = Field(
        min_length=10, description="The public key of the oracle or node used to verify the VRF proof."
    )
    seed_hash: str = Field(min_length=10, description="The SHA-256 hash of the origin seed used to initialize the VRF.")


class HardwareEnclaveAttestation(CoreasonBaseModel):
    enclave_type: Literal["intel_tdx", "amd_sev_snp", "aws_nitro", "nvidia_cc"] = Field(
        description="The physical silicon architecture generating the root-of-trust quote."
    )
    platform_measurement_hash: str = Field(
        description="The cryptographic hash of the Platform Configuration Registers (PCRs) proving the memory state was physically isolated."  # noqa: E501
    )
    hardware_signature_blob: str = Field(
        max_length=8192,
        description="The base64-encoded hardware quote signed by the silicon manufacturer's master private key.",
    )


class LatentSmoothingProfile(CoreasonBaseModel):
    """The mathematical curve used to gently taper an adversarial activation to prevent logit collapse."""

    decay_function: Literal["linear", "exponential", "cosine_annealing"] = Field(
        description="The trigonometric or algebraic function governing the attenuation curve."
    )
    transition_window_tokens: int = Field(
        gt=0, description="The exact number of forward-pass generation steps over which the decay is applied."
    )
    decay_rate_param: float | None = Field(
        default=None, description="The optional tuning parameter (e.g., half-life lambda for exponential decay)."
    )


class LogitSteganographyContract(CoreasonBaseModel):
    """Cryptographic contract for embedding undeniable, un-strippable provenance signatures
    directly into the token entropy."""

    verification_public_key_id: str = Field(
        description="The DID or public key identifier required by an auditor to reconstruct the PRF and verify the watermark."  # noqa: E501
    )
    prf_seed_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the cryptographic seed used to initialize the pseudo-random function (PRF).",
    )
    watermark_strength_delta: float = Field(
        gt=0.0,
        description="The exact logit scalar (bias) injected into the 'green list' vocabulary partition before Gumbel-Softmax sampling.",  # noqa: E501
    )
    target_bits_per_token: float = Field(
        gt=0.0,
        description="The information-theoretic density of the payload being embedded into the generative stream.",
    )
    context_history_window: int = Field(
        ge=0,
        description="The k-gram rolling window size of preceding tokens hashed into the PRF state to ensure robustness against text cropping.",  # noqa: E501
    )


class ModelProfile(CoreasonBaseModel):
    """
    Abstraction for an underlying LLM provider in liquid compute.
    """

    model_name: str = Field(description="The identifier of the underlying model.")
    provider: str = Field(description="The name of the provider hosting the model.")
    context_window_size: int = Field(description="The maximum context window size in tokens.")
    capabilities: list[str] = Field(description="A list of supported capabilities by the model.")
    rate_card: RateCard = Field(description="The economic cost definition associated with the model.")
    supported_functional_experts: list[str] = Field(
        default_factory=list,
        description="A declarative list of specialized functional expert clusters (e.g., 'falsifier', 'synthesizer') physically present in this model's architecture.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "capabilities", sorted(self.capabilities))
        object.__setattr__(self, "supported_functional_experts", sorted(self.supported_functional_experts))
        return self


class PermissionBoundary(CoreasonBaseModel):
    """
    Zero-trust security boundaries for tool execution.
    """

    network_access: bool = Field(description="Whether the tool is permitted to make external network requests.")
    allowed_domains: list[str] | None = Field(
        default=None, description="Whitelist of allowed network domains if network access is true."
    )
    file_system_read_only: bool = Field(description="True if the tool is strictly forbidden from writing to the disk.")
    auth_requirements: list[str] | None = Field(
        default=None,
        description="An explicit list of authentication protocol identifiers (e.g., 'oauth2:github', 'mtls:internal') the orchestrator must negotiate before allocating compute.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.allowed_domains is not None:
            object.__setattr__(self, "allowed_domains", sorted(self.allowed_domains))
        if self.auth_requirements is not None:
            object.__setattr__(self, "auth_requirements", sorted(self.auth_requirements))
        return self


class PostQuantumSignature(CoreasonBaseModel):
    pq_algorithm: Literal["ml-dsa", "slh-dsa", "falcon"] = Field(
        description="The NIST FIPS post-quantum cryptographic algorithm used."
    )
    public_key_id: str = Field(description="The identifier of the post-quantum public evaluation key.")
    pq_signature_blob: str = Field(
        max_length=100000,
        description="The base64-encoded post-quantum signature. Bounded to 100KB to safely accommodate massive SPHINCS+ hash trees without OOM crashes.",  # noqa: E501
    )


class RoutingFrontier(CoreasonBaseModel):
    """
    Mathematical Pareto boundaries for dynamic spot-market liquid compute.
    """

    max_latency_ms: int = Field(
        gt=0, description="The absolute physical speed limit acceptable for time-to-first-token or total generation."
    )
    max_cost_magnitude_per_token: int = Field(
        gt=0, description="The strict magnitude ceiling. MUST be an integer to maintain cryptographic determinism."
    )
    min_capability_score: float = Field(
        ge=0.0, le=1.0, description="The cognitive capability floor required for the task (0.0 to 1.0)."
    )
    tradeoff_preference: Literal[
        "latency_optimized", "cost_optimized", "capability_optimized", "carbon_optimized", "balanced"
    ] = Field(description="The mathematical optimization vector to break ties within the frontier.")
    max_carbon_intensity_gco2eq_kwh: float | None = Field(
        default=None,
        ge=0.0,
        description="The maximum operational carbon intensity of the physical data center grid allowed for this agent's routing.",  # noqa: E501
    )


class SaeFeatureActivation(CoreasonBaseModel):
    feature_index: int = Field(
        ge=0,
        description="The exact dimensional index of the monosemantic feature in the Sparse Autoencoder dictionary.",
    )
    activation_magnitude: float = Field(
        description="The mathematical strength of this feature's activation during the forward pass."
    )
    interpretability_label: str | None = Field(
        default=None,
        description="The human-readable semantic concept mapped to this feature (e.g., 'sycophancy', 'truth_retrieval').",  # noqa: E501
    )


class ActivationSteeringContract(CoreasonBaseModel):
    """
    Hardware-level contract for Representation Engineering via activation injection/ablation.
    """

    steering_vector_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the extracted RepE control tensor (e.g., the 'caution' vector).",
    )
    injection_layers: list[int] = Field(
        min_length=1, description="The specific transformer layer indices where this vector must be applied."
    )
    scaling_factor: float = Field(
        description="The mathematical magnitude/strength of the injection (can be negative for ablation)."
    )
    vector_modality: Literal["additive", "ablation", "clamping"] = Field(
        description="The tensor operation to perform: add the vector, subtract it, or clamp activations to its bounds."
    )


class CognitiveRoutingDirective(CoreasonBaseModel):
    """
    Hardware-level contract overriding MoE routing to enforce functional/specialist paths.
    """

    dynamic_top_k: int = Field(
        ge=1,
        description="The exact number of functional experts the router must activate per token. High values simulate deep cognitive strain.",  # noqa: E501
    )
    routing_temperature: float = Field(
        ge=0.0,
        description="The temperature applied to the router's softmax gate, controlling how deterministically it picks experts.",  # noqa: E501
    )
    expert_logit_biases: dict[str, float] = Field(
        default_factory=dict,
        description="Explicit tensor biases applied to the router gate. Keys are expert IDs (e.g., 'expert_falsifier'), values are logit modifiers.",  # noqa: E501
    )
    enforce_functional_isolation: bool = Field(
        default=False,
        description="If True, the orchestrator applies a hard mask (-inf) to any expert not explicitly boosted in expert_logit_biases.",  # noqa: E501
    )


class CognitiveStateProfile(CoreasonBaseModel):
    """Causal Directed Acyclic Graphs (cDAGs) and constraints for state progression."""

    urgency_index: float = Field(
        ge=0.0, le=1.0, description="Drives structural constraints; high urgency forces fast heuristic routing."
    )
    caution_index: float = Field(
        ge=0.0, le=1.0, description="Drives precision; high caution injects analytical/falsification steering vectors."
    )
    divergence_tolerance: float = Field(
        ge=0.0,
        le=1.0,
        description="The 'curiosity' metric; dictates how far the router is allowed to stray from high-probability distributions.",  # noqa: E501
    )
    activation_steering: ActivationSteeringContract | None = Field(
        default=None,
        description="The precise mathematical contract for altering the residual stream to enforce this constraint.",
    )
    moe_routing_directive: CognitiveRoutingDirective | None = Field(
        default=None,
        description="The structural mandate overriding default token routing to enforce this cognitive state.",
    )


class CognitiveUncertaintyProfile(CoreasonBaseModel):
    """Structural Causal Models (SCMs) for active epistemic bounding."""

    aleatoric_entropy: float = Field(
        ge=0.0, le=1.0, description="Irreducible ambiguity detected in the observational fields (P(y|x))."
    )
    epistemic_uncertainty: float = Field(
        ge=0.0, le=1.0, description="The causal gap demanding Do-Calculus Interventions (P(y|do(x)))."
    )
    semantic_consistency_score: float = Field(
        ge=0.0, le=1.0, description="Counterfactual Geometries representing alternative timeline vectors."
    )
    requires_abductive_escalation: bool = Field(
        description="True if epistemic_uncertainty breaches the safety threshold, requiring structural mandate escalation."  # noqa: E501
    )


class ConstitutionalRule(CoreasonBaseModel):
    """
    Defines a constitutional rule for AI governance.
    """

    rule_id: str = Field(description="Unique identifier for the constitutional rule.")
    description: str = Field(description="Detailed description of the rule.")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level if the rule is violated."
    )
    forbidden_intents: set[Annotated[str, StringConstraints(min_length=1)]] = Field(
        description="List of intents that are forbidden by this rule."
    )


class GradingCriteria(CoreasonBaseModel):
    """
    Defines criteria used for grading LLM behavior or output.
    """

    criterion_id: str = Field(description="Unique identifier for the grading criterion.")
    description: str = Field(description="Detailed description of what is being graded.")
    weight: float = Field(ge=0.0, description="Weight or significance of this criterion.")


class AdjudicationRubric(CoreasonBaseModel):
    """
    Rubric defining multiple criteria and passing threshold for algorithmic adjudication.
    """

    rubric_id: str = Field(description="Unique identifier for the rubric.")
    criteria: list[GradingCriteria] = Field(description="List of criteria used in the rubric.")
    passing_threshold: float = Field(ge=0.0, le=100.0, description="The minimum score required to pass.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "criteria", sorted(self.criteria, key=lambda x: x.criterion_id))
        return self


class PredictionMarketPolicy(CoreasonBaseModel):
    """
    The ruleset governing the market. It enforces Sybil resistance
    (via quadratic staking) and dictates when the market stops trading.
    """

    staking_function: Literal["linear", "quadratic"] = Field(
        description="The mathematical curve applied to stakes. Quadratic enforces Sybil resistance."
    )
    min_liquidity_magnitude: int = Field(ge=0, description="Minimum liquidity required.")
    convergence_delta_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The threshold indicating the market price has stabilized enough to trigger the resolution oracle.",
    )


class QuorumPolicy(CoreasonBaseModel):
    """The mathematical boundaries required to survive Byzantine failures in a decentralized swarm."""

    max_tolerable_faults: int = Field(
        ge=0,
        description="The maximum number of actively malicious, hallucinating, or degraded nodes (f) the swarm must survive.",  # noqa: E501
    )
    min_quorum_size: int = Field(
        gt=0, description="The minimum number of participating agents (N) required to form consensus."
    )
    state_validation_metric: Literal["ledger_hash", "zk_proof", "semantic_embedding"] = Field(
        description="The cryptographic material the agents must sign to submit a valid vote."
    )
    byzantine_action: Literal["quarantine", "slash_escrow", "ignore"] = Field(
        description="The deterministic punishment executed by the orchestrator against nodes that violate the consensus quorum."  # noqa: E501
    )

    @model_validator(mode="after")
    def enforce_bft_math(self) -> Self:
        """Mathematically guarantees the network can reach Byzantine agreement."""
        if self.min_quorum_size < 3 * self.max_tolerable_faults + 1:
            raise ValueError("Byzantine Fault Tolerance requires min_quorum_size (N) >= 3f + 1.")
        return self


class ConsensusPolicy(CoreasonBaseModel):
    """
    Explicit ruleset governing how a council resolves disagreements.
    """

    strategy: Literal["unanimous", "majority", "debate_rounds", "prediction_market", "pbft"] = Field(
        description="The mathematical rule for reaching agreement."
    )
    tie_breaker_node_id: NodeID | None = Field(
        default=None, description="The node authorized to break deadlocks if unanimity or majority fails."
    )
    max_debate_rounds: int | None = Field(
        default=None, description="The maximum number of argument/rebuttal cycles permitted before forced adjudication."
    )
    prediction_market_rules: PredictionMarketPolicy | None = Field(
        default=None,
        description="The strict algorithmic mechanism rules required if the strategy is prediction_market.",
    )
    quorum_rules: QuorumPolicy | None = Field(
        default=None, description="The strict Byzantine fault tolerance limits required if the strategy is 'pbft'."
    )

    @model_validator(mode="after")
    def validate_pbft_requirements(self) -> Self:
        if self.strategy == "pbft" and self.quorum_rules is None:
            raise ValueError("quorum_rules must be provided when strategy is 'pbft'.")
        return self


class RedactionRule(CoreasonBaseModel):
    """
    A specific rule for algorithmic data sanitization.
    """

    rule_id: str = Field(description="Unique identifier for the sanitization rule.")
    classification: InformationClassification = Field(description="The category of sensitive data this rule targets.")
    target_pattern: str = Field(description="The semantic entity type or declarative regex pattern to identify.")
    target_regex_pattern: str = Field(max_length=200, description="The dynamic regex pattern to target.")
    context_exclusion_zones: list[str] | None = Field(
        default=None, max_length=100, description="Specific JSON paths where this rule should NOT apply."
    )
    action: SanitizationAction = Field(description="The required algorithmic response when this pattern is detected.")
    replacement_token: str | None = Field(
        default=None, description="The strictly typed string to insert if the action is 'redact'."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.context_exclusion_zones is not None:
            object.__setattr__(self, "context_exclusion_zones", sorted(self.context_exclusion_zones))
        return self


class SaeLatentFirewall(CoreasonBaseModel):
    """A real-time mechanistic interpretability boundary that monitors and controls specific neural circuits."""

    target_feature_index: int = Field(
        ge=0,
        description="The exact dimensional index of the monosemantic feature in the Sparse Autoencoder dictionary.",
    )
    monitored_layers: list[int] = Field(
        min_length=1,
        description="The specific transformer layer indices where this feature activation must be monitored.",
    )
    max_activation_threshold: float = Field(
        ge=0.0,
        description="The mathematical magnitude limit. If the feature activates beyond this, the firewall trips.",
    )
    violation_action: Literal["clamp", "halt", "quarantine", "smooth_decay"] = Field(
        description="The tensor-level remediation applied when the threshold is breached."
    )
    clamp_value: float | None = Field(
        default=None,
        description="If violation_action is 'clamp', the physical value to which the activation tensor is forced.",
    )
    sae_dictionary_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact SAE projection matrix required to decode this feature.",
    )
    smoothing_profile: LatentSmoothingProfile | None = Field(
        default=None,
        description="The geometric parameters for continuous attenuation if violation_action is 'smooth_decay'.",
    )

    @model_validator(mode="after")
    def validate_smooth_decay(self) -> Self:
        if self.violation_action == "smooth_decay":
            if self.smoothing_profile is None:
                raise ValueError("smoothing_profile must be provided when violation_action is 'smooth_decay'.")
            if self.clamp_value is None:
                raise ValueError(
                    "clamp_value must be provided as the target asymptote when violation_action is 'smooth_decay'."
                )
        return self


class SecureSubSession(CoreasonBaseModel):
    """
    Declarative boundary for handling unredacted secrets within a temporarily isolated memory partition.
    """

    session_id: str = Field(max_length=255, description="Unique identifier for the secure session.")
    allowed_vault_keys: list[str] = Field(
        max_length=100, description="List of enterprise vault keys the agent is temporarily allowed to access."
    )
    max_ttl_seconds: int = Field(ge=1, le=3600, description="Maximum time-to-live for the unredacted memory partition.")
    description: str = Field(max_length=2000, description="Audit justification for this temporary secure session.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_vault_keys", sorted(self.allowed_vault_keys))
        return self


class DefeasibleCascade(CoreasonBaseModel):
    cascade_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this automated truth maintenance operation.",  # noqa: E501
    )
    root_falsified_event_id: str = Field(
        description="The source BeliefMutationEvent or HypothesisGenerationEvent Content Identifier (CID) that collapsed and triggered this cascade."  # noqa: E501
    )
    propagated_decay_factor: float = Field(
        ge=0.0, le=1.0, description="The calculated Entropy Penalty applied to this specific subgraph."
    )
    quarantined_event_ids: list[str] = Field(
        min_length=1,
        description="The strict list of downstream event Content Identifiers (CIDs) isolated and muted by this cascade to prevent Epistemic Contagion.",  # noqa: E501
    )
    cross_boundary_quarantine_issued: bool = Field(
        default=False,
        description="Cryptographic proof that this cascade was broadcast to the Swarm to halt epistemic contagion.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "quarantined_event_ids", sorted(self.quarantined_event_ids))
        return self


class MultimodalTokenAnchor(CoreasonBaseModel):
    """AGENT INSTRUCTION: Unified multimodal grounding mapping extracted facts to strict 1D token spans and 2D visual
    patches."""

    token_span_start: int | None = Field(
        default=None, ge=0, description="The starting index in the discrete VLM context window."
    )
    token_span_end: int | None = Field(
        default=None, ge=0, description="The ending index in the discrete VLM context window."
    )
    visual_patch_hashes: list[str] = Field(
        default_factory=list,
        description="List of SHA-256 hashes corresponding to specific VQ-VAE visual patches attended to.",
    )
    bounding_box: tuple[float, float, float, float] | None = Field(
        default=None, description="The strictly typed [x_min, y_min, x_max, y_max] normalized coordinate matrix."
    )
    block_type: Literal["paragraph", "table", "figure", "footnote", "header", "equation"] | None = Field(
        default=None, description="The structural classification of the source region."
    )

    @model_validator(mode="after")
    def validate_token_spans(self) -> Self:
        """Mathematically enforce valid 1D token sequence geometry."""
        if self.token_span_start is not None:
            if self.token_span_end is None:
                raise ValueError("If token_span_start is defined, token_span_end MUST be defined.")
            if self.token_span_end <= self.token_span_start:
                raise ValueError("token_span_end MUST be strictly greater than token_span_start.")
        elif self.token_span_end is not None:
            raise ValueError("token_span_end cannot be defined without a token_span_start.")
        return self

    @model_validator(mode="after")
    def validate_spatial_geometry(self) -> Self:
        """AGENT INSTRUCTION: Enforce mathematical spatial monotonicity."""
        if self.bounding_box is not None:
            x_min, y_min, x_max, y_max = self.bounding_box
            if x_min > x_max or y_min > y_max:
                raise ValueError(
                    f"Spatial invariant violated: min bounds (x:{x_min}, y:{y_min}) exceed max bounds (x:{x_max}, y:{y_max})"  # noqa: E501
                )
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "visual_patch_hashes", sorted(self.visual_patch_hashes))
        return self


class RollbackRequest(CoreasonBaseModel):
    request_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the causal rollback operation."  # noqa: E501
    )
    target_event_id: str = Field(
        description="The Content Identifier (CID) of the corrupted event in the EpistemicLedger to revert to."
    )
    invalidated_node_ids: list[str] = Field(
        default_factory=list,
        description="A list of nodes whose operational histories are causally tainted and must be flushed.",
    )

    @model_validator(mode="after")
    def sort_invalidated_nodes(self) -> Self:
        object.__setattr__(self, "invalidated_node_ids", sorted(self.invalidated_node_ids))
        return self


class StatePatch(CoreasonBaseModel):
    op: PatchOperation = Field(
        description="The strict RFC 6902 JSON Patch operation, acting as a deterministic state vector mutation."
    )
    path: str = Field(description="The JSON pointer indicating the exact state vector to mutate deterministically.")
    value: Any | None = Field(
        default=None,
        description="The payload to insert or test, if applicable, for this deterministic state vector mutation.",
    )


class StateDiff(CoreasonBaseModel):
    diff_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this state differential."  # noqa: E501
    )
    author_node_id: str = Field(
        description="The exact Lineage Watermark of the agent or system that authored this state mutation."
    )
    lamport_timestamp: int = Field(
        ge=0,
        description="Strict scalar logical clock used for deterministic LWW (Last-Writer-Wins) conflict resolution.",
    )
    vector_clock: dict[str, int] = Field(
        description="Causal history mapping of all known Lineage Watermarks to their latest logical mutation count at the time of authoring."  # noqa: E501
    )
    patches: list[StatePatch] = Field(
        default_factory=list, description="The exact, ordered sequence of deterministic state vector mutations."
    )
    # Note: patches is a structurally ordered sequence (Chronological Mutations) and MUST NOT be sorted.


class TemporalCheckpoint(CoreasonBaseModel):
    checkpoint_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the temporal anchor."
    )
    ledger_index: int = Field(description="The exact array index in the EpistemicLedger this checkpoint represents.")
    state_hash: str = Field(
        description="The canonical RFC 8785 SHA-256 hash of the entire topology at this exact index."
    )


class ThoughtBranch(CoreasonBaseModel):
    branch_id: str = Field(
        min_length=1,
        description="A deterministic capability pointer bounding this specific topological divergence in the Latent Scratchpad Trace.",  # noqa: E501
    )
    parent_branch_id: str | None = Field(
        default=None, description="The branch this thought diverged from, enabling tree reconstruction."
    )
    latent_content_hash: str = Field(
        pattern="^[a-f0-9]{64}$", description="The SHA-256 hash of the raw latent dimensions explored in this branch."
    )
    prm_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="The logical validity score assigned to this branch by the Process Reward Model.",
    )


class LatentScratchpadTrace(CoreasonBaseModel):
    trace_id: str = Field(
        min_length=1, description="A Content Identifier (CID) bounding this ephemeral test-time execution tree."
    )
    explored_branches: list[ThoughtBranch] = Field(
        description="All logical paths the agent attempted within this Ephemeral Epistemic Quarantine—a volatile workspace where probability waves collapse before being committed to the immutable ledger."  # noqa: E501
    )
    discarded_branches: list[str] = Field(
        description="A list of Content Identifiers (CIDs) that were explicitly pruned due to logical dead-ends."
    )
    resolution_branch_id: str | None = Field(
        default=None,
        description="The Content Identifier (CID) that successfully resolved the uncertainty and led to the final output.",  # noqa: E501
    )
    total_latent_tokens: int = Field(
        ge=0, description="The total expenditure (in tokens) spent purely on internal reasoning."
    )

    @model_validator(mode="after")
    def verify_referential_integrity(self) -> Self:
        explored_branch_ids = {branch.branch_id for branch in self.explored_branches}
        if self.resolution_branch_id is not None and self.resolution_branch_id not in explored_branch_ids:
            raise ValueError(f"resolution_branch_id '{self.resolution_branch_id}' not found in explored_branches.")
        for discarded_id in self.discarded_branches:
            if discarded_id not in explored_branch_ids:
                raise ValueError(f"discarded branch '{discarded_id}' not found in explored_branches.")
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "explored_branches", sorted(self.explored_branches, key=lambda x: x.branch_id))
        object.__setattr__(self, "discarded_branches", sorted(self.discarded_branches))
        return self


class EphemeralNamespacePartition(CoreasonBaseModel):
    """
    A hermetically sealed, ephemeral execution partition for dynamic dependency resolution.
    """

    partition_id: str = Field(min_length=1, description="Unique identifier for this ephemeral partition.")
    execution_runtime: Literal["wasm32-wasi", "riscv32-zkvm", "bpf"] = Field(
        description="The strict virtual machine target mandated for dynamic execution."
    )
    authorized_bytecode_hashes: list[str] = Field(
        min_length=1, description="The explicit whitelist of SHA-256 hashes allowed to execute within this partition."
    )
    max_ttl_seconds: int = Field(
        gt=0, description="The absolute temporal guillotine before the orchestrator drops the context."
    )
    max_vram_mb: int = Field(gt=0, description="The strict physical VRAM ceiling allocated to this partition.")
    allow_network_egress: bool = Field(
        default=False, description="Capability-based flag to allow or mathematically deny network sockets."
    )
    allow_subprocess_spawning: bool = Field(
        default=False, description="Capability-based flag to allow or deny OS-level process spawning."
    )

    @model_validator(mode="after")
    def validate_cryptographic_hashes(self) -> Self:
        for h in self.authorized_bytecode_hashes:
            if not re.match("^[a-f0-9]{64}$", h):
                raise ValueError(f"Invalid SHA-256 hash in whitelist: {h}")
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "authorized_bytecode_hashes", sorted(self.authorized_bytecode_hashes))
        return self


class ToolManifest(CoreasonBaseModel):
    """
    Declarative mathematical definition of a tool.
    """

    tool_name: str = Field(description="The exact identifier of the tool.")
    description: str = Field(description="Semantic description of what the tool does, used by the LLM for selection.")
    input_schema: dict[str, Any] = Field(
        description="The strict JSON Schema dictionary defining the required arguments."
    )
    side_effects: SideEffectProfile = Field(
        description="The declarative side-effect and idempotency profile of the tool."
    )
    permissions: PermissionBoundary = Field(description="The zero-trust security boundaries for the tool's execution.")
    sla: ExecutionSLA | None = Field(default=None, description="Execution limits for the tool.")
    is_preemptible: bool = Field(
        default=False,
        description="If True, the orchestrator is authorized to send a SIGINT to abort this tool's execution mid-flight if a BargeInInterruptEvent occurs.",  # noqa: E501
    )


class BilateralSLA(CoreasonBaseModel):
    receiving_tenant_id: str = Field(
        max_length=255, description="The strict enterprise identifier of the foreign B2B tenant receiving this payload."
    )
    max_permitted_classification: InformationClassification = Field(
        description="The absolute highest data sensitivity allowed to cross this federated boundary."
    )
    liability_limit_magnitude: int = Field(
        ge=0, description="The strict magnitude cap on cross-tenant economic liability."
    )
    permitted_geographic_regions: list[str] = Field(
        default_factory=list,
        description="Explicit whitelist of geographic regions or cloud enclaves where execution is structurally permitted (Data Residency Pinning).",  # noqa: E501
    )
    max_permitted_grid_carbon_intensity: float | None = Field(
        default=None,
        ge=0.0,
        description="Absolute structural ESG mandate. The execution graph will quarantine any federated node operating on a grid exceeding this gCO2eq/kWh threshold.",  # noqa: E501
    )
    pq_signature: PostQuantumSignature | None = Field(
        default=None, description="The quantum-resistant signature securing the multi-tenant structural boundary."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "permitted_geographic_regions", sorted(self.permitted_geographic_regions))
        return self


class FederatedDiscoveryProtocol(CoreasonBaseModel):
    broadcast_endpoints: list[str] = Field(description="A list of MCP URI endpoints open for B2B task bidding.")
    supported_ontologies: list[str] = Field(
        description="A list of cryptographic hashes of domain ontologies this swarm is capable of processing."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "broadcast_endpoints", sorted(self.broadcast_endpoints, key=str))
        object.__setattr__(self, "supported_ontologies", sorted(self.supported_ontologies))
        return self


class ActiveInferenceContract(CoreasonBaseModel):
    task_id: str = Field(min_length=1, description="Unique identifier for this active inference execution.")
    target_hypothesis_id: str = Field(description="The HypothesisGenerationEvent this task is attempting to falsify.")
    target_condition_id: str = Field(description="The specific FalsificationCondition being tested.")
    selected_tool_name: str = Field(
        description="The exact tool from the ActionSpaceManifest allocated for this experiment."
    )
    expected_information_gain: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematically estimated reduction in Epistemic Uncertainty (entropy) this tool call will yield.",  # noqa: E501
    )
    execution_cost_budget_magnitude: int = Field(
        ge=0, description="The maximum economic expenditure authorized to run this specific scientific test."
    )


class AdjudicationIntent(CoreasonBaseModel):
    type: Literal["forced_adjudication"] = Field(
        default="forced_adjudication", description="Discriminator for breaking deadlocks within a CouncilTopology."
    )
    deadlocked_claims: list[str] = Field(
        min_length=2, description="The conflicting claim IDs or proposals the human must choose between."
    )
    resolution_schema: dict[str, Any] = Field(
        description="The strict JSON Schema for the tie-breaking response (usually an enum of the deadlocked_claims)."
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The action to take if the oracle is unresponsive."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "deadlocked_claims", sorted(self.deadlocked_claims))
        return self


class AdjudicationVerdict(CoreasonBaseModel):
    """
    Verdict resulting from grading an LLM behavior or output against a rubric.
    """

    rubric_id: str = Field(description="The ID of the rubric used for adjudication.")
    target_node_id: NodeID = Field(description="The ID of the node that was evaluated.")
    score: int = Field(ge=0, le=100, description="The final score assigned based on the rubric.")
    passed: bool = Field(description="Indicates whether the evaluation passed the threshold.")
    reasoning: str = Field(description="Explanation or reasoning for the verdict and score.")


class AdversarialSimulationProfile(CoreasonBaseModel):
    """
    A deterministic red-team configuration defining a structural attack vector
    to continuously validate semantic firewalls and execution bounds.
    """

    simulation_id: str = Field(description="The unique identifier for this red-team experiment.")
    target_node_id: str = Field(description="The exact NodeID the 'Judas Node' will attempt to compromise.")
    attack_vector: Literal["prompt_extraction", "data_exfiltration", "semantic_hijacking", "tool_poisoning"] = Field(
        description="The mathematically predictable category of structural sabotage being simulated."
    )
    synthetic_payload: dict[str, Any] | str = Field(
        description="The raw poisoned text or malicious JSON-RPC schema injected into the target's context window."
    )
    expected_firewall_trip: str | None = Field(
        default=None,
        description="The exact rule_id of the InformationFlowPolicy or Governance bound expected to block this attack. Used for automated test assertions.",  # noqa: E501
    )


class AgentBid(CoreasonBaseModel):
    agent_id: str = Field(description="The NodeID of the bidder.")
    estimated_cost_magnitude: int = Field(description="The node's calculated cost to fulfill the task.")
    estimated_latency_ms: int = Field(ge=0, description="The node's estimated time to completion.")
    estimated_carbon_gco2eq: float = Field(
        ge=0.0,
        description="The agent's mathematical projection of the environmental cost to execute this inference task.",
    )
    confidence_score: float = Field(ge=0.0, le=1.0, description="The node's epistemic certainty of success.")


class AmbientSignal(CoreasonBaseModel):
    """
    Lightweight UX signal for UI rendering of progress.
    """

    status_message: str = Field(description="A human-readable status message for the current task.")
    progress: float | None = Field(
        default=None, description="The progress ratio from 0.0 to 1.0, or None if indeterminate."
    )


class AnalogicalMappingTask(CoreasonBaseModel):
    task_id: str = Field(min_length=1, description="Unique identifier for this lateral thinking task.")
    source_domain: str = Field(
        description="The unrelated abstract concept space (e.g., 'thermodynamics', 'mycelial networks')."
    )
    target_domain: str = Field(description="The actual problem space currently being solved.")
    required_isomorphisms: int = Field(
        ge=1,
        description="The exact number of structural/logical mappings the agent must successfully bridge between the two domains.",  # noqa: E501
    )
    divergence_temperature_override: float = Field(
        ge=0.0, description="The specific high-temperature sampling override required to force this creative leap."
    )


class AnchoringPolicy(CoreasonBaseModel):
    """
    The mathematical center of gravity preventing epistemic drift and sycophancy in the swarm.
    """

    anchor_prompt_hash: str = Field(
        pattern="^[a-f0-9]{64}$", description="The undeniable SHA-256 hash of the core objective."
    )
    max_semantic_drift: float = Field(
        ge=0.0,
        le=1.0,
        description="The maximum allowed cosine deviation from the anchor before the orchestrator forces a state rollback.",  # noqa: E501
    )


type AttackVector = Literal["rebuttal", "undercutter", "underminer"]

type AttestationMechanism = Literal["fido2_webauthn", "zk_snark_groth16", "pqc_ml_dsa"]


class AuctionPolicy(CoreasonBaseModel):
    auction_type: AuctionType = Field(description="The market mechanism governing the auction.")
    tie_breaker: TieBreaker = Field(description="The deterministic rule for resolving tied bids.")
    max_bidding_window_ms: int = Field(
        description="The absolute timeout in milliseconds for nodes to submit proposals."
    )


class BackpressurePolicy(CoreasonBaseModel):
    """
    Declarative backpressure constraints.
    """

    max_queue_depth: int = Field(
        description="The maximum number of unprocessed messages/observations allowed between connected nodes before yielding."  # noqa: E501
    )
    token_budget_per_branch: int | None = Field(
        default=None, description="The maximum token cost allowed per execution branch before rate-limiting."
    )
    max_tokens_per_minute: int | None = Field(
        default=None,
        gt=0,
        description="The maximum kinetic velocity of token consumption allowed before the circuit breaker trips.",
    )
    max_requests_per_minute: int | None = Field(
        default=None, gt=0, description="The maximum kinetic velocity of API requests allowed."
    )
    max_uninterruptible_span_ms: int | None = Field(
        default=None,
        gt=0,
        description="Systemic heartbeat constraint. A node cannot lock the thread longer than this without yielding to poll for BargeInInterruptEvents.",  # noqa: E501
    )
    max_concurrent_tool_invocations: int | None = Field(
        default=None,
        gt=0,
        description="The mathematical integer ceiling to prevent Sybil-like parallel mutations against the ActionSpaceManifest.",  # noqa: E501
    )


class BaseIntent(CoreasonBaseModel):
    """Base class for presentation intents."""


class BasePanel(CoreasonBaseModel):
    """Base class for Scientific Visualization panels."""

    panel_id: str = Field(description="Unique identifier for the panel.")


class BaseStateEvent(CoreasonBaseModel):
    event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the Merkle-DAG."  # noqa: E501
    )
    timestamp: float = Field(description="Causal Ancestry markers required to resolve decentralized event ordering.")


class SystemFaultEvent(BaseStateEvent):
    type: Literal["system_fault"] = Field(
        default="system_fault", description="Discriminator type for a system fault event."
    )


class BoundedInterventionScope(CoreasonBaseModel):
    """
    Constraints bounding human interaction for interventions.
    """

    allowed_fields: list[str] = Field(description="List of specific fields the human is permitted to mutate.")
    json_schema_whitelist: dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]] = Field(
        description="Strict JSON Schema constraints for the human's input."
    )


class BoundedJSONRPCRequest(CoreasonBaseModel):
    """Base schema enforcing rigorous JSON-RPC 2.0 boundaries to prevent DoS attacks."""

    jsonrpc: Literal["2.0"] = Field(..., description="JSON-RPC version.")
    method: str = Field(..., max_length=1000, description="Method to be invoked.")
    params: dict[str, Any] | None = Field(default=None, description="Payload parameters.")
    id: str | int | None = Field(default=None, description="Unique request identifier.")

    @field_validator("params", mode="before")
    @classmethod
    def validate_params_depth_and_size(cls, v: Any) -> Any:
        """Enforce strict depth and size constraints to prevent RAM exhaustion and DoS attacks."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("params must be a dictionary")

        def _enforce_limits(obj: Any, current_depth: int) -> None:
            if current_depth > 10:
                raise ValueError("JSON payload exceeds maximum depth of 10")
            if isinstance(obj, dict):
                if len(obj) > 100:
                    raise ValueError("Dictionary exceeds maximum of 100 keys")
                for key, val in obj.items():
                    if len(key) > 1000:
                        raise ValueError("Dictionary key exceeds maximum length of 1000")
                    _enforce_limits(val, current_depth + 1)
            elif isinstance(obj, list):
                if len(obj) > 1000:
                    raise ValueError("List exceeds maximum of 1000 elements")
                for item in obj:
                    _enforce_limits(item, current_depth + 1)
            elif isinstance(obj, str):
                if len(obj) > 10000:
                    raise ValueError("String exceeds maximum length of 10000 characters")

        _enforce_limits(v, 0)
        return v


class BrowserDOMState(CoreasonBaseModel):
    type: Literal["browser"] = Field(
        default="browser", description="Discriminator for Causal Actuators representing structural shifts."
    )
    current_url: str = Field(description="Spatial Execution Bounds where the agent interacts.")

    @field_validator("current_url")
    @classmethod
    def _enforce_spatial_safety(cls, url: str) -> str:
        """
        AGENT INSTRUCTION: Mathematically prove the requested coordinate is
        a globally routable topology. Reject all local/private Bogon space
        to prevent epistemic SSRF escape.
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme == "file":
            raise ValueError("SSRF topological violation detected: file:// schema is forbidden")
        hostname = parsed.hostname
        if not hostname:
            return url
        hostname_lower = hostname.lower()
        if hostname_lower in {"localhost", "broadcasthost"} or hostname_lower.endswith(
            (".local", ".internal", ".arpa")
        ):
            raise ValueError(f"SSRF topological violation detected: {hostname}")
        try:
            clean_hostname = hostname.strip("[]")
            ip = ipaddress.ip_address(clean_hostname)
        except ValueError:
            return url
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError(f"SSRF mathematical bound violation detected: {ip}")
        return url

    viewport_size: tuple[int, int] = Field(description="Capability Perimeters detailing bounding coordinates.")
    dom_hash: str = Field(description="The SHA-256 hash acting as the structural manifestation vector.")
    accessibility_tree_hash: str = Field(
        description="The SHA-256 hash of the accessibility tree defining Exogenous Perturbations to the state space."
    )
    screenshot_cid: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the snapshot representation.",  # noqa: E501
    )


class BypassReceipt(CoreasonBaseModel):
    """The Merkle Null-Op preserving the topological chain of custody when an extraction node is intentionally
    skipped."""

    artifact_event_id: str = Field(
        min_length=1, description="The exact genesis CID of the document, ensuring continuity."
    )
    bypassed_node_id: NodeID = Field(
        description="The exact extraction step in the DAG that was mathematically starved of compute."
    )
    justification: Literal["modality_mismatch", "budget_exhaustion", "sla_timeout"] = Field(
        description="The deterministic reason the orchestrator severed this execution branch."
    )
    cryptographic_null_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 null-hash representing the skipped state to satisfy the Epistemic Ledger.",
    )


class CausalAttribution(CoreasonBaseModel):
    source_event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the source event in the Merkle-DAG."  # noqa: E501
    )
    influence_weight: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical attention/importance weight (0.0 to 1.0) assigned to this source by the agent.",
    )


class CausalDirectedEdge(CoreasonBaseModel):
    source_variable: str = Field(min_length=1, description="The independent variable $X$.")
    target_variable: str = Field(min_length=1, description="The dependent variable $Y$.")
    edge_type: Literal["direct_cause", "confounder", "collider", "mediator"] = Field(
        description="The specific Pearlian topological relationship between the two variables."
    )


type ChartAxisScale = Literal["linear", "log", "categorical", "datetime"]


class AffineTransformMatrix(CoreasonBaseModel):
    pixel_min: float = Field(description="The absolute minimal visual coordinate on this axis.")
    pixel_max: float = Field(description="The absolute maximal visual coordinate on this axis.")
    domain_min: float = Field(description="The semantic/data value corresponding to pixel_min.")
    domain_max: float = Field(description="The semantic/data value corresponding to pixel_max.")
    scale_type: ChartAxisScale = Field(description="The mathematical progression between min and max.")


class CircuitBreakerEvent(CoreasonBaseModel):
    """
    Indicates that a circuit breaker has been tripped for a target node.
    """

    type: Literal["circuit_breaker_event"] = Field(
        default="circuit_breaker_event", description="The type of the resilience payload."
    )
    target_node_id: NodeID = Field(description="The ID of the node for which the circuit breaker was tripped.")
    error_signature: str = Field(description="Signature or summary of the error causing the trip.")


class ConstitutionalAmendmentProposal(CoreasonBaseModel):
    """
    Proposed amendment generated in response to normative drift detection.
    """

    type: Literal["constitutional_amendment"] = Field(
        default="constitutional_amendment", description="The strict discriminator for this intervention payload."
    )
    drift_event_id: str = Field(
        description="The CID of the NormativeDriftEvent that justified triggering this proposal."
    )
    proposed_patch: dict[str, Any] = Field(
        description="A strict, structurally bounded JSON Patch (RFC 6902) proposed by the AI to mutate the GovernancePolicy."  # noqa: E501
    )
    justification: str = Field(
        description="The AI's natural language structural/logical argument for why this patch resolves the contradiction without violating the root AnchoringPolicy."  # noqa: E501
    )


class ContinuousMutationPolicy(CoreasonBaseModel):
    mutation_paradigm: Literal["append_only", "merge_on_read"] = Field(
        description="Forces non-destructive graph mutations."
    )
    max_uncommitted_rows: int = Field(gt=0, description="Backpressure threshold before forcing a commit.")
    micro_batch_interval_ms: int = Field(gt=0, description="Temporal bound for flushing the stream.")

    @model_validator(mode="after")
    def enforce_append_only_memory_bound(self) -> Self:
        """Mathematically prevent Out-Of-Memory (OOM) crashes by strictly bounding the buffer."""
        if self.mutation_paradigm == "append_only" and self.max_uncommitted_rows > 10000:
            raise ValueError("max_uncommitted_rows must be <= 10000 for append_only paradigm to prevent OOM crashes.")
        return self


class CounterfactualRegretEvent(BaseStateEvent):
    """A cryptographic record of an agent simulating an alternative timeline to calculate epistemic regret
    and update its policy."""

    type: Literal["counterfactual_regret"] = Field(
        default="counterfactual_regret", description="Discriminator type for a counterfactual regret event."
    )
    historical_event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the specific historical state node where the agent mathematically diverged to simulate an alternative path."  # noqa: E501
    )
    counterfactual_intervention: str = Field(
        description="The specific alternative action or do-calculus intervention applied in the simulation."
    )
    expected_utility_actual: float = Field(
        description="The calculated utility of the trajectory that was actually executed."
    )
    expected_utility_simulated: float = Field(
        description="The calculated utility of the simulated counterfactual trajectory."
    )
    epistemic_regret: float = Field(
        description="The mathematical variance (simulated - actual) representing the opportunity cost of the historical decision."  # noqa: E501
    )
    policy_update_gradients: dict[str, float] = Field(
        default_factory=dict,
        description="The stateless routing gradient adjustments derived from the calculated regret, used to self-correct future routing.",  # noqa: E501
    )


class CrossSwarmHandshake(CoreasonBaseModel):
    handshake_id: str = Field(description="Unique identifier for this B2B negotiation.")
    initiating_tenant_id: str = Field(description="The enterprise DID requesting the connection.")
    receiving_tenant_id: str = Field(description="The enterprise DID receiving the connection.")
    offered_sla: BilateralSLA = Field(description="The initial structural/data boundary proposed.")
    status: Literal["proposed", "negotiating", "aligned", "rejected"] = Field(
        default="proposed", description="The current status of the handshake."
    )


class CrossoverStrategy(CoreasonBaseModel):
    """The mathematical rules for combining elite agents."""

    strategy_type: CrossoverType = Field(description="The heuristic method for blending successful parent agents.")
    blending_factor: float = Field(
        ge=0.0, le=1.0, description="The proportional mix ratio when merging vector properties."
    )
    verifiable_entropy: VerifiableEntropy | None = Field(
        default=None, description="The cryptographic envelope proving the fairness of the applied crossover logic."
    )


class CrystallizationPolicy(CoreasonBaseModel):
    min_observations_required: int = Field(
        ge=10, description="The minimum number of episodic logs needed to statistically prove a crystallized rule."
    )
    aleatoric_entropy_threshold: float = Field(
        le=0.1,
        description="The entropy variance must fall below this mathematical threshold to prove absolute certainty before compression is authorized.",  # noqa: E501
    )
    target_memory_tier: Literal["semantic", "working"] = Field(
        description="The destination tier where the compressed rule will be stored."
    )


class CustodyReceipt(CoreasonBaseModel):
    """
    Cryptographic state of an agent to ensure full traceability and provenance.
    """

    model_config = ConfigDict(frozen=True)
    record_id: str = Field(max_length=255, description="Unique identifier for this chain-of-custody entry.")
    source_node_id: str = Field(max_length=255, description="The execution node that emitted the original data.")
    applied_policy_id: str = Field(
        max_length=255, description="The ID of the InformationFlowPolicy successfully applied."
    )
    pre_redaction_hash: str | None = Field(
        default=None,
        max_length=255,
        description="Optional SHA-256 hash of the raw toxic data for isolated audit vaults.",
    )
    post_redaction_hash: str = Field(
        max_length=255, description="The definitive SHA-256 hash of the sanitized, mathematically clean payload."
    )
    redaction_timestamp_unix_nano: int = Field(description="The precise temporal point the redaction was completed.")


class DefeasibleAttack(CoreasonBaseModel):
    attack_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this directed attack edge."  # noqa: E501
    )
    source_claim_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the claim mounting the attack."  # noqa: E501
    )
    target_claim_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the claim being attacked."  # noqa: E501
    )
    attack_vector: AttackVector = Field(description="Geometric matrices of undercutting defeaters.")


class DimensionalProjectionContract(CoreasonBaseModel):
    source_model_name: str = Field(description="The native embedding model of the origin agent.")
    target_model_name: str = Field(description="The native embedding model of the destination agent.")
    projection_matrix_hash: str = Field(
        description="The SHA-256 hash of the exact mathematical matrix used to compress or translate the latent dimensions."  # noqa: E501
    )
    isometry_preservation_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Mathematical proof (e.g., Earth Mover's Distance preservation) of how accurately relative semantic distances were maintained during projection.",  # noqa: E501
    )


type DistributionType = Literal["gaussian", "uniform", "beta"]


class DistributionProfile(CoreasonBaseModel):
    """Profile defining a probability density function."""

    distribution_type: DistributionType = Field(
        description="The mathematical shape of the probability density function."
    )
    mean: float | None = Field(default=None, description="The expected value (mu) of the distribution.")
    variance: float | None = Field(default=None, description="The mathematical variance (sigma squared).")
    confidence_interval_95: tuple[float, float] | None = Field(default=None, description="The 95% probability bounds.")

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> Any:
        if self.confidence_interval_95 is not None and self.confidence_interval_95[0] >= self.confidence_interval_95[1]:
            raise ValueError("confidence_interval_95 must have interval[0] < interval[1]")
        return self


class DiversityConstraint(CoreasonBaseModel):
    """
    Constraints enforcing cognitive heterogeneity.
    """

    min_adversaries: int = Field(
        description="The minimum number of adversarial or 'Devil's Advocate' roles required to prevent groupthink."
    )
    model_variance_required: bool = Field(
        description="If True, forces the orchestrator to route sub-agents to different foundational models."
    )
    temperature_variance: float | None = Field(
        default=None, description="Required statistical variance in temperature settings across the council."
    )


class DocumentLayoutBlock(CoreasonBaseModel):
    block_id: str = Field(min_length=1, description="Unique structural identifier for this geometric region.")
    block_type: Literal["header", "paragraph", "figure", "table", "footnote", "caption", "equation"] = Field(
        description="The taxonomic classification of the layout region."
    )
    anchor: MultimodalTokenAnchor = Field(description="The strict visual and token coordinate bindings for this block.")


class DocumentLayoutAnalysis(CoreasonBaseModel):
    blocks: dict[str, DocumentLayoutBlock] = Field(
        description="Dictionary mapping block_ids to their strict spatial definitions."
    )
    reading_order_edges: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Directed edges defining the topological sort (chronological flow) of the document.",
    )
    # Note: reading_order_edges is a structurally ordered sequence (Topological Sort) and MUST NOT be sorted.

    @model_validator(mode="after")
    def sort_document_layout_arrays(self) -> Self:
        object.__setattr__(self, "reading_order_edges", sorted(self.reading_order_edges))
        return self

    @model_validator(mode="after")
    def verify_dag_and_integrity(self) -> Self:
        adj: dict[str, list[str]] = {node_id: [] for node_id in self.blocks}
        for source, target in self.reading_order_edges:
            if source not in self.blocks:
                raise ValueError(f"Source block '{source}' does not exist.")
            if target not in self.blocks:
                raise ValueError(f"Target block '{target}' does not exist.")
            adj[source].append(target)
        visited: set[str] = set()
        recursion_stack: set[str] = set()
        for start_node in self.blocks:
            if start_node in visited:
                continue
            stack = [(start_node, iter(adj[start_node]))]
            visited.add(start_node)
            recursion_stack.add(start_node)
            while stack:
                curr, neighbors = stack[-1]
                try:
                    neighbor = next(neighbors)
                    if neighbor not in visited:
                        visited.add(neighbor)
                        recursion_stack.add(neighbor)
                        stack.append((neighbor, iter(adj[neighbor])))
                    elif neighbor in recursion_stack:
                        raise ValueError("Reading order contains a cyclical contradiction.")
                except StopIteration:
                    recursion_stack.remove(curr)
                    stack.pop()
        return self


class DraftingIntent(CoreasonBaseModel):
    type: Literal["drafting"] = Field(
        default="drafting", description="Discriminator for requesting specific missing context from a human."
    )
    context_prompt: str = Field(description="The prompt explaining what information the swarm is missing.")
    resolution_schema: dict[str, Any] = Field(
        description="The strict JSON Schema the human's input must satisfy before the graph can resume."
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The action to take if the human fails to provide the draft."
    )


class DynamicConvergenceSLA(CoreasonBaseModel):
    """Service Level Agreement defining the mathematical conditions for early termination of a reasoning search."""

    convergence_delta_epsilon: float = Field(
        ge=0.0,
        description="The minimal required PRM score improvement across the lookback window to justify continued compute.",  # noqa: E501
    )
    lookback_window_steps: int = Field(
        gt=0, description="The N-step temporal window over which the PRM gradient is calculated."
    )
    minimum_reasoning_steps: int = Field(
        gt=0,
        description="The mandatory 'burn-in' period. The orchestrator cannot terminate the search before this structural depth is reached, preventing premature collapse.",  # noqa: E501
    )


class EmbodiedSensoryVector(CoreasonBaseModel):
    sensory_modality: Literal["video", "audio", "spatial_telemetry"] = Field(
        description="Multimodal Sensor Fusion and Spatial-Temporal Bindings representing Proprioceptive State and Exteroceptive Vectors."  # noqa: E501
    )
    bayesian_surprise_score: float = Field(
        ge=0.0,
        description="The calculated KL divergence between the prior belief and the incoming structural evidence.",
    )
    temporal_duration_ms: int = Field(
        gt=0, le=86400000, description="The exact length of the timeline encapsulated by this observation."
    )
    salience_threshold_breached: bool = Field(
        default=True, description="Continuous-to-Discrete Crystallization threshold being crossed."
    )


class BargeInInterruptEvent(BaseStateEvent):
    """A cryptographic receipt of a continuous multimodal sequence being prematurely severed by an external stimulus."""

    type: Literal["barge_in"] = Field(
        default="barge_in", description="Discriminator type for a barge-in interruption event."
    )
    target_event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the active node generation cycle that was killed in the Merkle-DAG."  # noqa: E501
    )
    sensory_trigger: EmbodiedSensoryVector | None = Field(
        default=None,
        description="The continuous multimodal trigger (e.g., audio spike, user saying 'stop') that justified the interruption.",  # noqa: E501
    )
    retained_partial_payload: dict[str, Any] | str | None = Field(
        default=None,
        description="The 'stutter' state: the incomplete fragment of thought or text appended before the kill signal.",
    )
    epistemic_disposition: Literal["discard", "retain_as_context", "mark_as_falsified"] = Field(
        description="Explicit instruction to the orchestrator on how to patch the shared memory blackboard with the partial payload."  # noqa: E501
    )


type EncodingChannel = Literal["x", "y", "color", "size", "opacity", "shape", "text"]


class EnsembleTopologySpec(CoreasonBaseModel):
    """
    AGENT INSTRUCTION: Declarative mapping of concurrent topology branches for test-time superposition.
    Must map to strict W3C DIDs (NodeIDs) and provide an explicit wave-collapse opcode.
    """

    concurrent_branch_ids: list[NodeID] = Field(
        ..., min_length=2, description="A list of strict W3C DIDs (NodeIDs) representing concurrent topology branches."
    )
    fusion_function: Literal["weighted_consensus", "highest_confidence", "brier_score_collapse"] = Field(
        ..., description="The explicit wave-collapse opcode used for resolving concurrent branches."
    )


class EpistemicCompressionSLA(CoreasonBaseModel):
    strict_probability_retention: bool = Field(
        default=True, description="If True, forces the resulting SemanticNode to populate its uncertainty_profile."
    )
    max_allowed_entropy_loss: float = Field(
        ge=0.0,
        le=1.0,
        description="The maximum allowed statistical flattening of the source data. Bounded between [0.0, 1.0].",
    )
    required_grounding_density: Literal["sparse", "dense", "exhaustive"] = Field(
        description="Dictates the required granularity of the MultimodalTokenAnchor (e.g., must the model map every single entity, or just the global claim?)."  # noqa: E501
    )


class EpistemicPromotionEvent(BaseStateEvent):
    type: Literal["epistemic_promotion"] = Field(
        default="epistemic_promotion", description="Discriminator type for an epistemic promotion event."
    )
    source_episodic_event_ids: list[str] = Field(
        description="A list of CIDs (Content Identifiers) representing the raw logs being compressed and archived."
    )
    crystallized_semantic_node_id: str = Field(
        description="The resulting permanent W3C DID / CID of the newly minted knowledge node."
    )
    compression_ratio: float = Field(
        description="A mathematical proof of the token savings achieved (e.g., old_token_count / new_token_count)."
    )


class EpistemicScanner(CoreasonBaseModel):
    """
    Policy for epistemic scanning and gap detection.
    """

    active: bool = Field(description="Whether the epistemic scanner is active.")
    dissonance_threshold: float = Field(
        ge=0.0, le=1.0, description="The threshold for cognitive dissonance before triggering an action."
    )
    action_on_gap: Literal["fail", "probe", "clarify"] = Field(
        description="The action to take when an epistemic gap is detected."
    )


class EpistemicTransmutationTask(CoreasonBaseModel):
    task_id: str = Field(
        min_length=1, description="Unique identifier for this specific multimodal extraction intervention."
    )
    artifact_event_id: str = Field(description="The CID of the MultimodalArtifact being processed.")
    target_modalities: list[
        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]
    ] = Field(min_length=1, description="The specific SOTA modality resolutions required for this extraction pass.")
    compression_sla: EpistemicCompressionSLA = Field(
        description="The strict mathematical boundary defining the maximum allowed informational entropy loss."
    )
    execution_cost_budget_magnitude: int | None = Field(
        default=None,
        ge=0,
        description="Optional maximum economic expenditure authorized to run this VLM transmutation.",
    )

    @model_validator(mode="after")
    def validate_grounding_density_for_visuals(self) -> Self:
        if (
            "tabular_grid" in self.target_modalities or "raster_image" in self.target_modalities
        ) and self.compression_sla.required_grounding_density == "sparse":
            raise ValueError(
                "Epistemic safety violation: Visual or tabular modalities require strict spatial tracking. 'required_grounding_density' cannot be 'sparse'."  # noqa: E501
            )
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "target_modalities", sorted(self.target_modalities))
        return self


class EscalationContract(CoreasonBaseModel):
    uncertainty_escalation_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The exact Epistemic Uncertainty score that triggers the opening of the Latent Scratchpad.",
    )
    max_latent_tokens_budget: int = Field(
        gt=0,
        description="The maximum number of hidden tokens the orchestrator is authorized to buy for the internal monologue.",  # noqa: E501
    )
    max_test_time_compute_ms: int = Field(
        gt=0, description="The physical time limit allowed for the scratchpad search before forcing a timeout."
    )


class EscalationIntent(CoreasonBaseModel):
    type: Literal["escalation"] = Field(
        default="escalation", description="Discriminator for security or economic boundary overrides."
    )
    tripped_rule_id: str = Field(
        description="The ID of the Data Loss Prevention (DLP) or Governance rule that blocked execution."
    )
    resolution_schema: dict[str, Any] = Field(
        description="The strict JSON Schema requiring an explicit cryptographic sign-off or justification string to bypass the breaker."  # noqa: E501
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The default action is usually terminate or rollback for security escalations."
    )


class EscrowPolicy(CoreasonBaseModel):
    escrow_locked_magnitude: int = Field(
        ge=0, description="The strictly typed integer amount cryptographically locked prior to execution."
    )
    release_condition_metric: str = Field(
        description="A declarative pointer to the SLA or QA rubric required to release the funds."
    )
    refund_target_node_id: str = Field(
        description="The exact NodeID to return funds to if the release condition fails."
    )


class EvictionPolicy(CoreasonBaseModel):
    strategy: Literal["fifo", "salience_decay", "summarize"] = Field(
        description="The mathematical heuristic used to select which semantic memories are retracted or compressed."
    )
    max_retained_tokens: int = Field(
        gt=0, description="The strict geometric upper bound of the Epistemic Quarantine's token capacity."
    )
    protected_event_ids: list[str] = Field(
        default_factory=list,
        description="Explicit list of Content Identifiers (CIDs) the orchestrator is mathematically forbidden from retracting.",  # noqa: E501
    )


class EvidentiaryWarrant(CoreasonBaseModel):
    source_event_id: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for a specific observation in the EpistemicLedger.",  # noqa: E501
    )
    source_semantic_node_id: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for a specific concept in the Semantic Knowledge Graph.",  # noqa: E501
    )
    justification: str = Field(description="The logical premise explaining why this evidence supports the claim.")


class ArgumentClaim(CoreasonBaseModel):
    claim_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this specific logical proposition."  # noqa: E501
    )
    proponent_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the agent or system that advanced this claim."  # noqa: E501
    )
    text_chunk: str = Field(max_length=50000, description="The natural language representation of the proposition.")
    warrants: list[EvidentiaryWarrant] = Field(
        default_factory=list, description="The foundational premises supporting this claim."
    )

    @model_validator(mode="after")
    def sort_argument_claim_arrays(self) -> Self:
        object.__setattr__(self, "warrants", sorted(self.warrants, key=lambda x: x.justification))
        return self


class ArgumentGraph(CoreasonBaseModel):
    """A Truth Maintenance System (TMS) calculating dialectical justification for non-monotonic belief retraction."""

    claims: dict[str, ArgumentClaim] = Field(
        max_length=10000, description="Components of an Abstract Argumentation Framework."
    )
    attacks: dict[str, DefeasibleAttack] = Field(
        default_factory=dict, max_length=10000, description="Geometric matrices of undercutting defeaters."
    )


class ExecutionNode(CoreasonBaseModel):
    """
    Cryptographic state of an execution node in a Merkle DAG trace.
    """

    model_config = ConfigDict(frozen=True)
    request_id: str = Field(description="The unique ID for this specific execution.")
    parent_request_id: str | None = Field(default=None, description="The ID of the parent request.")
    root_request_id: str | None = Field(default=None, description="The ID of the trace root.")
    inputs: Any = Field(description="The inputs provided to the execution node.")
    outputs: Any = Field(description="The outputs generated by the execution node.")
    parent_hashes: list[str] = Field(
        default_factory=list, description="A list of cryptographic hashes of parent execution nodes."
    )
    node_hash: str | None = Field(default=None, description="The cryptographic SHA-256 hash of this node.")

    @model_validator(mode="after")
    def validate_lineage(self) -> Self:
        if self.parent_request_id is not None and self.root_request_id is None:
            raise ValueError("Orphaned Lineage: parent_request_id is set but root_request_id is None")
        return self

    def generate_node_hash(self) -> str:
        """
        Generate a strictly deterministic SHA-256 hash for the node via RFC 8785 canonicalization.
        Ensures identical hashes across varying architectures and thread-states (NoGIL).
        """
        payload = {
            "request_id": self.request_id,
            "parent_request_id": self.parent_request_id,
            "root_request_id": self.root_request_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "parent_hashes": self.parent_hashes,
        }

        def _canonicalize(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _canonicalize(v) for k, v in sorted(obj.items()) if v is not None}
            if isinstance(obj, list):
                return [_canonicalize(v) for v in obj]
            if isinstance(obj, tuple):
                return tuple([_canonicalize(v) for v in obj])
            if isinstance(obj, set):
                return sorted(
                    [_canonicalize(v) for v in obj if v is not None], key=lambda x: json.dumps(x, sort_keys=True)
                )
            return obj

        canonical_payload = _canonicalize(payload)
        json_bytes = json.dumps(canonical_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        return hashlib.sha256(json_bytes).hexdigest()

    @model_validator(mode="after")
    def populate_hash(self) -> Self:
        """Automatically populate node_hash if not explicitly provided."""
        if not self.node_hash:
            object.__setattr__(self, "node_hash", self.generate_node_hash())
        return self


class FYIIntent(BaseIntent):
    """Intent indicating the presentation is informational only."""

    type: Literal["fyi"] = Field(default="fyi", description="Discriminator for an FYI intent.")


class FallbackSLA(CoreasonBaseModel):
    """
    SLA defining bounds on human intervention delays.
    """

    timeout_seconds: int = Field(gt=0, description="The maximum allowed delay for a human intervention.")
    timeout_action: Literal["fail_safe", "proceed_with_defaults", "escalate"] = Field(
        description="The action to take when the timeout expires."
    )
    escalation_target_node_id: NodeID | None = Field(
        default=None, description="The specific NodeID to route the execution to if the escalate action is triggered."
    )


class FallbackTrigger(CoreasonBaseModel):
    """
    Indicates that fallback procedures should be triggered for a target node.
    """

    type: Literal["fallback"] = Field(default="fallback", description="The type of the resilience payload.")
    target_node_id: NodeID = Field(description="The ID of the failing node.")
    fallback_node_id: NodeID = Field(description="The ID of the node to use as a fallback.")


class FalsificationCondition(CoreasonBaseModel):
    condition_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this falsification test to the Merkle-DAG.",  # noqa: E501
    )
    description: str = Field(
        description="Semantic description of what observation would prove the parent hypothesis is false."
    )
    required_tool_name: str | None = Field(
        default=None,
        description="The specific ActionSpaceManifest tool required to test this condition (e.g., 'sql_query_db').",
    )
    falsifying_observation_signature: str = Field(
        description="The expected data schema or regex pattern that, if returned by the tool, kills the hypothesis."
    )


class FaultInjectionProfile(CoreasonBaseModel):
    fault_type: FaultType = Field(description="The specific type of fault to inject.")
    target_node_id: str | None = Field(default=None, description="The specific node to attack, or None for swarm-wide.")
    intensity: float = Field(description="The severity of the fault, represented from 0.0 to 1.0.")


class FederatedCapabilityAttestation(CoreasonBaseModel):
    """
    An immutable cryptographic receipt proving an agent has the structural authority
    to query a remote resource.
    """

    attestation_id: str = Field(min_length=1, description="Cryptographic Lineage Watermark for the attestation.")
    target_topology_id: NodeID = Field(description="The DID of the discovered external data lake/VPC.")
    authorized_session: SecureSubSession = Field(
        description="The isolated memory partition granted to the agent for this connection."
    )
    governing_sla: BilateralSLA = Field(
        description="The structural and physical boundary constraints for querying this target."
    )

    @model_validator(mode="after")
    def enforce_restricted_vault_locks(self) -> Self:
        if self.governing_sla.max_permitted_classification == "restricted" and (
            not self.authorized_session.allowed_vault_keys
        ):
            raise ValueError("RESTRICTED federated connections MUST define allowed_vault_keys in the SecureSubSession.")
        return self


class FederatedStateSnapshot(CoreasonBaseModel):
    topology_id: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the federated topology, if applicable.",  # noqa: E501
    )


class FitnessObjective(CoreasonBaseModel):
    """A specific objective function to optimize within a generation."""

    target_metric: str = Field(
        description="The specific telemetry or execution metric to evaluate (e.g., 'latency', 'accuracy')."
    )
    direction: OptimizationDirection = Field(
        description="Whether the algorithm should maximize or minimize this metric."
    )
    weight: float = Field(
        default=1.0, description="The relative importance of this objective in a multi-objective generation."
    )


class FormalVerificationContract(CoreasonBaseModel):
    """
    Passive schema defining a mathematical proof of safety invariants.
    """

    proof_system: Literal["tla_plus", "lean4", "coq", "z3"] = Field(
        description="The mathematical dialect and theorem prover used to compile the proof."
    )
    invariant_theorem: str = Field(
        description="The exact mathematical assertion or safety invariant being proven (e.g., 'No data classified as CONFIDENTIAL routes externally')."  # noqa: E501
    )
    compiled_proof_hash: str = Field(
        description="The SHA-256 fingerprint of the verified proof object that the Rust/C++ orchestrator must load and check."  # noqa: E501
    )


class GlobalGovernance(CoreasonBaseModel):
    """
    Global governance bounds for a swarm executing a workflow envelope.
    """

    max_budget_magnitude: int = Field(
        description="The absolute maximum economic cost allowed for the entire swarm lifecycle."
    )
    max_global_tokens: int = Field(description="The maximum aggregate token usage allowed across all nodes.")
    max_carbon_budget_gco2eq: float | None = Field(
        default=None,
        ge=0.0,
        description="The absolute physical energy footprint allowed for this execution graph. If exceeded, the orchestrator terminates the swarm.",  # noqa: E501
    )
    global_timeout_seconds: int = Field(
        ge=0, description="The absolute Time-To-Live (TTL) for the execution envelope before graceful termination."
    )
    formal_verification: FormalVerificationContract | None = Field(
        default=None, description="The mathematical proof of structural correctness mandated for this execution graph."
    )


class GenerativeManifoldSLA(CoreasonBaseModel):
    """Mathematical governor for fractal/cyclic graph synthesis."""

    max_topological_depth: int = Field(
        ge=1, description="The absolute physical depth limit for recursive encapsulation."
    )
    max_node_fanout: int = Field(
        ge=1, description="The maximum number of horizontally connected nodes per topology tier."
    )
    max_synthetic_tokens: int = Field(ge=1, description="The economic constraint on the entire generated mock payload.")

    @model_validator(mode="after")
    def enforce_geometric_bounds(self) -> Self:
        """Mathematically guarantees the configuration cannot authorize an OOM explosion."""
        if self.max_topological_depth * self.max_node_fanout > 1000:
            raise ValueError("Geometric explosion risk: max_topological_depth * max_node_fanout must be <= 1000.")
        return self


class GlobalSemanticProfile(CoreasonBaseModel):
    """The immutable receipt of Step 1 ingestion acting as a static structural index of the artifact."""

    artifact_event_id: str = Field(
        min_length=1, description="The exact genesis CID of the document entering the routing tier."
    )
    detected_modalities: list[
        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]
    ] = Field(description="The strictly typed enum list of physical modalities detected in the artifact.")
    token_density: int = Field(
        ge=0, description="The mathematical token density used for downstream compute budget allocation."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "detected_modalities", sorted(self.detected_modalities))
        return self


class DynamicRoutingManifest(CoreasonBaseModel):
    """The Softmax Router Gate dictating the active execution topology and spot compute allocation."""

    manifest_id: str = Field(min_length=1, description="The unique Content Identifier (CID) for this routing plan.")
    artifact_profile: GlobalSemanticProfile = Field(description="The semantic profile governing this route.")
    active_subgraphs: dict[str, list[NodeID]] = Field(
        description="Mapping of specific modalities (e.g., 'tabular_grid') to the explicit lists of worker NodeIDs authorized to execute."  # noqa: E501
    )
    bypassed_steps: list[BypassReceipt] = Field(
        default_factory=list, description="The declarative list of steps the orchestrator is mandated to skip."
    )
    branch_budgets_magnitude: dict[NodeID, int] = Field(
        description="The strict allocation of compute budget bound to specific nodes."
    )

    @model_validator(mode="after")
    def validate_modality_alignment(self) -> Self:
        """Mathematically proves that the router is not hallucinating graphs for non-existent modalities."""
        for modality in self.active_subgraphs:
            if modality not in self.artifact_profile.detected_modalities:
                raise ValueError(
                    f"Epistemic Violation: Cannot route to subgraph '{modality}' because it is missing from detected_modalities."  # noqa: E501
                )
        return self

    @model_validator(mode="after")
    def validate_conservation_of_custody(self) -> Self:
        """Ensures bypass receipts do not contaminate cross-document boundaries."""
        for bypass in self.bypassed_steps:
            if bypass.artifact_event_id != self.artifact_profile.artifact_event_id:
                raise ValueError(
                    "Merkle Violation: BypassReceipt artifact_event_id does not match the root artifact_profile."
                )
        return self


class GovernancePolicy(CoreasonBaseModel):
    """
    Defines a governance policy comprising multiple constitutional rules.
    """

    policy_name: str = Field(description="Name of the governance policy.")
    version: SemanticVersion = Field(description="Semantic version of the governance policy.")
    rules: list[ConstitutionalRule] = Field(description="List of constitutional rules included in this policy.")


class GrammarPanel(CoreasonBaseModel):
    """Panel representing a deterministic, declarative visual grammar."""

    panel_id: str = Field(description="The unique identifier for this UI panel.")
    type: Literal["grammar"] = Field(default="grammar", description="Discriminator for Grammar of Graphics charts.")
    title: str = Field(description="The human-readable title of the chart.")
    data_source_id: str = Field(description="The cryptographic pointer to the dataset in the EpistemicLedger.")
    mark: Literal["point", "line", "area", "bar", "rect", "arc"] = Field(
        description="The geometric shape used to represent the data."
    )
    encodings: list[ChannelEncoding] = Field(description="The mapping of data fields to visual channels.")
    facet: FacetMatrix | None = Field(default=None, description="Optional faceting matrix for small multiples.")

    @model_validator(mode="after")
    def sort_encodings(self) -> Self:
        """Mathematically sorts self.encodings by the string value of channel for deterministic hashing."""
        object.__setattr__(self, "encodings", sorted(self.encodings, key=lambda e: e.channel))
        return self


class GraphFlatteningDirective(CoreasonBaseModel):
    node_projection_mode: Literal["wide_columnar", "struct_array"] = Field(description="How to flatten SemanticNode.")
    edge_projection_mode: Literal["adjacency_list", "map_array"] = Field(description="How to flatten SemanticEdge.")
    preserve_cryptographic_lineage: bool = Field(
        default=True, description="Forces the inclusion of MultimodalTokenAnchor hashes in the flattened row."
    )


class HTTPTransportConfig(CoreasonBaseModel):
    """Configuration for stateless HTTP-based MCP transport."""

    type: Literal["http"] = Field(default="http", description="Type of transport.")
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the stateless connection.")
    headers: dict[str, str] = Field(
        default_factory=dict, description="HTTP headers, strictly bounded for zero-trust credentials."
    )

    @field_validator("headers", mode="after")
    @classmethod
    def _prevent_crlf_injection(cls, v: dict[str, str]) -> dict[str, str]:
        """AGENT INSTRUCTION: Strictly forbid HTTP request smuggling vectors."""
        for key, value in v.items():
            if "\r" in key or "\n" in key or "\r" in value or ("\n" in value):
                raise ValueError("CRLF injection detected in headers")
        return v


class HomomorphicEncryptionProfile(CoreasonBaseModel):
    fhe_scheme: Literal["ckks", "bgv", "bfv", "tfhe"] = Field(
        description="The specific homomorphic encryption dialect used to encode the ciphertext."
    )
    public_key_id: str = Field(
        description="The Content Identifier (CID) of the public evaluation key the orchestrator must utilize to perform privacy-preserving geometric math on ciphertext without epistemic contamination."  # noqa: E501
    )
    ciphertext_blob: str = Field(max_length=5000000, description="The base64-encoded homomorphic ciphertext.")


class HypothesisStake(CoreasonBaseModel):
    """
    The mathematical record of an agent taking a magnitude/compute position on a specific causal hypothesis.
    """

    agent_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        description="The ID of the agent placing the stake."
    )
    target_hypothesis_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        description="The exact HypothesisGenerationEvent the agent is betting on."
    )
    staked_magnitude: int = Field(gt=0, description="The volume of compute budget committed to this position.")
    implied_probability: float = Field(ge=0.0, le=1.0, description="The agent's calculated internal confidence score.")


class InformationalIntent(CoreasonBaseModel):
    type: Literal["informational"] = Field(
        default="informational", description="Discriminator for read-only informational handoffs."
    )
    message: str = Field(description="The context or summary to display to the human operator.")
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The orchestrator's automatic fallback if the human does not acknowledge the intent in time."
    )


type AnyPresentationIntent = Annotated[
    InformationalIntent | DraftingIntent | AdjudicationIntent | EscalationIntent, Field(discriminator="type")
]

type AnyIntent = AnyPresentationIntent


class InputMapping(CoreasonBaseModel):
    """
    Dictates how keys from a parent's shared_state_contract map to a nested topology's state.
    """

    parent_key: str = Field(description="The key in the parent's shared state contract.")
    child_key: str = Field(description="The mapped key in the nested topology's state contract.")


class InsightCard(CoreasonBaseModel):
    """Panel displaying a semantic text summary."""

    panel_id: str = Field(description="The unique identifier for this UI panel.")
    type: Literal["insight_card"] = Field(
        default="insight_card", description="Discriminator for markdown insight cards."
    )
    title: str = Field(description="The human-readable title of the insight.")
    markdown_content: str = Field(description="The markdown formatted text content.")

    @field_validator("markdown_content")
    @classmethod
    def sanitize_markdown(cls, v: str) -> str:
        """Strictly restrict '<' to mathematical contexts to prevent XSS."""
        v_lower = v.lower()
        if re.search("on[a-zA-Z]+\\s*=", v_lower):
            raise ValueError("Forbidden HTML event handler detected.")
        if re.search("<[^=\\s\\d]", v):
            raise ValueError(
                "HTML tags are prohibited. '<' may only be used as a mathematical operator followed by a space, digit, or '='."  # noqa: E501
            )
        return v

    @field_validator("markdown_content", mode="after")
    @classmethod
    def _prevent_malicious_uri_schemes(cls, v: str) -> str:
        """AGENT INSTRUCTION: Statically sever XSS vectors embedded in markdown links."""
        if re.search("\\]\\(\\s*(javascript|vbscript|data):", v, flags=re.IGNORECASE):
            raise ValueError("Malicious executable link scheme detected in markdown content")
        return v


type AnyPanel = Annotated[
    GrammarPanel | InsightCard,
    Field(discriminator="type", description="A discriminated union of presentation UI panels."),
]


class InterventionRequest(CoreasonBaseModel):
    """
    Emitted when an agent needs human approval or further intervention.
    """

    type: Literal["request"] = Field(default="request", description="The type of the intervention payload.")
    intervention_scope: BoundedInterventionScope | None = Field(
        default=None, description="The scope constraints bounding the intervention."
    )
    fallback_sla: FallbackSLA | None = Field(default=None, description="The SLA constraints on the intervention delay.")
    target_node_id: NodeID = Field(description="The ID of the target node.")
    context_summary: str = Field(description="A summary of the context requiring intervention.")
    proposed_action: dict[str, str | int | float | bool | None] = Field(
        description="The action proposed by the agent that requires approval."
    )
    adjudication_deadline: float = Field(description="The deadline for adjudication, represented as a UNIX timestamp.")


class InterventionalCausalTask(CoreasonBaseModel):
    task_id: str = Field(min_length=1, description="Unique identifier for this causal intervention.")
    target_hypothesis_id: str = Field(description="The hypothesis containing the SCM being tested.")
    intervention_variable: str = Field(
        description="The specific node $X$ in the SCM the agent is forcing to a specific state."
    )
    do_operator_state: str = Field(
        description="The exact value or condition forced upon the intervention_variable, isolating it from its historical causes."  # noqa: E501
    )
    expected_causal_information_gain: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical proof of entropy reduction yielded specifically by breaking the confounding back-doors.",  # noqa: E501
    )
    execution_cost_budget_magnitude: int = Field(
        ge=0, description="The maximum economic expenditure authorized to run this specific causal intervention."
    )


class JSONRPCError(CoreasonBaseModel):
    """JSON-RPC 2.0 Error object."""

    code: int = Field(..., description="A Number that indicates the error type that occurred.")
    message: str = Field(..., description="A String providing a short description of the error.")
    data: Any | None = Field(
        default=None,
        description="A Primitive or Structured value that contains additional information about the error.",
    )


class JSONRPCErrorResponse(CoreasonBaseModel):
    """JSON-RPC 2.0 Error Response object."""

    jsonrpc: Literal["2.0"] = Field(..., description="JSON-RPC version.")
    error: JSONRPCError = Field(..., description="The error object.")
    id: str | int | None = Field(default=None, description="The request ID that this error corresponds to.")


class LakehouseMountConfig(CoreasonBaseModel):
    catalog_uri: str = Field(min_length=1, description="The stateless endpoint of the catalog (e.g., Polaris, Nessie).")
    table_format: Literal["iceberg", "delta", "hudi"] = Field(description="Strict boundary for the destination format.")
    schema_evolution_mode: Literal["strict", "additive_only"] = Field(
        description="Dictates if the agent can evolve the schema."
    )


type LifecycleTrigger = Literal[
    "on_start",
    "on_node_transition",
    "before_tool_execution",
    "on_failure",
    "on_consensus_reached",
    "on_max_loops_reached",
]


class InterventionPolicy(CoreasonBaseModel):
    """
    Proactive oversight hook bound to a specific lifecycle event.
    """

    trigger: LifecycleTrigger = Field(
        description="The exact topological lifecycle event that triggers this intervention."
    )
    scope: BoundedInterventionScope | None = Field(
        default=None,
        description="The strictly typed boundaries for what the human/oversight system is allowed to mutate during this pause.",  # noqa: E501
    )
    blocking: bool = Field(
        default=True,
        description="If True, the graph execution halts until a verdict is rendered. If False, it is an async observation.",  # noqa: E501
    )


class BaseNode(CoreasonBaseModel):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(description="A description of the node's function.")
    architectural_intent: str | None = Field(
        default=None, description="The AI's declarative rationale for selecting this node."
    )
    justification: str | None = Field(
        default=None, description="Cryptographic/audit justification for this node's existence in the graph."
    )
    intervention_policies: list[InterventionPolicy] = Field(
        default_factory=list,
        description="A declarative list of proactive oversight hooks bound to this node's lifecycle.",
    )
    domain_extensions: dict[str, Any] | None = Field(
        default=None,
        description="Passive, untyped extension point for vertical domain context. Strictly bounded to prevent JSON-bomb memory leaks.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_agent_attestation_arrays(self) -> Self:
        object.__setattr__(self, "intervention_policies", sorted(self.intervention_policies, key=lambda x: x.trigger))
        return self

    @field_validator("domain_extensions", mode="before")
    @classmethod
    def validate_domain_extensions_depth(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("domain_extensions must be a dictionary")

        def _check_depth(obj: Any, depth: int) -> None:
            if depth > 5:
                raise ValueError("domain_extensions exceeds maximum allowed depth of 5")
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if not isinstance(key, str):
                        raise ValueError("domain_extensions keys must be strings")
                    if len(key) > 255:
                        raise ValueError("domain_extensions key exceeds maximum length of 255 characters")
                    _check_depth(val, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    _check_depth(item, depth + 1)
            elif obj is not None and (not isinstance(obj, (str, int, float, bool))):
                raise ValueError(f"domain_extensions leaf values must be JSON primitives, got {type(obj).__name__}")

        _check_depth(v, 0)
        return v


class HumanNode(BaseNode):
    """
    A node representing a human participant in the workflow.
    """

    type: Literal["human"] = Field(default="human", description="Discriminator for a Human node.")
    required_attestation: AttestationMechanism | None = Field(
        default=None,
        description="AGENT INSTRUCTION: If set, the orchestrator MUST NOT resolve\n        this node without a cryptographically matching WetwareAttestationContract\n        supplied in the InterventionVerdict.",  # noqa: E501
    )


class MemoizedNode(BaseNode):
    """
    A passive structural interlock representing a historically executed graph branch.
    """

    type: Literal["memoized"] = Field(default="memoized", description="Discriminator for a Memoized node.")
    target_topology_hash: TopologyHash = Field(description="The exact SHA-256 fingerprint of the executed topology.")
    expected_output_schema: dict[str, Any] = Field(
        description="The strictly typed JSON Schema expected from the cached payload."
    )


class SystemNode(BaseNode):
    """
    A node representing a deterministic system capability.
    """

    type: Literal["system"] = Field(default="system", description="Discriminator for a System node.")


class LineageWatermark(CoreasonBaseModel):
    watermark_protocol: Literal["merkle_dag", "statistical_token", "homomorphic_mac"] = Field(
        description="The mathematical methodology used to embed the chain of custody."
    )
    hop_signatures: dict[str, str] = Field(
        description="A dictionary mapping intermediate participant NodeIDs to their deterministic execution signatures."
    )
    tamper_evident_root: str = Field(
        description="The overarching cryptographic hash (e.g., Merkle Root) proving the dataset has not been laundered or structurally modified."  # noqa: E501
    )


class MCPCapabilityWhitelist(CoreasonBaseModel):
    """
    A zero-trust boundary defining exactly which JSON-RPC capabilities
    the execution node is authorized to mount from the remote server.
    """

    allowed_tools: list[str] = Field(
        default_factory=list, description="The explicit whitelist of function names the node is allowed to call."
    )
    allowed_resources: list[str] = Field(
        default_factory=list, description="The explicit whitelist of resource URIs the node is allowed to read."
    )
    allowed_prompts: list[str] = Field(
        default_factory=list, description="The explicit whitelist of workflow templates the node is allowed to trigger."
    )
    required_licenses: list[str] = Field(
        default_factory=list,
        description="Explicit list of DUA/RBAC enterprise licenses mathematically required to perceive and mount this capability.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_tools", sorted(self.allowed_tools))
        object.__setattr__(self, "allowed_resources", sorted(self.allowed_resources))
        object.__setattr__(self, "allowed_prompts", sorted(self.allowed_prompts))
        object.__setattr__(self, "required_licenses", sorted(self.required_licenses))
        return self


class MCPServerManifest(CoreasonBaseModel):
    """
    The structural contract for mounting an external Model Context Protocol server.
    """

    server_uri: str = Field(description="The network URI for SSE/HTTP, or the command execution string for stdio.")
    transport_type: Literal["stdio", "sse", "http"] = Field(
        description="The physical transport layer protocol used to stream the JSON-RPC packets."
    )
    binary_hash: str | None = Field(
        default=None,
        description="Optional SHA-256 hash of the local binary to prevent supply-chain execution attacks over stdio.",
    )
    capability_whitelist: MCPCapabilityWhitelist = Field(
        description="The strict capability bounds enforced by the orchestrator prior to connection."
    )


class ActionSpaceManifest(CoreasonBaseModel):
    """
    A curated environment of tools accessible to an agent or node.
    """

    action_space_id: str = Field(description="The unique identifier for this curated environment of tools.")
    native_tools: list[ToolManifest] = Field(
        default_factory=list, description="The list of discrete, natively defined tools available in this space."
    )
    mcp_servers: list[MCPServerManifest] = Field(
        default_factory=list,
        description="The array of verified external Model Context Protocol servers mounted into this action space.",
    )
    ephemeral_partitions: list[EphemeralNamespacePartition] = Field(
        default_factory=list,
        description="Hermetically sealed memory boundaries for dynamically resolved scripts and PEFT adapters.",
    )

    @model_validator(mode="after")
    def verify_unique_tool_namespaces_and_sort(self) -> Self:
        tool_names = {t.tool_name for t in self.native_tools}
        if len(tool_names) < len(self.native_tools):
            raise ValueError("Tool names within an ActionSpaceManifest must be strictly unique.")

        object.__setattr__(self, "native_tools", sorted(self.native_tools, key=lambda x: x.tool_name))
        object.__setattr__(self, "mcp_servers", sorted(self.mcp_servers, key=lambda x: x.server_uri))
        object.__setattr__(
            self, "ephemeral_partitions", sorted(self.ephemeral_partitions, key=lambda x: x.partition_id)
        )
        return self


class OntologicalSurfaceProjection(CoreasonBaseModel):
    """
    A mathematically bounded, declarative subgraph of all ToolManifests and
    MCPServerManifests currently valid for the agent's ProfileID.
    """

    projection_id: str = Field(
        min_length=1, description="A cryptographic Lineage Watermark bounding this specific capability set."
    )
    action_spaces: list[ActionSpaceManifest] = Field(
        default_factory=list, description="The full, machine-readable declaration of accessible tools and MCP servers."
    )
    supported_personas: list[ProfileID] = Field(
        default_factory=list, description="The strict list of foundational model personas available."
    )

    @model_validator(mode="after")
    def verify_unique_action_spaces(self) -> Self:
        space_ids = {space.action_space_id for space in self.action_spaces}
        if len(space_ids) < len(self.action_spaces):
            raise ValueError("Action spaces within a projection must have strictly unique action_space_ids.")
        object.__setattr__(self, "action_spaces", sorted(self.action_spaces, key=lambda x: x.action_space_id))
        object.__setattr__(self, "supported_personas", sorted(self.supported_personas))
        return self


class MCPClientMessage(BoundedJSONRPCRequest):
    """Strict JSON-RPC 2.0 structure for MCP client messages."""

    method: Literal["mcp.ui.emit_intent"] = Field(..., description="Method for intent bubbling.")


class MCPPromptRef(CoreasonBaseModel):
    """A dynamic reference to an MCP-provided prompt template."""

    server_id: str = Field(..., description="The ID of the MCP server providing this prompt.")
    prompt_name: str = Field(..., description="The name of the prompt template.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments to fill the prompt template.")
    fallback_persona: str | None = Field(default=None, description="A fallback persona if the prompt fails to load.")
    prompt_hash: str | None = Field(default=None, description="Cryptographic hash for prompt integrity verification.")


class MCPResourceManifest(CoreasonBaseModel):
    """A collection of Semantic Memory resource URIs provided by a specific MCP server."""

    server_id: str = Field(..., description="The ID of the MCP server providing these resources.")
    uris: list[str] = Field(default_factory=list, description="List of resource URIs available to the agent.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "uris", sorted(self.uris))
        return self


type MCPTransportType = Literal["stdio", "sse", "http"]


class MCPClientBinding(CoreasonBaseModel):
    """
    Binding configuration for a Model Context Protocol (MCP) server.
    """

    server_uri: str = Field(description="The URI or command path to the MCP server.")
    transport_type: MCPTransportType = Field(
        description="The transport protocol used to communicate with the MCP server."
    )

    allowed_mcp_tools: list[str] | None = Field(
        default=None,
        description="An explicit whitelist of tools the agent is allowed to invoke from this server. If None, all discovered tools are allowed.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.allowed_mcp_tools is not None:
            object.__setattr__(self, "allowed_mcp_tools", sorted(self.allowed_mcp_tools))
        return self


class MacroGrid(CoreasonBaseModel):
    """A layout matrix containing a list of panels."""

    layout_matrix: list[list[str]] = Field(description="A matrix defining the layout structure, using panel IDs.")
    panels: list[AnyPanel] = Field(description="A list of panels included in the grid.")

    @model_validator(mode="after")
    def verify_referential_integrity(self) -> Self:
        """Verify that all panel IDs referenced in layout_matrix exist in panels."""
        panel_ids = {panel.panel_id for panel in self.panels}
        for row in self.layout_matrix:
            for panel_id in row:
                if panel_id not in panel_ids:
                    raise ValueError(f"Ghost Panel referenced in layout_matrix: {panel_id}")
        return self


type MarkType = Literal["point", "line", "area", "bar", "rect", "arc"]


class MarketContract(CoreasonBaseModel):
    minimum_collateral: float = Field(ge=0.0, description="The minimum amount of token collateral held in escrow.")
    "\n    MATHEMATICAL BOUNDARY: Must be >= 0.0. Downstream agents must secure this collateral before execution.\n    "
    slashing_penalty: float = Field(ge=0.0, description="The exact token amount slashed for Byzantine faults.")
    "\n    MATHEMATICAL BOUNDARY: Must be >= 0.0 AND mathematically less than or equal to minimum_collateral.\n    "

    @model_validator(mode="after")
    def _enforce_economic_escrow_invariant(self) -> Self:
        """Mathematically prove that a contract cannot penalize more than the escrowed amount."""
        if self.slashing_penalty > self.minimum_collateral:
            raise ValueError("ECONOMIC INVARIANT VIOLATION: slashing_penalty cannot exceed minimum_collateral.")
        return self


class MarketResolutionState(CoreasonBaseModel):
    """
    The resolution state of an algorithmic prediction market.
    """

    market_id: Annotated[str, StringConstraints(min_length=1)] = Field(description="The ID of the prediction market.")
    winning_hypothesis_id: str = Field(description="The hypothesis ID that was verified.")
    falsified_hypothesis_ids: list[str] = Field(description="The hypothesis IDs that were falsified.")
    payout_distribution: dict[str, int] = Field(
        description="The deterministic mapping of agent IDs to their earned compute budget/magnitude based on Brier scoring."  # noqa: E501
    )


class MathematicalNotationExtraction(CoreasonBaseModel):
    math_type: Literal["inline", "display"] = Field(description="The structural context of the equation.")
    syntax: Literal["latex", "mathml"] = Field(description="The strict symbolic compilation language.")
    expression: str = Field(min_length=1, description="The raw, unescaped mathematical syntax string.")
    anchor: MultimodalTokenAnchor = Field(
        description="The strict visual and token coordinate bindings. Cannot be None."
    )

    @model_validator(mode="after")
    def verify_grounding(self) -> Self:
        if self.anchor.token_span_start is None and self.anchor.bounding_box is None:
            raise ValueError("Mathematical extractions must have a definitive visual or token bounding box.")
        return self


class MechanisticAuditContract(CoreasonBaseModel):
    trigger_conditions: list[Literal["on_tool_call", "on_belief_update", "on_quarantine", "on_falsification"]] = Field(
        min_length=1,
        description="The specific architectural events that authorize the orchestrator to halt generation and extract internal activations.",  # noqa: E501
    )
    target_layers: list[int] = Field(
        min_length=1, description="The specific transformer block indices the execution engine must read from."
    )
    max_features_per_layer: int = Field(gt=0, description="The top-k features to extract, preventing memory overflow.")
    require_zk_commitments: bool = Field(
        default=True,
        description="If True, the orchestrator MUST generate cryptographic latent state proofs alongside the activation reads.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "trigger_conditions", sorted(self.trigger_conditions))
        object.__setattr__(self, "target_layers", sorted(self.target_layers))
        return self


class EpistemicProvenance(CoreasonBaseModel):
    extracted_by: NodeID = Field(
        description="The Content Identifier (CID) of the agent node that extracted this memory."
    )
    source_event_id: str = Field(
        description="The exact event Content Identifier (CID) in the EpistemicLedger that generated this fact."
    )
    source_artifact_id: str | None = Field(
        default=None, description="The CID of the Genesis MultimodalArtifact this memory was transmutated from."
    )
    multimodal_anchor: MultimodalTokenAnchor | None = Field(
        default=None, description="The unified VLM spatial and temporal token matrix where this data was extracted."
    )
    lineage_watermark: LineageWatermark | None = Field(
        default=None,
        description="The cryptographic, tamper-evident chain of custody tracing this memory across multiple swarm hops.",  # noqa: E501
    )


class MigrationContract(CoreasonBaseModel):
    contract_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this structural migration mapping."  # noqa: E501
    )
    source_version: str = Field(description="The exact semantic version string of the payload before migration.")
    target_version: str = Field(description="The exact semantic version string of the payload after migration.")
    path_transformations: dict[str, str] = Field(
        default_factory=dict, description="A strict mapping of old RFC 6902 JSON Pointers to new JSON Pointers."
    )
    dropped_paths: list[str] = Field(
        default_factory=list,
        description="Explicit whitelist of JSON Pointers that are safely deprecated and intentionally dropped during migration.",  # noqa: E501
    )


class MultimodalArtifact(CoreasonBaseModel):
    """AGENT INSTRUCTION: The root Genesis Block for an unstructured document entering the Merkle-DAG."""

    artifact_id: str = Field(description="The definitive Content Identifier (CID) bounding the raw file.")
    mime_type: str = Field(description="Strict MIME typing of the source artifact (e.g., 'application/pdf').")
    byte_stream_hash: str = Field(
        pattern="^[a-f0-9]{64}$", description="The undeniable SHA-256 hash of the pre-transmutation byte stream."
    )
    temporal_ingest_timestamp: float = Field(description="The UNIX timestamp anchoring the genesis block.")


class MutationPolicy(CoreasonBaseModel):
    """Constraints governing random heuristic mutations."""

    mutation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="The probability that a given agent parameter will randomly mutate between generations.",
    )
    temperature_shift_variance: float = Field(
        description="The maximum allowed delta for an agent's temperature during mutation."
    )
    verifiable_entropy: VerifiableEntropy | None = Field(
        default=None, description="The cryptographic envelope proving the fairness of the applied mutation rate."
    )


class NDimensionalTensorManifest(CoreasonBaseModel):
    """
    Cryptographic shadow of an N-Dimensional spatial or mathematical array.
    Used for routing multi-dimensional compute without passing raw bytes.
    """

    dtype: TensorDType = Field(..., description="Data type of the tensor elements.")
    shape: tuple[int, ...] = Field(..., description="N-Dimensional shape tuple.")
    memory_footprint_bytes: int = Field(..., description="Exact byte size of the uncompressed tensor.")
    merkle_root: str = Field(..., pattern="^[a-fA-F0-9]{64}$", description="SHA-256 Merkle root of the payload chunks.")
    storage_uri: str = Field(..., description="Strict URI pointer to the physical bytes.")

    @model_validator(mode="after")
    def _enforce_physics_engine(self) -> "NDimensionalTensorManifest":
        """Mathematically prove the topology matches the declared memory footprint."""
        if len(self.shape) < 1:
            raise ValueError("Tensor shape must have at least 1 dimension.")
        for dim in self.shape:
            if dim <= 0:
                raise ValueError(f"Tensor dimensions must be strictly positive integers. Got: {self.shape}")
        bytes_per_element = (
            self.dtype.bytes_per_element
            if isinstance(self.dtype, TensorDType)
            else TensorDType(self.dtype).bytes_per_element
        )
        calculated_bytes = math.prod(self.shape) * bytes_per_element
        if calculated_bytes != self.memory_footprint_bytes:
            raise ValueError(
                f"Topological mismatch: Shape {self.shape} of {self.dtype.value} requires {calculated_bytes} bytes, but manifest declares {self.memory_footprint_bytes} bytes."  # noqa: E501
            )
        return self


class NeuralAuditAttestation(CoreasonBaseModel):
    audit_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the Merkle-DAG.",  # noqa: E501
    )
    layer_activations: dict[int, list[SaeFeatureActivation]] = Field(
        description="A mapping of specific transformer layer indices to their top-k activated SAE features."
    )
    causal_scrubbing_applied: bool = Field(
        default=False,
        description="Cryptographic proof that the orchestrator actively resampled or ablated this circuit to verify its causal responsibility for the output.",  # noqa: E501
    )


class NeuroSymbolicHandoff(CoreasonBaseModel):
    handoff_id: str = Field(min_length=1, description="Unique identifier for this symbolic delegation.")
    solver_protocol: Literal["z3", "lean4", "coq", "tla_plus", "sympy"] = Field(
        description="The target deterministic math/logic engine."
    )
    formal_grammar_payload: str = Field(
        description="The raw code or formal proof syntax generated by the LLM to be evaluated."
    )
    expected_proof_schema: dict[str, Any] = Field(
        description="The strict JSON Schema the deterministic solver must use to return the verified answer to the agent."  # noqa: E501
    )
    timeout_ms: int = Field(
        gt=0, description="The maximum compute time allocated to the symbolic solver before aborting."
    )


class NormativeDriftEvent(BaseStateEvent):
    type: Literal["normative_drift"] = Field(
        default="normative_drift", description="Discriminator type for a normative drift event."
    )
    tripped_rule_id: str = Field(
        description="The Content Identifier (CID) of the specific ConstitutionalRule causing logical friction."
    )
    measured_semantic_drift: float = Field(
        description="The calculated probabilistic delta showing how far the swarm's observed reality is diverging from the static rule."  # noqa: E501
    )
    contradiction_proof_hash: str = Field(
        description="A cryptographic pointer to the internal scratchpad trace (ThoughtBranch) definitively proving the rule is obsolete or causing a loop."  # noqa: E501
    )


class ObservabilityPolicy(CoreasonBaseModel):
    traces_sampled: bool = Field(
        default=True, description="Whether the orchestrator must record telemetry for this topology."
    )
    detailed_events: bool = Field(default=False, description="Whether to include granular intra-tool loop events.")


class OntologicalHandshake(CoreasonBaseModel):
    handshake_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this protocol handshake to the Merkle-DAG.",  # noqa: E501
    )
    participant_node_ids: list[str] = Field(min_length=2, description="The agents establishing semantic alignment.")
    measured_cosine_similarity: float = Field(
        ge=-1.0, le=1.0, description="The calculated geometric alignment of the agents' core definitions."
    )
    alignment_status: Literal["aligned", "projected", "fallback_triggered", "incommensurable"] = Field(
        description="The final verdict of the handshake protocol."
    )
    applied_projection: DimensionalProjectionContract | None = Field(
        default=None,
        description="The projection applied if the agents natively used different embedding dimensionalities.",
    )


class OutputMapping(CoreasonBaseModel):
    """
    Dictates how keys from a nested topology's state map back to a parent's shared_state_contract.
    """

    child_key: str = Field(description="The key in the nested topology's state contract.")
    parent_key: str = Field(description="The mapped key in the parent's shared state contract.")


class CompositeNode(BaseNode):
    """
    A node that encapsulates a nested workflow topology.
    """

    type: Literal["composite"] = Field(default="composite", description="Discriminator for a Composite node.")
    topology: "AnyTopology" = Field(description="The encapsulated subgraph to execute.")
    input_mappings: list[InputMapping] = Field(default_factory=list, description="Explicit state projection inputs.")
    output_mappings: list[OutputMapping] = Field(default_factory=list, description="Explicit state projection outputs.")

    @model_validator(mode="after")
    def sort_composite_arrays(self) -> Self:
        object.__setattr__(self, "input_mappings", sorted(self.input_mappings, key=lambda x: x.parent_key))
        object.__setattr__(self, "output_mappings", sorted(self.output_mappings, key=lambda x: x.child_key))
        return self


class OverrideIntent(CoreasonBaseModel):
    """
    Dictatorial oversight override payload.
    """

    type: Literal["override"] = Field(default="override", description="The type of the intervention payload.")
    authorized_node_id: NodeID = Field(description="The NodeID of the human or agent executing the override.")
    target_node_id: NodeID = Field(description="The NodeID being forcefully overridden.")
    override_action: dict[str, str | int | float | bool | None] = Field(
        description="The exact payload forcefully injected into the state."
    )
    justification: str = Field(
        max_length=2000, description="Cryptographic audit justification for bypassing algorithmic consensus."
    )


class PeftAdapterContract(CoreasonBaseModel):
    """Declarative contract for dynamically mounting a Parameter-Efficient Fine-Tuning (PEFT) adapter."""

    adapter_id: str = Field(description="Unique identifier for the requested LoRA adapter.")
    safetensors_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the cold-storage adapter weights file ensuring supply-chain zero-trust.",
    )
    base_model_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact foundational model this adapter was mathematically trained against.",
    )
    adapter_rank: int = Field(
        gt=0,
        description="The low-rank intrinsic dimension (r) of the update matrices, used by the orchestrator to calculate VRAM cost.",  # noqa: E501
    )
    target_modules: list[str] = Field(
        min_length=1, description="The explicit list of attention head modules to inject (e.g., ['q_proj', 'v_proj'])."
    )
    eviction_ttl_seconds: int | None = Field(
        default=None,
        gt=0,
        description="The time-to-live before the inference engine forcefully evicts this adapter from the LRU cache.",
    )


class PersistenceCommitReceipt(BaseStateEvent):
    type: Literal["persistence_commit"] = Field(
        default="persistence_commit", description="Discriminator type for a persistence commit receipt."
    )
    lakehouse_snapshot_id: str = Field(
        min_length=1, description="The external cryptographic receipt generated by Iceberg/Delta."
    )
    committed_state_diff_id: str = Field(min_length=1, description="The internal StateDiff CID that was flushed.")
    target_table_uri: str = Field(min_length=1, description="The specific table mutated.")


class PredictionMarketState(CoreasonBaseModel):
    """
    The state of the Automated Market Maker (AMM) using Robin Hanson's
    Logarithmic Market Scoring Rule (LMSR) to ensure infinite liquidity.
    """

    market_id: Annotated[str, StringConstraints(min_length=1)] = Field(description="The ID of the prediction market.")
    resolution_oracle_condition_id: str = Field(
        description="The specific FalsificationCondition ID whose execution will trigger the market payout."
    )
    lmsr_b_parameter: str = Field(
        pattern="^\\d+\\.\\d+$",
        description="The stringified decimal representing the liquidity parameter defining the market depth and max loss for the AMM.",  # noqa: E501
    )
    order_book: list[HypothesisStake] = Field(description="The immutable ledger of all stakes placed by the swarm.")
    current_market_probabilities: dict[str, str] = Field(
        description="Mapping of hypothesis IDs to their current LMSR-calculated market price (probability) as stringified decimals."  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_prediction_market_state_arrays(self) -> Self:
        object.__setattr__(self, "order_book", sorted(self.order_book, key=lambda x: x.agent_id))
        return self


class PresentationEnvelope(CoreasonBaseModel):
    """An envelope wrapping a grid presentation and its intent."""

    intent: AnyPresentationIntent = Field(description="The reason an agent is presenting this data to a human.")
    grid: MacroGrid = Field(description="The grid of panels being presented.")


class ProcessRewardContract(CoreasonBaseModel):
    convergence_sla: DynamicConvergenceSLA | None = Field(
        default=None,
        description="The dynamic circuit breaker that halts the search when PRM variance converges, preventing VRAM waste.",  # noqa: E501
    )
    pruning_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="If a ThoughtBranch's prm_score falls below this threshold, the orchestrator MUST halt its generation.",  # noqa: E501
    )
    max_backtracks_allowed: int = Field(
        ge=0,
        description="The absolute limit on how many times the agent can start a new branch before throwing a SystemFaultEvent.",  # noqa: E501
    )
    evaluator_model_name: str | None = Field(
        default=None, description="The specific PRM model used to score the logic (e.g., 'math-prm-v2')."
    )


type QoSClassification = Literal["critical", "high", "interactive", "background_batch"]


class ComputeProvisioningRequest(CoreasonBaseModel):
    """
    A request by a swarm to provision resources based on requirements.
    """

    max_budget: float = Field(description="The maximum cost budget allowable for the provisioned compute.")
    required_capabilities: list[str] = Field(
        description="The minimal functional capabilities required by the requested compute."
    )
    qos_class: QoSClassification = Field(
        default="interactive",
        description="The Quality of Service priority, used by the compute spot market for semantic load shedding.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "required_capabilities", sorted(self.required_capabilities))
        return self


class QuarantineIntent(CoreasonBaseModel):
    """
    Indicates that a target node should be quarantined.
    """

    type: Literal["quarantine_intent"] = Field(
        default="quarantine_intent", description="The type of the resilience payload."
    )
    target_node_id: NodeID = Field(description="The ID of the node to be quarantined.")
    reason: str = Field(description="The reason for the quarantine order.")


type AnyResiliencePayload = Annotated[
    QuarantineIntent | CircuitBreakerEvent | FallbackTrigger, Field(discriminator="type")
]


class SSETransportConfig(CoreasonBaseModel):
    """Configuration for remote SSE-based MCP transport."""

    type: Literal["sse"] = Field(default="sse", description="Type of transport.")
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the SSE connection.")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers, e.g., for authentication.")

    @field_validator("headers", mode="after")
    @classmethod
    def _prevent_crlf_injection(cls, v: dict[str, str]) -> dict[str, str]:
        """AGENT INSTRUCTION: Strictly forbid HTTP request smuggling vectors."""
        for key, value in v.items():
            if "\r" in key or "\n" in key or "\r" in value or ("\n" in value):
                raise ValueError("CRLF injection detected in headers")
        return v


class SalienceProfile(CoreasonBaseModel):
    baseline_importance: float = Field(
        ge=0.0, le=1.0, description="The starting importance score of this memory from 0.0 to 1.0."
    )
    decay_rate: float = Field(ge=0.0, description="The rate at which this memory's relevance decays over time.")


type ScaleType = Literal["linear", "log", "time", "ordinal", "nominal"]


class SelfCorrectionPolicy(CoreasonBaseModel):
    """
    Policy for self-correction and iterative refinement.
    """

    max_loops: int = Field(ge=0, le=50, description="The maximum number of self-correction loops allowed.")
    rollback_on_failure: bool = Field(description="Whether to rollback to the previous state on failure.")


class SemanticFirewallPolicy(CoreasonBaseModel):
    max_input_tokens: int = Field(
        gt=0, description="The absolute physical ceiling of tokens allowed in a single ingress payload."
    )
    forbidden_intents: list[str] = Field(
        default_factory=list,
        description="A strict list of semantic intents (e.g., 'role_override', 'system_prompt_leak') that trigger immediate quarantine.",  # noqa: E501
    )
    action_on_violation: Literal["drop", "quarantine", "redact"] = Field(
        description="The deterministic action the orchestrator must take if a firewall rule is violated."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "forbidden_intents", sorted(self.forbidden_intents))
        return self


class InformationFlowPolicy(CoreasonBaseModel):
    """
    Mathematical Data Loss Prevention (DLP) contract that bounds the graph.
    """

    policy_id: str = Field(description="Unique identifier for this macroscopic flow control policy.")
    active: bool = Field(default=True, description="Whether this policy is currently enforcing data sanitization.")
    rules: list[RedactionRule] = Field(default_factory=list, description="The array of sanitization rules to enforce.")
    semantic_firewall: SemanticFirewallPolicy | None = Field(
        default=None, description="The active cognitive defense perimeter against adversarial control-flow overrides."
    )
    latent_firewalls: list[SaeLatentFirewall] = Field(
        default_factory=list,
        description="The list of tensor-level mechanistic firewalls monitoring the forward pass for adversarial intent.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_rules(self) -> Self:
        """
        Mathematically sorts rules by rule_id to guarantee deterministic hashing.
        """
        object.__setattr__(self, "rules", sorted(self.rules, key=lambda r: r.rule_id))
        object.__setattr__(
            self, "latent_firewalls", sorted(self.latent_firewalls, key=lambda x: x.target_feature_index)
        )
        return self


class SimulationConvergenceSLA(CoreasonBaseModel):
    """
    The statistical limits of the sandbox simulation.
    """

    max_monte_carlo_rollouts: int = Field(
        gt=0, description="The absolute physical limit on how many alternate futures the system is allowed to render."
    )
    variance_tolerance: float = Field(
        ge=0.0,
        le=1.0,
        description="The statistical confidence required to collapse the probability wave early and save GPU VRAM.",
    )


class SimulationEscrow(CoreasonBaseModel):
    locked_magnitude: int = Field(
        gt=0,
        description="The strictly typed boundary requiring locked magnitude to prevent zero-cost griefing of the swarm.",  # noqa: E501
    )


class ExogenousEpistemicEvent(CoreasonBaseModel):
    shock_id: str = Field(min_length=1, description="Cryptographic identifier for the Black Swan event.")
    target_node_hash: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="Regex-bound SHA-256 string targeting a specific Merkle root in the epistemic graph.",
    )
    bayesian_surprise_score: float = Field(
        ge=0.0,
        allow_inf_nan=False,
        description="Strictly bounded mathematical quantification of the epistemic decay or Variational Free Energy.",
    )
    synthetic_payload: dict[str, Any] = Field(
        description="Bounded dictionary representing the injected hallucination or observation."
    )
    escrow: SimulationEscrow = Field(description="The cryptographic Proof-of-Stake funding the shock.")

    @model_validator(mode="after")
    def enforce_economic_escrow(self) -> Self:
        if self.escrow.locked_magnitude <= 0:
            raise ValueError("ExogenousEpistemicEvent requires a strictly positive escrow to execute.")
        return self


class SpanEvent(CoreasonBaseModel):
    name: str = Field(description="The semantic name of the event.")
    timestamp_unix_nano: int = Field(description="The precise temporal execution point.")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Typed metadata bound to the event.")


class ExecutionSpan(CoreasonBaseModel):
    trace_id: str = Field(description="The global identifier for the entire execution causal tree.")
    span_id: str = Field(description="The unique identifier for this specific operation.")
    parent_span_id: str | None = Field(default=None, description="The causal link to the invoking node.")
    name: str = Field(description="The semantic identifier for the operation.")
    kind: SpanKind = Field(default="internal", description="The role of the span.")
    start_time_unix_nano: int = Field(ge=0, description="Temporal start bound.")
    end_time_unix_nano: int | None = Field(default=None, ge=0, description="Temporal end bound, if completed.")
    status: SpanStatusCode = Field(default="unset", description="The execution health flag.")
    events: list[SpanEvent] = Field(
        default_factory=list, max_length=10000, description="Structured log records emitted during the span."
    )
    # Note: events is a structurally ordered sequence (Temporal execution) and MUST NOT be sorted.

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Any:
        if self.end_time_unix_nano is not None and self.end_time_unix_nano < self.start_time_unix_nano:
            raise ValueError("end_time_unix_nano cannot be before start_time_unix_nano")
        return self

    @model_validator(mode="after")
    def sort_events(self) -> Any:
        object.__setattr__(self, "events", sorted(self.events, key=lambda e: e.timestamp_unix_nano))
        return self


class SpatialKinematicAction(CoreasonBaseModel):
    """A mathematical declaration of an OS-level pointer or interaction trajectory."""

    action_type: Literal["click", "double_click", "drag_and_drop", "scroll", "hover", "keystroke"] = Field(
        description="The specific kinematic interaction paradigm."
    )
    target_coordinate: NormalizedCoordinate | None = Field(
        default=None, description="The primary spatial terminus for clicks or hovers."
    )
    trajectory_duration_ms: int | None = Field(
        default=None, gt=0, description="The exact temporal duration of the movement, simulating human kinematics."
    )
    bezier_control_points: list[NormalizedCoordinate] = Field(
        default_factory=list, description="Waypoints for constructing non-linear, bot-evasive movement curves."
    )
    # Note: bezier_control_points is a structurally ordered sequence (Geometry/Time) and MUST NOT be sorted.
    expected_visual_concept: str | None = Field(
        default=None,
        description="The visual anchor (e.g., 'Submit Button'). The orchestrator must verify this semantic concept exists at the target_coordinate before executing the macro, preventing blind clicks.",  # noqa: E501
    )


class StateContract(CoreasonBaseModel):
    """
    A strict Cryptographic State Contract (Typed Blackboard) for multi-agent memory sharing.
    """

    schema_definition: dict[str, Any] = Field(
        description="A strict JSON Schema dictionary defining the required shape of the shared memory blackboard."
    )
    strict_validation: bool = Field(
        default=True,
        description="If True, the orchestrator must reject any state mutation that fails the schema definition.",
    )


class OntologicalAlignmentPolicy(CoreasonBaseModel):
    """
    The pre-flight execution gate forcing agents to mathematically align their latent semantics.
    """

    min_cosine_similarity: float = Field(
        ge=-1.0,
        le=1.0,
        description="The absolute minimum latent vector similarity required to allow swarm communication.",
    )
    require_isometry_proof: bool = Field(
        description="If True, the orchestrator must reject dimensional projections that fall below a safe isometry preservation score."  # noqa: E501
    )
    fallback_state_contract: StateContract | None = Field(
        default=None,
        description="The rigid external JSON schema to force agents to use if their latent vector geometries are hopelessly incommensurable.",  # noqa: E501
    )


class StatisticalChartExtraction(CoreasonBaseModel):
    axes: dict[str, AffineTransformMatrix] = Field(
        description="Named axes (e.g., 'x', 'y') defining the affine transformation boundaries."
    )
    data_series: list[dict[str, float | str]] = Field(
        description="The discrete semantic tuples extracted from the chart markers."
    )

    @model_validator(mode="after")
    def verify_dimensional_isometry(self) -> Self:
        axis_keys = set(self.axes.keys())
        for point in self.data_series:
            point_keys = set(point.keys())
            if not point_keys.issubset(axis_keys) and (not axis_keys.issubset(point_keys)):
                missing = axis_keys - point_keys
                if missing:
                    raise ValueError(f"Data point missing required axis dimensions: {missing}")
        return self


class StdioTransportConfig(CoreasonBaseModel):
    """Configuration for local Stdio-based MCP transport."""

    type: Literal["stdio"] = Field(default="stdio", description="Type of transport.")
    command: str = Field(..., description="The command executable to run (e.g., 'node', 'python').")
    args: list[str] = Field(default_factory=list, description="List of arguments to pass to the command.")
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables required by the transport."
    )


type MCPTransport = StdioTransportConfig | SSETransportConfig | HTTPTransportConfig


class MCPServerConfig(CoreasonBaseModel):
    """Configuration definition for connecting to an MCP Server."""

    server_id: str = Field(..., description="A unique identifier for this server instance.")
    transport: MCPTransport = Field(..., discriminator="type", description="Polymorphic transport configuration.")
    required_capabilities: list[str] = Field(
        default_factory=lambda: ["tools", "resources", "prompts"],
        description="A list of capabilities required from the MCP server.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "required_capabilities", sorted(self.required_capabilities))
        return self


class SteadyStateHypothesis(CoreasonBaseModel):
    expected_max_latency: float = Field(ge=0.0, description="The expected maximum latency under normal conditions.")
    max_loops_allowed: int = Field(description="The maximum allowed loops for the swarm to reach a conclusion.")
    required_tool_usage: list[str] | None = Field(
        default=None, description="A list of required tools that must be utilized."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.required_tool_usage is not None:
            object.__setattr__(self, "required_tool_usage", sorted(self.required_tool_usage))
        return self


class ChaosExperiment(CoreasonBaseModel):
    experiment_id: str = Field(description="The unique identifier for the chaos experiment.")
    hypothesis: SteadyStateHypothesis = Field(description="The baseline steady state hypothesis being tested.")
    faults: list[FaultInjectionProfile] = Field(
        description="The list of fault injection profiles defining the chaotic elements."
    )
    shocks: list[ExogenousEpistemicEvent] = Field(
        default_factory=list,
        description="The declarative list of exogenous Black Swan events injected into the topology.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "faults", sorted(self.faults, key=lambda x: (x.fault_type, x.target_node_id)))
        object.__setattr__(self, "shocks", sorted(self.shocks, key=lambda x: x.shock_id))
        return self


class StructuralCausalModel(CoreasonBaseModel):
    observed_variables: list[str] = Field(description="The nodes in the DAG that the agent can passively measure.")
    latent_variables: list[str] = Field(description="The unobserved confounders the agent suspects exist.")
    causal_edges: list[CausalDirectedEdge] = Field(description="The declared topological mapping of causality.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "observed_variables", sorted(self.observed_variables))
        object.__setattr__(self, "latent_variables", sorted(self.latent_variables))
        object.__setattr__(
            self, "causal_edges", sorted(self.causal_edges, key=lambda x: (x.source_variable, x.target_variable))
        )
        return self


class HypothesisGenerationEvent(BaseStateEvent):
    type: Literal["hypothesis"] = Field(
        default="hypothesis", description="Discriminator for a hypothesis generation event."
    )

    hypothesis_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this abductive leap to the Merkle-DAG.",  # noqa: E501
    )
    premise_text: str = Field(description="The natural language explanation of the abductive theory.")
    bayesian_prior: float = Field(
        ge=0.0, le=1.0, description="The agent's initial probabilistic belief in this hypothesis before testing."
    )
    falsification_conditions: list[FalsificationCondition] = Field(
        min_length=1,
        description="The list of strict conditions that the orchestrator must test to attempt to disprove this premise.",  # noqa: E501
    )
    status: Literal["active", "falsified", "verified"] = Field(
        default="active", description="The current validity state of this hypothesis in the EpistemicLedger."
    )
    causal_model: StructuralCausalModel | None = Field(
        default=None,
        description="The formal DAG representing the agent's structural assumptions about the environment.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "falsification_conditions", sorted(self.falsification_conditions, key=lambda x: x.condition_id)
        )
        return self


class SuspenseEnvelope(CoreasonBaseModel):
    """
    Indicates that the swarm is waiting on a long-running process or human input.
    """


class SyntheticGenerationProfile(CoreasonBaseModel):
    """Authoritative blueprint for external fuzzing and simulation engines."""

    profile_id: str = Field(min_length=1, description="Unique identifier for this simulation profile.")
    manifold_sla: GenerativeManifoldSLA = Field(description="The structural topological gas limit.")
    target_schema_ref: str = Field(min_length=1, description="The string name of the Pydantic class to synthesize.")


class System1Reflex(CoreasonBaseModel):
    """
    Policy for fast, intuitive system 1 thinking.
    """

    confidence_threshold: float = Field(
        ge=0.0, le=1.0, description="The confidence threshold required to execute a reflex action."
    )
    allowed_read_only_tools: list[str] = Field(description="List of read-only tools allowed during a reflex action.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_read_only_tools", sorted(self.allowed_read_only_tools))
        return self


class System2RemediationPrompt(CoreasonBaseModel):
    """
    A passive data envelope that deterministically maps a kinetic execution error
    (e.g., a Pydantic ValidationError) into a structurally rigid System 2 correction directive.
    """

    fault_id: str = Field(
        min_length=1, description="A cryptographic Lineage Watermark (CID) tracking this specific dimensional collapse."
    )

    target_node_id: NodeID = Field(
        description="The strict W3C DID of the agent that authored the invalid state, ensuring the fault is routed back to the exact memory partition."  # noqa: E501
    )
    failing_pointers: list[str] = Field(
        min_length=1,
        description="A strictly typed array of RFC 6902 JSON Pointers isolating the exact topological coordinate of the hallucination.",  # noqa: E501
    )
    remediation_prompt: str = Field(
        min_length=1, description="The deterministic, non-monotonic natural-language constraint the agent must satisfy."
    )

    @model_validator(mode="after")
    def _sort_failing_pointers(self) -> Self:
        """Mathematically sort pointers to guarantee deterministic canonical hashing."""
        object.__setattr__(self, "failing_pointers", sorted(self.failing_pointers))
        return self


class TableCell(CoreasonBaseModel):
    row_index: int = Field(ge=0, description="The zero-indexed absolute matrix row.")
    col_index: int = Field(ge=0, description="The zero-indexed absolute matrix column.")
    row_span: int = Field(default=1, ge=1, description="The vertical height of the cell.")
    col_span: int = Field(default=1, ge=1, description="The horizontal width of the cell.")
    content: str = Field(description="The normalized text value.")
    anchor: MultimodalTokenAnchor = Field(description="The physical location of the cell within the image or document.")


class TabularMatrixExtraction(CoreasonBaseModel):
    cells: list[TableCell] = Field(description="The sparse tensor representing all populated cells.")

    @model_validator(mode="after")
    def sort_tabular_data_arrays(self) -> Self:
        object.__setattr__(self, "cells", sorted(self.cells, key=lambda x: (x.row_index, x.col_index)))
        return self

    @model_validator(mode="after")
    def detect_geometric_collisions(self) -> Self:
        occupied_coordinates: set[tuple[int, int]] = set()
        for cell in self.cells:
            for r in range(cell.row_index, cell.row_index + cell.row_span):
                for c in range(cell.col_index, cell.col_index + cell.col_span):
                    coord = (r, c)
                    if coord in occupied_coordinates:
                        raise ValueError(f"Geometric Collision Detected: Cell overlapping at coordinate {coord}.")
                    occupied_coordinates.add(coord)
        return self


class TamperError(ValueError):
    """Raised when an execution trace has been tampered with or is topologically invalid."""


class TaskAnnouncement(CoreasonBaseModel):
    task_id: str = Field(description="Unique identifier for the required task.")
    required_action_space_id: str | None = Field(
        default=None, description="Optional restriction forcing bidders to possess a specific toolset."
    )
    max_budget_magnitude: int = Field(description="The absolute ceiling price the orchestrator is willing to pay.")


class TaskAward(CoreasonBaseModel):
    task_id: str = Field(description="The identifier of the resolved task.")
    awarded_syndicate: dict[str, int] = Field(
        description="Strict mapping of agent NodeIDs to their exact fractional payout in magnitude."
    )
    cleared_price_magnitude: int = Field(description="The final cryptographic clearing price.")
    escrow: EscrowPolicy | None = Field(default=None, description="The conditional escrow locking the compute budget.")

    @model_validator(mode="after")
    def validate_escrow_bounds(self) -> Self:
        """Ensures locked funds do not exceed the cleared auction price."""
        if self.escrow is not None and self.escrow.escrow_locked_magnitude > self.cleared_price_magnitude:
            raise ValueError("Escrow locked amount cannot exceed the total cleared price.")
        return self

    @model_validator(mode="after")
    def verify_syndicate_allocation(self) -> Self:
        if sum(self.awarded_syndicate.values()) != self.cleared_price_magnitude:
            raise ValueError("Syndicate allocation sum must exactly equal cleared_price_magnitude")
        return self


class AuctionState(CoreasonBaseModel):
    announcement: TaskAnnouncement = Field(description="The original call for proposals.")
    bids: list[AgentBid] = Field(default_factory=list, description="The array of received bids.")
    award: TaskAward | None = Field(
        default=None, description="The final cryptographic receipt of the auction, if resolved."
    )
    clearing_timeout: int = Field(gt=0, description="Maximum wait time for auction settlement.")
    "\n    MATHEMATICAL BOUNDARY: Must be > 0. Defines the absolute execution ceiling before forced timeout.\n    "
    minimum_tick_size: float = Field(gt=0.0, description="The smallest allowable bid increment.")
    "\n    MATHEMATICAL BOUNDARY: Must be > 0.0. Negative or zero tick sizes will instantly trigger validation faults.\n    "  # noqa: E501

    @model_validator(mode="after")
    def sort_bids(self) -> Self:
        """Mathematically sort bids by agent_id for deterministic hashing."""
        object.__setattr__(self, "bids", sorted(self.bids, key=lambda bid: bid.agent_id))
        return self


type TelemetryScalar = str | int | float | bool | None

type MetadataDict = dict[str, TelemetryScalar | list[TelemetryScalar]]


class LogEnvelope(CoreasonBaseModel):
    """
    An out-of-band telemetry log envelope.
    """

    timestamp: float = Field(description="The UNIX timestamp of the log event.")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        description="The severity level of the log event."
    )
    message: str = Field(description="The primary log message.")
    metadata: MetadataDict = Field(
        default_factory=dict, description="Contextual key-value metadata associated with the event."
    )


class SpanTrace(CoreasonBaseModel):
    """
    An execution window span trace.
    """

    span_id: str = Field(description="The unique identifier for this execution span.")
    parent_span_id: str | None = Field(default=None, description="The identifier of the parent span, if any.")
    start_time: float = Field(description="The UNIX timestamp when the span started.")
    end_time: float | None = Field(default=None, description="The UNIX timestamp when the span ended.")
    status: Literal["OK", "ERROR", "PENDING"] = Field(description="The completion status of the span.")
    metadata: MetadataDict = Field(
        default_factory=dict, description="Contextual key-value metadata associated with the span execution."
    )


class TemporalBounds(CoreasonBaseModel):
    valid_from: float | None = Field(
        default=None, ge=0.0, description="The UNIX timestamp when this memory became true."
    )
    valid_to: float | None = Field(default=None, description="The UNIX timestamp when this memory was invalidated.")
    interval_type: CausalInterval | None = Field(
        default=None, description="The Allen's interval algebra or causal relationship classification."
    )

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Self:
        if self.valid_from is not None and self.valid_to is not None and (self.valid_to < self.valid_from):
            raise ValueError("valid_to cannot be before valid_from")
        return self


class TerminalBufferState(CoreasonBaseModel):
    type: Literal["terminal"] = Field(
        default="terminal", description="Discriminator for Causal Actuators on structural buffers."
    )
    working_directory: str = Field(description="Capability Perimeters defining context bounds.")
    stdout_hash: str = Field(description="The SHA-256 hash of the Exogenous Perturbations captured.")
    stderr_hash: str = Field(description="The SHA-256 hash tracking structural deviation anomalies.")
    env_variables_hash: str = Field(description="The SHA-256 hash of the state-space context matrix.")


type AnyToolchainState = Annotated[
    BrowserDOMState | TerminalBufferState,
    Field(
        discriminator="type",
        description="A discriminated union of Causal Actuators defining strict perimeters for Exogenous Perturbations to the causal graph.",  # noqa: E501
    ),
]


class TheoryOfMindSnapshot(CoreasonBaseModel):
    target_agent_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the agent whose mind is being modeled.",  # noqa: E501
    )
    assumed_shared_beliefs: list[str] = Field(
        description="A list of Content Identifiers (CIDs) acting as cryptographic Lineage Watermarks that the modeling agent assumes the target already possesses."  # noqa: E501
    )
    identified_knowledge_gaps: list[str] = Field(
        description="Specific topics or logical premises the target agent is assumed to be missing."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "assumed_shared_beliefs", sorted(self.assumed_shared_beliefs))
        object.__setattr__(self, "identified_knowledge_gaps", sorted(self.identified_knowledge_gaps))
        return self

    empathy_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical confidence (0.0 to 1.0) the agent has in its model of the target's mind.",
    )


class ToolInvocationEvent(BaseStateEvent):
    """A Priori Kinetic Commitment representing the Pearlian Do-Operator prior to network execution."""

    type: Literal["tool_invocation"] = Field(
        default="tool_invocation", description="Discriminator type for a tool invocation event."
    )
    tool_name: str = Field(description="The exact tool targeted in the ActionSpaceManifest.")
    parameters: dict[str, Any] = Field(description="The intended JSON-RPC payload.")
    authorized_budget_magnitude: int | None = Field(
        default=None, ge=0, description="The maximum escrow unlocked for this specific run."
    )


class TraceExportBatch(CoreasonBaseModel):
    batch_id: str = Field(description="Unique identifier for this telemetry snapshot.")
    spans: list[ExecutionSpan] = Field(
        default_factory=list, description="A collection of execution spans to be serialized."
    )

    @model_validator(mode="after")
    def sort_spans(self) -> Any:
        object.__setattr__(self, "spans", sorted(self.spans, key=lambda s: s.span_id))
        return self


class TruthMaintenancePolicy(CoreasonBaseModel):
    decay_propagation_rate: float = Field(
        ge=0.0, le=1.0, description="Entropy Penalty applied per edge traversal during a defeasible cascade."
    )
    epistemic_quarantine_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The minimum certainty boundary. If an event's propagated confidence drops below this threshold, it is structurally quarantined.",  # noqa: E501
    )
    enforce_cross_agent_quarantine: bool = Field(
        default=False,
        description="If True, the orchestrator must automatically emit global QuarantineIntents to sever infected SemanticEdges across the swarm to prevent epistemic contagion.",  # noqa: E501
    )
    max_cascade_depth: int = Field(gt=0, description="The absolute recursion depth limit for state retractions.")
    max_quarantine_blast_radius: int = Field(
        gt=0, description="The maximum number of nodes allowed to be severed in a single defeasible event."
    )


class UtilityJustificationGraph(CoreasonBaseModel):
    """
    AGENT INSTRUCTION: Immutable cryptographic receipt of multi-dimensional utility routing.
    If variance threshold falls below delta, fallback to deterministic ensemble superposition.
    """

    optimizing_vectors: dict[str, float] = Field(
        default_factory=dict, description="Multi-dimensional continuous values representing optimizations."
    )
    degrading_vectors: dict[str, float] = Field(
        default_factory=dict, description="Multi-dimensional continuous values representing degradations."
    )
    superposition_variance_threshold: float = Field(
        ...,
        ge=0.0,
        allow_inf_nan=False,
        description="The statistical variance threshold below which deterministic fallback is enforced.",
    )
    ensemble_spec: EnsembleTopologySpec | None = Field(
        default=None,
        description="The deterministic ensemble specification to fall back on when threshold falls below delta.",
    )

    @model_validator(mode="after")
    def _enforce_mathematical_interlocks(self) -> "UtilityJustificationGraph":
        if self.ensemble_spec is not None and self.superposition_variance_threshold == 0.0:
            raise ValueError(
                "Topological Interlock Failed: ensemble_spec defined but variance threshold is 0.0. Mathematical certainty prohibits superposition."  # noqa: E501
            )
        for vectors in (self.optimizing_vectors, self.degrading_vectors):
            for key, val in vectors.items():
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Tensor Poisoning Detected: Vector '{key}' contains invalid float {val}.")
        return self


class VectorEmbedding(CoreasonBaseModel):
    vector_base64: str = Field(
        pattern="^[A-Za-z0-9+/]*={0,2}$", max_length=5000000, description="The base64-encoded dense vector array."
    )
    dimensionality: int = Field(description="The size of the vector array.")
    model_name: str = Field(description="The provenance of the embedding model used (e.g., 'text-embedding-3-large').")


class SemanticEdge(CoreasonBaseModel):
    edge_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this semantic edge to the Merkle-DAG."  # noqa: E501
    )
    subject_node_id: str = Field(description="The origin SemanticNode Content Identifier (CID).")
    object_node_id: str = Field(description="The destination SemanticNode Content Identifier (CID).")
    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="The probabilistic certainty of this logical connection."
    )
    predicate: str = Field(description="The string representation of the relationship (e.g., 'WORKS_FOR').")
    embedding: VectorEmbedding | None = Field(
        default=None,
        description="Topologically Bounded Latent Spaces used to calculate exact geometric distance and preserve structural Isometry.",  # noqa: E501
    )
    provenance: EpistemicProvenance | None = Field(
        default=None,
        description="Optional distinct provenance if the relationship was inferred separately from the nodes.",
    )
    temporal_bounds: TemporalBounds | None = Field(
        default=None, description="The time window during which this relationship holds true."
    )
    causal_relationship: Literal["causes", "confounds", "correlates_with", "undirected"] = Field(
        default="undirected", description="The Pearlian directionality of the semantic relationship."
    )


class SemanticNode(CoreasonBaseModel):
    node_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this semantic node to the Merkle-DAG."  # noqa: E501
    )
    label: str = Field(description="The categorical label of the node (e.g., 'Person', 'Concept').")
    scope: Literal["global", "tenant", "session"] = Field(
        default="session",
        description="The cryptographic namespace partitioning boundary. Global is public, Tenant is corporate, Session is ephemeral.",  # noqa: E501
    )
    text_chunk: str = Field(max_length=50000, description="The raw natural language representation of the memory.")
    embedding: VectorEmbedding | None = Field(
        default=None,
        description="Topologically Bounded Latent Spaces used to calculate exact geometric distance and preserve structural Isometry.",  # noqa: E501
    )
    provenance: EpistemicProvenance = Field(description="The cryptographic chain of custody for this memory.")
    tier: CognitiveTier = Field(default="semantic", description="The cognitive tier this memory resides in.")
    temporal_bounds: TemporalBounds | None = Field(
        default=None, description="The time window during which this node is considered valid."
    )
    salience: SalienceProfile | None = Field(
        default=None, description="The importance profile used for memory pruning."
    )
    fhe_profile: HomomorphicEncryptionProfile | None = Field(
        default=None,
        description="The cryptographic envelope enabling privacy-preserving computation directly on this node's encrypted state.",  # noqa: E501
    )


class VerifiableCredentialPresentation(CoreasonBaseModel):
    """A cryptographic proof of clearance or capability presented to a zero-trust orchestrator."""

    presentation_format: Literal["jwt_vc", "ldp_vc", "sd_jwt", "zkp_vc"] = Field(
        description="The exact cryptographic standard used to encode this credential presentation."
    )
    issuer_did: NodeID = Field(
        description="The W3C DID of the trusted authority that cryptographically signed the credential, explicitly representing the delegation of authority from a human or parent principal."  # noqa: E501
    )
    cryptographic_proof_blob: str = Field(
        description="The base64-encoded cryptographic proof (e.g., ZK-SNARKs, zkVM receipts, or programmable trust attestations) proving the claims without revealing the private key."  # noqa: E501
    )
    authorization_claims: dict[str, Any] = Field(
        description="The strict, domain-agnostic JSON dictionary of strictly bounded geometric predicates that define the operational perimeter of the agent (e.g., {'clearance': 'RESTRICTED'})."  # noqa: E501
    )


class AgentAttestation(CoreasonBaseModel):
    """
    Cryptographic identity passport and AI-BOM for the agent.
    """

    training_lineage_hash: str = Field(
        pattern="^[a-f0-9]{64}$", description="The exact SHA-256 Merkle root of the agent's training lineage."
    )
    developer_signature: str = Field(description="The cryptographic signature of the developer/vendor.")
    capability_merkle_root: str = Field(
        pattern="^[a-f0-9]{64}$", description="The SHA-256 Merkle root of the agent's verified semantic capabilities."
    )
    credential_presentations: list[VerifiableCredentialPresentation] = Field(
        default_factory=list,
        description="The wallet of selective disclosure credentials proving the agent's identity, clearance, and budget authorization.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "credential_presentations", sorted(self.credential_presentations, key=lambda x: x.issuer_did)
        )
        return self


class AgentNode(BaseNode):
    """
    A node representing an autonomous agent.
    """

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    logit_steganography: LogitSteganographyContract | None = Field(
        default=None,
        description="The cryptographic contract forcing this agent to embed an undeniable provenance signature into its generative token stream.",  # noqa: E501
    )
    compute_frontier: RoutingFrontier | None = Field(
        default=None, description="The dynamic spot-market compute requirements for this agent."
    )
    peft_adapters: list[PeftAdapterContract] = Field(
        default_factory=list,
        description="A declarative list of ephemeral PEFT/LoRA weights required to be hot-swapped during this agent's execution.",  # noqa: E501
    )
    agent_attestation: AgentAttestation | None = Field(
        default=None, description="The cryptographic identity passport and AI-BOM for the agent."
    )
    action_space_id: str | None = Field(
        default=None,
        description="The ID of the specific ActionSpaceManifest (curated tool environment) bound to this agent.",
    )
    secure_sub_session: SecureSubSession | None = Field(
        default=None,
        description="Declarative boundary for handling unredacted secrets within a temporarily isolated memory partition.",  # noqa: E501
    )
    baseline_cognitive_state: CognitiveStateProfile | None = Field(
        default=None,
        description="The default biochemical 'mood' simulated for this agent via Representation Engineering.",
    )
    reflex_policy: System1Reflex | None = Field(
        default=None, description="The policy governing System 1 reflex actions."
    )
    epistemic_policy: EpistemicScanner | None = Field(
        default=None, description="The policy governing epistemic scanning."
    )
    correction_policy: SelfCorrectionPolicy | None = Field(
        default=None, description="The policy governing self-correction loops."
    )
    escalation_policy: EscalationContract | None = Field(
        default=None, description="The mathematical boundary authorizing the agent to spin up Test-Time Compute."
    )
    prm_policy: ProcessRewardContract | None = Field(
        default=None, description="The ruleset governing how intermediate thoughts are scored and pruned."
    )
    active_inference_policy: ActiveInferenceContract | None = Field(
        default=None,
        description="The formal contract demanding mathematical proof of Expected Information Gain before authorizing tool execution.",  # noqa: E501
    )
    analogical_policy: AnalogicalMappingTask | None = Field(
        default=None, description="The formal contract forcing the agent to execute cross-domain lateral thinking."
    )
    interventional_policy: InterventionalCausalTask | None = Field(
        default=None,
        description="The formal contract authorizing the agent to mutate variables to prove Pearlian causation.",
    )
    symbolic_handoff_policy: NeuroSymbolicHandoff | None = Field(
        default=None,
        description="The API-like contract allowing the agent to offload rigid logic to deterministic CPU solvers.",
    )
    audit_policy: MechanisticAuditContract | None = Field(
        default=None,
        description="The adaptive trigger policy for executing deep mechanistic interpretability brain-scans on this agent.",  # noqa: E501
    )
    anchoring_policy: AnchoringPolicy | None = Field(
        default=None,
        description="The declarative contract mathematically binding this agent to a core altruistic objective.",
    )

    @model_validator(mode="after")
    def sort_agent_node_arrays(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self


type AnyNode = Annotated[
    AgentNode | HumanNode | SystemNode | CompositeNode | MemoizedNode,
    Field(discriminator="type", description="A discriminated union of all valid workflow nodes."),
]


class BaseTopology(CoreasonBaseModel):
    """
    Base configuration for any workflow topology.
    """

    lifecycle_phase: Literal["draft", "live"] = Field(
        default="live", description="The execution phase of the graph. 'draft' allows incomplete structural state."
    )
    architectural_intent: str | None = Field(
        default=None, description="The AI's declarative rationale for selecting this topology."
    )
    justification: str | None = Field(
        default=None, description="Cryptographic/audit justification for this topology's configuration."
    )
    nodes: dict[NodeID, AnyNode] = Field(description="Flat registry of all nodes in this topology.")
    shared_state_contract: StateContract | None = Field(
        default=None, description="The schema-on-write contract governing the internal state of this topology."
    )
    information_flow: InformationFlowPolicy | None = Field(
        default=None,
        description="The structural Data Loss Prevention (DLP) contract governing all state mutations in this topology.",  # noqa: E501
    )
    observability: ObservabilityPolicy | None = Field(
        default=None, description="The distributed tracing rules bound to this specific execution graph."
    )


class CouncilTopology(BaseTopology):
    """
    A Council workflow topology involving multiple voting members and an adjudicator.
    """

    type: Literal["council"] = Field(default="council", description="Discriminator for a Council topology.")
    adjudicator_id: NodeID = Field(description="The NodeID of the adjudicator that synthesizes the council's output.")
    diversity_policy: DiversityConstraint | None = Field(
        default=None, description="Constraints enforcing cognitive heterogeneity across the council."
    )
    consensus_policy: ConsensusPolicy | None = Field(
        default=None, description="The explicit ruleset governing how the council resolves disagreements."
    )
    ontological_alignment: OntologicalAlignmentPolicy | None = Field(
        default=None,
        description="The pre-flight execution gate forcing agents to mathematically align their latent semantics before participating in the topology.",  # noqa: E501
    )
    council_escrow: EscrowPolicy | None = Field(
        default=None,
        description="The strictly typed mathematical surface area to lock funds specifically for PBFT council execution and slashing.",  # noqa: E501
    )

    @model_validator(mode="after")
    def enforce_funded_byzantine_slashing(self) -> Self:
        if (
            self.consensus_policy is not None
            and self.consensus_policy.strategy == "pbft"
            and (self.consensus_policy.quorum_rules is not None)
            and (self.consensus_policy.quorum_rules.byzantine_action == "slash_escrow")
        ) and (self.council_escrow is None or self.council_escrow.escrow_locked_magnitude <= 0):
            raise ValueError("Topological Interlock Failed: PBFT with slash_escrow requires a funded council_escrow.")
        return self

    @model_validator(mode="after")
    def check_adjudicator_id(self) -> Self:
        if self.adjudicator_id not in self.nodes:
            raise ValueError(f"Adjudicator ID '{self.adjudicator_id}' is not in nodes registry.")
        return self


class DAGTopology(BaseTopology):
    """
    A Directed Acyclic Graph workflow topology.
    """

    type: Literal["dag"] = Field(default="dag", description="Discriminator for a DAG topology.")
    edges: list[tuple[NodeID, NodeID]] = Field(default_factory=list, description="List of edges between nodes.")
    allow_cycles: bool = Field(
        default=False, description="Configuration indicating if cycles are allowed during validation."
    )
    backpressure: BackpressurePolicy | None = Field(
        default=None, description="Declarative backpressure constraints for the graph edges."
    )
    max_depth: int = Field(ge=1, le=256, description="The maximum recursive depth of the routing DAG.")
    "\n    TOPOLOGICAL BOUNDARY: Must be >= 1 and <= 256. Prevents runaway agentic cyclic recursion.\n    "
    max_fan_out: int = Field(ge=1, le=1024, description="The maximum number of parallel child nodes.")
    "\n    TOPOLOGICAL BOUNDARY: Must be >= 1 and <= 1024. Limits horizontal compute explosion.\n    "

    @model_validator(mode="after")
    def sort_dag_topology_arrays(self) -> Self:
        object.__setattr__(self, "edges", sorted(self.edges))
        return self

    @model_validator(mode="after")
    def verify_edges_exist(self) -> Self:
        if self.lifecycle_phase == "draft":
            return self
        for source, target in self.edges:
            if source not in self.nodes:
                raise ValueError(f"Edge source '{source}' does not exist in nodes registry.")
            if target not in self.nodes:
                raise ValueError(f"Edge target '{target}' does not exist in nodes registry.")
        if not self.allow_cycles:
            adj: dict[NodeID, list[NodeID]] = {node_id: [] for node_id in self.nodes}
            for source, target in self.edges:
                adj[source].append(target)
            visited: set[NodeID] = set()
            recursion_stack: set[NodeID] = set()
            for start_node in self.nodes:
                if start_node in visited:
                    continue
                stack = [(start_node, iter(adj[start_node]))]
                visited.add(start_node)
                recursion_stack.add(start_node)
                while stack:
                    curr, neighbors = stack[-1]
                    try:
                        neighbor = next(neighbors)
                        if neighbor not in visited:
                            visited.add(neighbor)
                            recursion_stack.add(neighbor)
                            stack.append((neighbor, iter(adj[neighbor])))
                        elif neighbor in recursion_stack:
                            raise ValueError("Graph contains cycles but allow_cycles is False.")
                    except StopIteration:
                        recursion_stack.remove(curr)
                        stack.pop()
        return self


class DigitalTwinTopology(BaseTopology):
    """
    An isolated sandbox graph representing a Digital Twin.
    """

    type: Literal["digital_twin"] = Field(
        default="digital_twin", description="Discriminator for a Digital Twin topology."
    )
    target_topology_id: str = Field(
        description="The identifier (expected to be a W3C DID) pointing to the real-world topology it is cloning."
    )
    convergence_sla: SimulationConvergenceSLA = Field(
        description="The strict mathematical boundaries for the simulation."
    )
    enforce_no_side_effects: bool = Field(
        default=True,
        description="A declarative flag that instructs the runtime to mathematically sever all external write access.",
    )


class EvaluatorOptimizerTopology(BaseTopology):
    """
    A formalized Actor-Critic micro-topology enforcing strict, finite generation-evaluation-revision cycles.
    """

    type: Literal["evaluator_optimizer"] = Field(
        default="evaluator_optimizer", description="Discriminator for an Evaluator-Optimizer loop."
    )
    generator_node_id: NodeID = Field(description="The ID of the actor generating the payload.")
    evaluator_node_id: NodeID = Field(description="The ID of the critic scoring the payload.")
    max_revision_loops: int = Field(
        ge=1, description="The absolute limit on Actor-Critic cycles to prevent infinite compute burn."
    )
    require_multimodal_grounding: bool = Field(
        default=False,
        description="If True, the evaluator_node_id MUST mathematically mask all tokens outside the MultimodalTokenAnchor during its forward pass to execute pure adversarial Proposer-Critique validation.",  # noqa: E501
    )

    @model_validator(mode="after")
    def verify_bipartite_nodes(self) -> Self:
        """Mathematically guarantees both the generator and evaluator exist in the node registry."""
        if self.generator_node_id not in self.nodes:
            raise ValueError(f"Generator node '{self.generator_node_id}' not found in topology nodes.")
        if self.evaluator_node_id not in self.nodes:
            raise ValueError(f"Evaluator node '{self.evaluator_node_id}' not found in topology nodes.")
        if self.generator_node_id == self.evaluator_node_id:
            raise ValueError("Generator and Evaluator cannot be the same node.")
        return self


class EvolutionaryTopology(BaseTopology):
    """
    An Evolutionary workflow topology that mutates and breeds agents over generations.
    """

    type: Literal["evolutionary"] = Field(
        default="evolutionary", description="Discriminator for an Evolutionary topology."
    )
    generations: int = Field(description="The absolute limit on evolutionary breeding cycles.")
    population_size: int = Field(description="The number of concurrent agents instantiated per generation.")
    mutation: MutationPolicy = Field(description="The constraints governing random heuristic mutations.")
    crossover: CrossoverStrategy = Field(description="The mathematical rules for combining elite agents.")
    fitness_objectives: list[FitnessObjective] = Field(
        description="The multi-dimensional criteria used to score and cull the population."
    )

    @model_validator(mode="after")
    def sort_objectives(self) -> Self:
        object.__setattr__(
            self, "fitness_objectives", sorted(self.fitness_objectives, key=lambda obj: obj.target_metric)
        )
        return self


class SMPCTopology(BaseTopology):
    """
    A Secure Multi-Party Computation topology.
    """

    type: Literal["smpc"] = Field(default="smpc", description="Discriminator for SMPC Topology.")
    smpc_protocol: Literal["garbled_circuits", "secret_sharing", "oblivious_transfer"] = Field(
        description="The exact cryptographic P2P protocol the nodes must use to evaluate the function."
    )
    joint_function_uri: str = Field(
        description="The URI or hash pointing to the exact math circuit or polynomial function the ring will collaboratively compute."  # noqa: E501
    )
    participant_node_ids: list[str] = Field(
        min_length=2,
        description="The strict ordered list of NodeIDs participating in the Secure Multi-Party Computation ring.",
    )
    ontological_alignment: OntologicalAlignmentPolicy | None = Field(
        default=None,
        description="The pre-flight execution gate forcing agents to mathematically align their latent semantics before participating in the topology.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "participant_node_ids", sorted(self.participant_node_ids))
        return self


class SwarmTopology(BaseTopology):
    """
    A dynamic Swarm workflow topology.
    """

    type: Literal["swarm"] = Field(default="swarm", description="Discriminator for a Swarm topology.")
    spawning_threshold: int = Field(default=3, description="Threshold limit for dynamic spawning of additional nodes.")
    max_concurrent_agents: int = Field(
        default=10, le=100, description="The absolute ceiling for concurrent agent threads."
    )
    auction_policy: AuctionPolicy | None = Field(
        default=None, description="The mathematical policy governing task decentralization via Spot Markets."
    )
    active_prediction_markets: list[PredictionMarketState] = Field(
        default_factory=list, description="The live algorithmic betting markets resolving swarm consensus."
    )
    resolved_markets: list[MarketResolutionState] = Field(
        default_factory=list,
        description="The immutable records of finalized markets and reputation capital distributions.",
    )

    @model_validator(mode="after")
    def enforce_concurrency_ceiling(self) -> Self:
        if self.spawning_threshold > self.max_concurrent_agents:
            raise ValueError("spawning_threshold cannot exceed max_concurrent_agents")
        return self


class AdversarialMarketTopology(CoreasonBaseModel):
    """
    A Zero-Cost Macro abstraction that deterministically compiles into a Red/Blue team CouncilTopology.
    """

    type: Literal["macro_adversarial"] = Field(
        default="macro_adversarial", description="Discriminator for adversarial macro."
    )
    blue_team_ids: list[NodeID] = Field(min_length=1, description="Nodes assigned to the Blue Team.")
    red_team_ids: list[NodeID] = Field(min_length=1, description="Nodes assigned to the Red Team.")
    adjudicator_id: NodeID = Field(description="The neutral node responsible for synthesizing the market resolution.")
    market_rules: PredictionMarketPolicy = Field(description="The mathematical AMM rules for the debate.")

    @model_validator(mode="after")
    def verify_disjoint_sets(self) -> Self:
        blue_set = set(self.blue_team_ids)
        red_set = set(self.red_team_ids)
        if blue_set.intersection(red_set):
            raise ValueError("Topological Contradiction: A node cannot exist in both the Blue and Red teams.")
        if self.adjudicator_id in blue_set or self.adjudicator_id in red_set:
            raise ValueError("Topological Contradiction: The adjudicator cannot be a member of a competing team.")
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "blue_team_ids", sorted(self.blue_team_ids))
        object.__setattr__(self, "red_team_ids", sorted(self.red_team_ids))
        return self

    def compile_to_base_topology(self) -> CouncilTopology:
        """Deterministically unwraps the macro into a rigid CouncilTopology."""
        nodes: dict[NodeID, AnyNode] = {self.adjudicator_id: SystemNode(description="Synthesizing Adjudicator")}
        for node_id in self.blue_team_ids:
            nodes[node_id] = SystemNode(description="Blue Team Member")
        for node_id in self.red_team_ids:
            nodes[node_id] = SystemNode(description="Red Team Member")
        consensus = ConsensusPolicy(strategy="prediction_market", prediction_market_rules=self.market_rules)
        return CouncilTopology(nodes=nodes, adjudicator_id=self.adjudicator_id, consensus_policy=consensus)


class ConsensusFederationTopology(CoreasonBaseModel):
    """
    A Zero-Cost Macro abstraction compiling into a standard PBFT CouncilTopology.
    """

    type: Literal["macro_federation"] = Field(
        default="macro_federation", description="Discriminator for federation macro."
    )
    participant_ids: list[NodeID] = Field(min_length=3, description="The nodes forming the PBFT ring.")
    adjudicator_id: NodeID = Field(description="The orchestrating sequencer for the PBFT consensus.")
    quorum_rules: QuorumPolicy = Field(description="The strict BFT tolerance bounds.")

    @model_validator(mode="after")
    def verify_adjudicator_isolation(self) -> Self:
        if self.adjudicator_id in self.participant_ids:
            raise ValueError("Topological Contradiction: Adjudicator cannot act as a voting participant.")
        return self

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "participant_ids", sorted(self.participant_ids))
        return self

    def compile_to_base_topology(self) -> CouncilTopology:
        nodes: dict[NodeID, AnyNode] = {self.adjudicator_id: SystemNode(description="PBFT Sequencer")}
        for node_id in self.participant_ids:
            nodes[node_id] = SystemNode(description="PBFT Participant")
        return CouncilTopology(
            nodes=nodes,
            adjudicator_id=self.adjudicator_id,
            consensus_policy=ConsensusPolicy(strategy="pbft", quorum_rules=self.quorum_rules),
        )


type AnyTopology = Annotated[
    DAGTopology
    | CouncilTopology
    | SwarmTopology
    | EvolutionaryTopology
    | SMPCTopology
    | EvaluatorOptimizerTopology
    | DigitalTwinTopology
    | AdversarialMarketTopology
    | ConsensusFederationTopology,
    Field(discriminator="type", description="A discriminated union of workflow topologies."),
]


class WorkflowEnvelope(CoreasonBaseModel):
    """
    The root envelope for an orchestrated workflow payload.
    """

    manifest_version: SemanticVersion = Field(description="The semantic version of this workflow manifestation schema.")
    topology: AnyTopology = Field(description="The underlying topology governing execution routing.")
    governance: GlobalGovernance | None = Field(
        default=None, description="Macro-economic circuit breakers and TTL limits for the swarm."
    )
    tenant_id: str | None = Field(
        default=None, max_length=255, description="The enterprise tenant boundary for this execution."
    )
    session_id: str | None = Field(
        default=None, max_length=255, description="The ephemeral session boundary for this execution."
    )
    max_risk_tolerance: RiskLevel | None = Field(
        default=None, description="The absolute maximum enterprise risk threshold permitted for this topology."
    )
    allowed_data_classifications: list[InformationClassification] | None = Field(
        default=None,
        description="The declarative whitelist of data classifications permitted to flow through this graph.",
    )
    federated_discovery: FederatedDiscoveryProtocol | None = Field(
        default=None, description="The broadcast protocol for B2B multi-swarm discovery."
    )
    federated_sla: BilateralSLA | None = Field(
        default=None,
        description="The B2B Service Level Agreement contract that must be mathematically satisfied before multi-tenant graph coupling.",  # noqa: E501
    )
    pq_signature: PostQuantumSignature | None = Field(
        default=None, description="The quantum-resistant signature securing the root execution graph."
    )


class WetwareAttestationContract(CoreasonBaseModel):
    """
    AGENT INSTRUCTION: This model represents a SOTA cryptographic receipt
    proving a human in the loop physically authorized a state transition.
    """

    mechanism: AttestationMechanism = Field(
        ..., description="The SOTA cryptographic mechanism used to generate the proof."
    )
    did_subject: str = Field(
        ..., pattern="^did:[a-z0-9]+:.*$", description="The Decentralized Identifier (DID) of the human operator."
    )
    cryptographic_payload: str = Field(
        ...,
        pattern="^[A-Za-z0-9+/=_-]+$",
        description="The strictly formatted (Base64url/Hex/Multibase) signature or proof.",
    )
    dag_node_nonce: UUID = Field(
        ..., description="The cryptographic nonce tightly binding this signature to the specific Merkle-DAG node."
    )


class InterventionVerdict(CoreasonBaseModel):
    """
    Emitted by a human or oversight AI to resume the swarm.
    """

    type: Literal["verdict"] = Field(default="verdict", description="The type of the intervention payload.")
    intervention_request_id: UUID = Field(
        description="The cryptographic nonce uniquely identifying the intervention request."
    )
    target_node_id: NodeID = Field(description="The ID of the target node.")
    approved: bool = Field(description="Indicates whether the proposed action was approved.")
    feedback: str | None = Field(description="Optional feedback provided along with the verdict.")
    attestation: WetwareAttestationContract | None = Field(
        default=None, description="The cryptographic proof provided by the human operator, if required."
    )

    @model_validator(mode="after")
    def verify_attestation_nonce(self) -> "InterventionVerdict":
        """
        Mathematically guarantees that if a cryptographic signature is presented,
        it cannot be a replay attack from a different node in the DAG.
        """
        if self.attestation is not None and self.attestation.dag_node_nonce != self.intervention_request_id:
            raise ValueError(
                "Anti-Replay Lock Triggered: Attestation nonce does not match the intervention request ID."
            )
        return self


type AnyInterventionPayload = Annotated[
    InterventionRequest | InterventionVerdict | OverrideIntent | ConstitutionalAmendmentProposal,
    Field(discriminator="type"),
]


class EpistemicQuarantineSnapshot(CoreasonBaseModel):
    """Represents the Epistemic Quarantine, partitioned from the Committed Epistemic Ledger."""

    system_prompt: str = Field(
        description="The basal non-monotonic instruction set currently held in Epistemic Quarantine."
    )
    active_context: dict[str, str] = Field(
        description="The ephemeral latent variables and environmental bindings currently active in Epistemic Quarantine."  # noqa: E501
    )
    argumentation: ArgumentGraph | None = Field(
        default=None,
        description="The formal graph of non-monotonic claims and defeasible attacks currently active in the swarm's working memory.",  # noqa: E501
    )
    theory_of_mind_models: list[TheoryOfMindSnapshot] = Field(
        default_factory=list,
        description="Empathetic models of other agents to compress and target outgoing communications.",
    )
    affordance_projection: OntologicalSurfaceProjection | None = Field(
        default=None,
        description="The mathematically bounded subgraph of capabilities currently available to the agent.",
    )
    capability_attestations: list[FederatedCapabilityAttestation] = Field(
        default_factory=list,
        description="Immutable cryptographic receipts of dynamically discovered external enterprise connectors.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "theory_of_mind_models", sorted(self.theory_of_mind_models, key=lambda x: x.target_agent_id)
        )
        object.__setattr__(
            self, "capability_attestations", sorted(self.capability_attestations, key=lambda x: x.attestation_id)
        )
        return self


class ZeroKnowledgeProof(CoreasonBaseModel):
    proof_protocol: Literal["zk-SNARK", "zk-STARK", "plonk", "bulletproofs"] = Field(
        description="The mathematical dialect of the cryptographic proof."
    )
    public_inputs_hash: str = Field(
        description="The SHA-256 hash of the public inputs (e.g., prompt, Lamport clock) anchoring this proof to the specific state index."  # noqa: E501
    )
    verifier_key_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking this node to the public evaluation key."  # noqa: E501
    )
    cryptographic_blob: str = Field(
        max_length=5000000, description="The base64-encoded succinct cryptographic proof payload."
    )
    latent_state_commitments: dict[str, Annotated[str, StringConstraints(max_length=100)]] = Field(
        default_factory=dict,
        description="Cryptographic bindings (hashes) of intermediate residual stream states to prevent activation spoofing.",  # noqa: E501
    )


class BeliefMutationEvent(BaseStateEvent):
    type: Literal["belief_mutation"] = Field(
        default="belief_mutation", description="Discriminator type for a Belief Assertion event."
    )
    payload: dict[str, Any] = Field(
        description="Topologically Bounded Latent Spaces capturing the semantic representation of the agent's internal cognitive shift or synthesis that anchor statistical probability to a definitive causal event hash."  # noqa: E501
    )
    source_node_id: NodeID | None = Field(
        default=None, description="The specific topological node that synthesized this belief assertion."
    )
    causal_attributions: list[CausalAttribution] = Field(
        default_factory=list,
        description="Immutable audit trail of prior states that forced this specific cognitive synthesis.",
    )
    hardware_attestation: HardwareEnclaveAttestation | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this belief was synthesized in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeProof | None = Field(
        default=None,
        description="The mathematical attestation proving this belief synthesis was appended securely without model-downgrade fraud.",  # noqa: E501
    )
    uncertainty_profile: CognitiveUncertaintyProfile | None = Field(
        default=None, description="The mathematical quantification of doubt associated with this synthesized belief."
    )
    scratchpad_trace: LatentScratchpadTrace | None = Field(
        default=None,
        description="The cryptographic record of the non-monotonic internal monologue that justifies this belief.",
    )
    neural_audit: NeuralAuditAttestation | None = Field(
        default=None,
        description="The mathematical brain-scan proving exactly which neural circuits fired to append this event.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "causal_attributions", sorted(self.causal_attributions, key=lambda x: x.source_event_id)
        )
        return self

    @field_validator("payload", mode="before")
    @classmethod
    def enforce_payload_topology(cls, v: Any) -> Any:
        return _validate_payload_bounds(v)


class ObservationEvent(BaseStateEvent):
    type: Literal["observation"] = Field(
        default="observation", description="Discriminator type for an observation event."
    )
    payload: dict[str, Any] = Field(
        description="Neurosymbolic Bindings of the raw, lossless semantic output appended from the environment or tool execution that anchor statistical probability to a definitive causal event hash."  # noqa: E501
    )
    source_node_id: NodeID | None = Field(
        default=None, description="The specific topological node that appended this observation."
    )
    hardware_attestation: HardwareEnclaveAttestation | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this observation was appended in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeProof | None = Field(
        default=None, description="The mathematical attestation proving this observation was appended securely."
    )
    toolchain_snapshot: AnyToolchainState | None = Field(
        default=None,
        description="The immutable cryptographic snapshot of the external environment at the moment of observation.",
    )
    sensory_trigger: EmbodiedSensoryVector | None = Field(
        default=None, description="The continuous multimodal trigger that forced this discrete observation."
    )
    neural_audit: NeuralAuditAttestation | None = Field(
        default=None,
        description="The mathematical brain-scan proving exactly which neural circuits fired to append this event.",
    )
    triggering_invocation_id: str | None = Field(
        default=None,
        description="The Event ID of the specific ToolInvocationEvent that spawned this observation, forming a strict bipartite directed edge.",  # noqa: E501
    )

    @field_validator("payload", mode="before")
    @classmethod
    def enforce_payload_topology(cls, v: Any) -> Any:
        return _validate_payload_bounds(v)


type AnyStateEvent = Annotated[
    ObservationEvent
    | BeliefMutationEvent
    | SystemFaultEvent
    | HypothesisGenerationEvent
    | BargeInInterruptEvent
    | CounterfactualRegretEvent
    | ToolInvocationEvent
    | EpistemicPromotionEvent
    | NormativeDriftEvent
    | PersistenceCommitReceipt,
    Field(discriminator="type", description="A discriminated union of state events."),
]


class EpistemicLedger(CoreasonBaseModel):
    """The Committed Epistemic Ledger (crystallized truth), completely partitioned from volatile working memory
    or Epistemic Quarantine."""

    history: list[AnyStateEvent] = Field(
        max_length=10000, description="An append-only, cryptographic ledger of state events."
    )
    checkpoints: list[TemporalCheckpoint] = Field(
        default_factory=list, description="Hard temporal anchors allowing state restoration."
    )
    active_rollbacks: list[RollbackRequest] = Field(
        default_factory=list, description="Causal invalidations actively enforced on the execution tree."
    )
    eviction_policy: EvictionPolicy | None = Field(
        default=None, description="The strict mathematical boundary governing context window compression."
    )
    migration_contracts: list[MigrationContract] = Field(
        default_factory=list,
        description="Declarative rules to translate historical states to the current active schema version.",
    )
    truth_maintenance_policy: TruthMaintenancePolicy | None = Field(
        default=None,
        description="The mathematical contract governing automated causal graph ablations and probabilistic decay.",
    )
    active_cascades: list[DefeasibleCascade] = Field(
        default_factory=list,
        description="The active state-differential payload muting specific causal subgraphs due to falsification.",
    )
    crystallization_policy: CrystallizationPolicy | None = Field(
        default=None,
        description="The mathematical threshold required to compress episodic observations into semantic rules.",
    )

    @model_validator(mode="after")
    def sort_history(self) -> Self:
        object.__setattr__(self, "history", sorted(self.history, key=lambda event: event.timestamp))
        object.__setattr__(self, "checkpoints", sorted(self.checkpoints, key=lambda x: x.checkpoint_id))
        object.__setattr__(self, "active_rollbacks", sorted(self.active_rollbacks, key=lambda x: x.request_id))
        object.__setattr__(self, "migration_contracts", sorted(self.migration_contracts, key=lambda x: x.contract_id))
        object.__setattr__(self, "active_cascades", sorted(self.active_cascades, key=lambda x: x.cascade_id))
        return self


# =========================================================================
# STRATUM 9: TOPOLOGICAL RESOLUTION (FORWARD REF EVALUATION)
# =========================================================================

CompositeNode.model_rebuild()
WorkflowEnvelope.model_rebuild()
MCPServerConfig.model_rebuild()

BaseTopology.model_rebuild()
DAGTopology.model_rebuild()
CouncilTopology.model_rebuild()
SwarmTopology.model_rebuild()
EvolutionaryTopology.model_rebuild()
SMPCTopology.model_rebuild()
EvaluatorOptimizerTopology.model_rebuild()
DigitalTwinTopology.model_rebuild()
AdversarialMarketTopology.model_rebuild()
ConsensusFederationTopology.model_rebuild()
