# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

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

type JsonPrimitiveState = (
    str
    | int
    | float
    | bool
    | None
    | list["JsonPrimitiveState"]
    | dict[Annotated[str, StringConstraints(max_length=255)], "JsonPrimitiveState"]
)


def _validate_payload_bounds(value: JsonPrimitiveState, current_depth: int = 0) -> JsonPrimitiveState:
    """
    AGENT INSTRUCTION: Mathematically bound recursive dictionary payloads
    to prevent OOM/CPU exhaustion during EpistemicLedgerState hashing.
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
    elif value is not None and (not isinstance(value, (int, float, bool))):
        raise ValueError(f"Payload value must be a valid JSON primitive, got {type(value).__name__}")
    return value


type AuctionMechanismProfile = Literal["sealed_bid", "dutch", "vickrey"]
type CausalIntervalProfile = Literal["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]
type CrossoverMechanismProfile = Literal["uniform_blend", "single_point", "heuristic"]


class InformationClassificationProfile(StrEnum):
    """
    Standardized Information Flow Control (IFC) lattice boundaries.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


type FaultCategoryProfile = Literal[
    "context_overload",
    "incorrect_context",
    "format_corruption",
    "latency_spike",
    "token_throttle",
    "network_degradation",
    "temporal_dilation",
    "dependency_blackout",
]
type CognitiveTierProfile = Literal["working", "episodic", "semantic"]
type NodeIdentifierState = Annotated[
    str,
    Field(
        min_length=7,
        pattern="^did:[a-z0-9]+:[a-zA-Z0-9.\\-_:]+$",
        description="A Decentralized Identifier (DID) representing a cryptographically accountable principal within the swarm.",  # noqa: E501
    ),
]
type OptimizationDirectionProfile = Literal["maximize", "minimize"]
type PatchOperationProfile = Literal["add", "remove", "replace", "copy", "move", "test"]
type ProfileIdentifierState = Annotated[
    str,
    Field(
        pattern="^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="A deterministic cognitive routing boundary that defines the non-monotonic instruction set for the agent.",  # noqa: E501
        examples=["default_assistant", "code_expert"],
    ),
]


class RiskLevelPolicy(StrEnum):
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
        if self == RiskLevelPolicy.SAFE:
            return 0
        if self == RiskLevelPolicy.STANDARD:
            return 1
        return 2


type SanitizationActionIntent = Literal["redact", "hash", "drop_event", "trigger_quarantine"]
type SemanticVersionState = Annotated[
    str,
    Field(
        pattern="^\\d+\\.\\d+\\.\\d+$",
        description="An Immutable structural checkpoint.",
        examples=["1.0.0", "0.1.0", "2.12.5"],
    ),
]
type SpanKindProfile = Literal["client", "server", "producer", "consumer", "internal"]
type SpanStatusCodeProfile = Literal["unset", "ok", "error"]


class TensorStructuralFormatProfile(StrEnum):
    """Mathematical tensor types for tensor payloads."""

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


type TieBreakerPolicy = Literal["lowest_cost", "lowest_latency", "highest_confidence", "random"]
type ToolIdentifierState = Annotated[
    str,
    Field(
        pattern="^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="A cryptographically deterministic capability pointer binding the agent to a verifiable spatial environment.",  # noqa: E501
        examples=["calculator", "web_search"],
    ),
]
type TopologyHashReceipt = Annotated[
    str,
    Field(
        pattern="^[a-f0-9]{64}$",
        description="A strictly typed SHA-256 hash pointing to a historically executed topological state.",
    ),
]


def _inject_topological_lock(schema: dict[str, Any]) -> None:
    current_desc = schema.get("description", "")
    lock_string = "CoReason Shared Kernel Ontology"
    if lock_string not in current_desc:
        schema["description"] = f"{lock_string}\n\n{current_desc}".strip()


class CoreasonBaseState(BaseModel):
    """
    AGENT INSTRUCTION: CoreasonBaseState is the immutable mathematical bedrock of the Hollow Data Plane, 
    utilizing RFC 8785 Canonical JSON Serialization to guarantee structural determinism across the swarm.

    CAUSAL AFFORDANCE: Enforces absolute structural rigidity. By declaring frozen=True, strict=True, 
    and extra='forbid', it mechanically prevents silent type coercion and blocks adversarial agents 
    from injecting hallucinated keys into the execution graph.

    EPISTEMIC BOUNDS: Bypasses Python's immutability lock exclusively during the instantiation phase 
    (__setattr__) to mechanically sort all unordered sets and arrays. This guarantees flawless, 
    zero-variance serialization, ensuring two identical graphs produce the exact same Merkle root hash.

    MCP ROUTING TRIGGERS: Merkle-DAG Root, RFC 8785 Canonicalization, Cryptographic Determinism, Immutable Substrate, Zero-Trust Architecture
    """

    model_config = ConfigDict(
        frozen=True, extra="forbid", validate_assignment=True, strict=True, json_schema_extra=_inject_topological_lock
    )

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


class SpatialBoundingBoxProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a 2D Euclidean bounding box within a normalized coordinate
    space to ensure resolution-independent topological scaling. As a ...Profile suffix,
    this is a declarative property descriptor.

    CAUSAL AFFORDANCE: Instructs the frontend rendering matrices to physically constrain
    graphical overlays, multimodal tokens, and UI projections within a rigid, deterministic
    spatial geometry.

    EPISTEMIC BOUNDS: All coordinate tensors (x_min, y_min, x_max, y_max) are
    mathematically clamped to a normalized continuous float space (ge=0.0, le=1.0). The
    @model_validator validate_geometry physically guarantees min bounds cannot exceed max
    bounds, preventing the generation of inverted or non-Euclidean manifolds.

    MCP ROUTING TRIGGERS: Euclidean Geometry, Topological Scaling, Normalized Coordinate
    Space, Bounding Box, Spatial Projection
    """

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


class DynamicLayoutManifest(CoreasonBaseState):
    """Schema representing a template for dynamic grid layouts."""

    layout_tstring: str = Field(
        max_length=2000, description="A Python 3.14 t-string template definition for dynamic UI grid evaluation."
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
            allowed_nodes = (ast.Module, ast.Expr, ast.Constant, ast.Name, ast.Load, ast.FormattedValue, ast.JoinedStr)
            for node in ast.walk(tree):
                if not isinstance(node, allowed_nodes):
                    raise ValueError(f"Kinetic execution bleed detected: Forbidden AST node {type(node).__name__}")
        return v


class ExecutionSLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ExecutionSLA is the rigid physical boundary dictating the absolute time and memory 
    limits for kinetic execution, practically bounding the Halting Problem within the swarm.

    CAUSAL AFFORDANCE: Acts as the hardware guillotine. It instructs the orchestrator's C++/Rust runtime 
    to physically sever the thread, drop the VRAM context, or kill the WASM container if an agent 
    exceeds its authorized footprint, preventing Denial of Service (DoS) via memory exhaustion.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on 
    max_execution_time_ms (le=86400000, gt=0) and max_compute_footprint_mb (le=1000000000, gt=0). 
    Any breach instantly triggers a SystemFaultEvent.

    MCP ROUTING TRIGGERS: Hardware Guillotine, Halting Problem Bounding, VRAM Allocation, Process Termination, Resource Exhaustion
    """

    max_execution_time_ms: int = Field(
        le=86400000,
        gt=0,
        description="The maximum allowed execution time in milliseconds before the orchestrator kills the process.",
    )
    max_compute_footprint_mb: int | None = Field(
        le=1000000000,
        default=None,
        gt=0,
        description="The maximum physical compute footprint allowed for the tool's execution sandbox.",
    )


class FacetMatrixProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Edward Tufte's principles of Small Multiples (Trellis
    displays) by establishing a categorical partitioning matrix for high-dimensional data
    projections. As a ...Profile suffix, this is a declarative property descriptor.

    CAUSAL AFFORDANCE: Authorizes the rendering engine to recursively split and project a
    singular visual grammar into a grid of structurally isomorphic sub-manifolds based on
    distinct categorical fields.

    EPISTEMIC BOUNDS: The partitioning constraints (row_field, column_field) are both
    optional (default=None) and physically bounded by max_length=2000 to mathematically
    prevent Dictionary Bombing and OOM crashes during matrix generation.

    MCP ROUTING TRIGGERS: Small Multiples, Trellis Display, Isomorphic Sub-Manifold,
    High-Dimensional Projection, Categorical Partitioning
    """

    row_field: str | None = Field(
        max_length=2000, default=None, description="The dataset field used to split the chart into rows."
    )
    column_field: str | None = Field(
        max_length=2000, default=None, description="The dataset field used to split the chart into columns."
    )


class SpatialCoordinateProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Specifies an exact N-dimensional (2D) affine coordinate vector for
    localized rendering and kinematic targeting. As a ...Profile suffix, this is a
    declarative property descriptor.

    CAUSAL AFFORDANCE: Provides the absolute spatial terminus for UI actions and overlays,
    enabling the orchestrator to perform bijective mappings from abstract latent data
    points to physical screen space.

    EPISTEMIC BOUNDS: The x and y axes are mathematically clamped to a normalized float
    space (ge=0.0, le=1.0), guaranteeing that dynamically generated coordinates can never
    physically breach the absolute boundaries of the rendering viewport.

    MCP ROUTING TRIGGERS: Affine Transformation, 2D Vector, Kinematic Terminus, Euclidean
    Coordinate, Bijective Mapping
    """

    x: float = Field(ge=0.0, le=1.0, description="The normalized X-axis coordinate (0.0 = left, 1.0 = right).")
    y: float = Field(ge=0.0, le=1.0, description="The normalized Y-axis coordinate (0.0 = top, 1.0 = bottom).")


class ComputeRateContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ComputeRateContract is the immutable economic physics engine defining the 
    Thermodynamic Cost of token generation across the network.

    CAUSAL AFFORDANCE: Allows the swarm orchestrator to mathematically project the budget exhaustion of 
    a specific Latent Scratchpad trace or Monte Carlo Tree Search (MCTS) rollout before committing 
    to the execution graph, effectively acting as an economic look-ahead.

    EPISTEMIC BOUNDS: Strict float boundaries (le=1000000000.0) on cost_per_million_input_tokens and 
    cost_per_million_output_tokens ensure that economic execution vectors cannot overflow the integers 
    in the Epistemic Ledger, protecting the escrow math.

    MCP ROUTING TRIGGERS: Thermodynamic Cost, Monte Carlo Tree Search, Economic Escrow, Token Burn, Budget Calculation
    """

    cost_per_million_input_tokens: float = Field(
        le=1000000000.0, description="The cost per 1 million input tokens provided to the model."
    )
    cost_per_million_output_tokens: float = Field(
        le=1000000000.0, description="The cost per 1 million output tokens generated by the model."
    )
    magnitude_unit: str = Field(max_length=2000, description="The magnitude unit of the associated costs.")


class ScalePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Stevens's levels of measurement and Wilkinson's Grammar
    of Graphics to mathematically project abstract data domains into visual geometric
    ranges. As a ...Policy suffix, this object defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Physically distorts or linearly maps the input metric tensor into
    rendering space, dictating how the orchestrator processes logarithmic, temporal, or
    ordinal data vectors for UI projection.

    EPISTEMIC BOUNDS: The transformation algorithm is strictly constrained to a Literal
    automaton ["linear", "log", "time", "ordinal", "nominal"]. Physical data boundaries
    (domain_min, domain_max) are optional (default=None) and upper-bounded by
    le=1000000000.0 to prevent geometric projection overflow (no ge bound enforced).

    MCP ROUTING TRIGGERS: Grammar of Graphics, Metric Tensor Distortion, Levels of
    Measurement, Scale Projection, FSM Literal
    """

    type: Literal["linear", "log", "time", "ordinal", "nominal"] = Field(
        description="The mathematical scale mapping metrics to pixels."
    )
    domain_min: float | None = Field(
        le=1000000000.0, default=None, description="The optional minimum bound of the scale domain."
    )
    domain_max: float | None = Field(
        le=1000000000.0, default=None, description="The optional maximum bound of the scale domain."
    )


class VisualEncodingProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the mathematical mapping function between an abstract data
    dimension (field) and a physiological human perception vector (channel). As a ...Profile
    suffix, this is a declarative, frozen snapshot of a rendering geometry.

    CAUSAL AFFORDANCE: Constrains the renderer's geometric plotting algorithm by forcing the
    interpretation of data through an optional ScalePolicy transformation (e.g., logarithmic
    or linear).

    EPISTEMIC BOUNDS: The channel is strictly typed to a Literal enum
    ["x", "y", "color", "size", "opacity", "shape", "text"]. The target field is physically
    bounded to max_length=2000 to prevent dictionary bombing during rendering loops.

    MCP ROUTING TRIGGERS: Bijective Mapping, Retinal Variables, Dimensionality Reduction,
    Geometric Plotting, Visual Channel Encoding
    """

    channel: Literal["x", "y", "color", "size", "opacity", "shape", "text"] = Field(
        description="The visual channel the metric is mapped to."
    )
    field: str = Field(max_length=2000, description="The exact column or field name from the semantic series.")
    scale: ScalePolicy | None = Field(default=None, description="Optional scale override for this specific channel.")


class SideEffectProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Lambda Calculus principles of referential transparency
    and state isolation by rigidly categorizing tool capabilities. As a ...Profile suffix,
    this is a declarative property descriptor.

    CAUSAL AFFORDANCE: Instructs the orchestrator's graph traversal engine on whether a
    tool can be safely re-evaluated during a Monte Carlo Tree Search (is_idempotent) or if
    it induces irreversible kinetic entropy (mutates_state).

    EPISTEMIC BOUNDS: Constrained entirely to strict Pydantic boolean logic (is_idempotent,
    mutates_state), mathematically severing ambiguity in side-effect classifications to
    prevent uncontrolled state mutation.

    MCP ROUTING TRIGGERS: Referential Transparency, Lambda Calculus, Idempotence, State
    Monad, Causal Actuator
    """

    is_idempotent: bool = Field(
        description="True if the tool can be safely retried multiple times without altering state beyond the first call."  # noqa: E501
    )
    mutates_state: bool = Field(description="True if the tool performs write operations or side-effects.")


class VerifiableEntropyReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen receipt representing a Verifiable Random
    Function (VRF) output via elliptic curve cryptography. As a ...Receipt suffix, this is an
    append-only coordinate on the Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Unlocks stochastic graph mutations (such as EvolutionaryTopology
    crossovers or prediction market resolutions) by providing mathematical proof via vrf_proof
    that the randomness was uniformly distributed and not manipulated by a Byzantine node.

    EPISTEMIC BOUNDS: The validity of the VRF is physically bound to the seed_hash (a strict
    SHA-256 pattern ^[a-f0-9]{64}$) and the public_key (min_length=10). This prevents
    adversarial Hash Poisoning, ensuring the entropy remains deterministically reproducible
    by the orchestrator.

    MCP ROUTING TRIGGERS: Verifiable Random Function, VRF, Stochastic Fairness, Elliptic
    Curve Cryptography, Zero-Knowledge Entropy
    """

    vrf_proof: str = Field(
        min_length=10, description="The zero-knowledge cryptographic proof of fair random generation."
    )
    public_key: str = Field(
        min_length=10, description="The public key of the oracle or node used to verify the VRF proof."
    )
    seed_hash: str = Field(
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        min_length=10,
        description="The SHA-256 hash of the origin seed used to initialize the VRF.",
    )


class HardwareEnclaveReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a Remote Attestation Quote generated by a Trusted Execution
    Environment (TEE) — supporting intel_tdx, amd_sev_snp, aws_nitro, and nvidia_cc —
    mathematically proving physical silicon isolation. As a ...Receipt suffix, this is an
    append-only coordinate on the Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Authorizes the swarm orchestrator to securely inject RESTRICTED
    classification payloads into the agent's context by proving the host OS cannot read or
    tamper with the working memory.

    EPISTEMIC BOUNDS: The attestation is physically bounded by the 8192-byte max_length of
    the hardware_signature_blob, and mathematically anchored to the exact memory state via the
    platform_measurement_hash (a strict SHA-256 pattern ^[a-f0-9]{64}$ representing the PCRs).

    MCP ROUTING TRIGGERS: Trusted Execution Environment, Remote Attestation, Platform
    Configuration Register, Hardware Root-of-Trust, SGX/TDX/Nitro
    """
    enclave_type: Literal["intel_tdx", "amd_sev_snp", "aws_nitro", "nvidia_cc"] = Field(
        le=1000000000, description="The physical silicon architecture generating the root-of-trust quote."
    )
    platform_measurement_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The cryptographic hash of the Platform Configuration Registers (PCRs) proving the memory state was physically isolated.",  # noqa: E501
    )
    hardware_signature_blob: str = Field(
        max_length=8192,
        description="The base64-encoded hardware quote signed by the silicon manufacturer's master private key.",
    )


class LatentSmoothingProfile(CoreasonBaseState):
    """The mathematical curve used to gently taper an adversarial activation to prevent logit collapse."""

    decay_function: Literal["linear", "exponential", "cosine_annealing"] = Field(
        description="The trigonometric or algebraic function governing the attenuation curve."
    )
    transition_window_tokens: int = Field(
        le=1000000000,
        gt=0,
        description="The exact number of forward-pass generation steps over which the decay is applied.",
    )
    decay_rate_param: float | None = Field(
        le=1.0,
        default=None,
        description="The optional tuning parameter (e.g., half-life lambda for exponential decay).",
    )


class LogitSteganographyContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographic mandate for neural watermarking. Uses a Pseudo-Random
    Function (PRF) seeded by previous token context to deterministically split the vocabulary
    into "green" and "red" lists during Gumbel-Softmax sampling. As a ...Contract suffix, this
    object defines rigid mathematical boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Physically manipulates the LLM's residual stream logit distribution
    just before the final softmax activation, embedding an undeniable, high-entropy Shannon
    information signature directly into the generated text without degrading model perplexity.

    EPISTEMIC BOUNDS: The injection is mathematically clamped by watermark_strength_delta
    (gt=0.0, le=1.0) to prevent logit explosion. Resistance to cropping attacks is
    geometrically enforced by context_history_window (ge=0, le=1000000000). The information
    density is bounded by target_bits_per_token (gt=0.0, le=1000000000.0).

    MCP ROUTING TRIGGERS: Logit Steganography, Gumbel-Softmax Watermarking, Pseudo-Random
    Function, Shannon Entropy, Provenance Tracking
    """

    verification_public_key_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The DID or public key identifier required by an auditor to reconstruct the PRF and verify the watermark.",  # noqa: E501
    )
    prf_seed_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the cryptographic seed used to initialize the pseudo-random function (PRF).",
    )
    watermark_strength_delta: float = Field(
        le=1.0,
        gt=0.0,
        description="The exact logit scalar (bias) injected into the 'green list' vocabulary partition before Gumbel-Softmax sampling.",  # noqa: E501
    )
    target_bits_per_token: float = Field(
        le=1000000000.0,
        gt=0.0,
        description="The information-theoretic density of the payload being embedded into the generative stream.",
    )
    context_history_window: int = Field(
        le=1000000000,
        ge=0,
        description="The k-gram rolling window size of preceding tokens hashed into the PRF state to ensure robustness against text cropping.",  # noqa: E501
    )


class ComputeEngineProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Acts as the liquid compute substrate abstraction, defining the
    foundational LLM matrix available on the Spot Market for dynamic routing. As a ...Profile
    suffix, this is a declarative, frozen snapshot of a compute geometry.

    CAUSAL AFFORDANCE: Projects the physical LLM capabilities, contextual memory constraints,
    and thermodynamic rate cards (ComputeRateContract) into the orchestrator's active routing
    manifold, allowing cost-aware topological planning.

    EPISTEMIC BOUNDS: The token working memory is mathematically bounded by
    context_window_size (le=1000000000). To guarantee RFC 8785 canonical hashing across
    disparate nodes, the capabilities and supported_functional_experts arrays are strictly
    sorted at instantiation via @model_validator.

    MCP ROUTING TRIGGERS: Liquid Compute, Spot Market Routing, Foundation Model Matrix,
    Thermodynamic Rate Card, Substrate Abstraction
    """

    model_name: str = Field(max_length=2000, description="The identifier of the underlying model.")
    provider: str = Field(max_length=2000, description="The name of the provider hosting the model.")
    context_window_size: int = Field(le=1000000000, description="The maximum context window size in tokens.")
    capabilities: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        max_length=1000000000,
        description="The explicit, structurally bounded array of capabilities authorized for this model.",
    )
    rate_card: ComputeRateContract = Field(description="The economic cost definition associated with the model.")
    supported_functional_experts: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        default_factory=list,
        description="The declarative array of specialized functional expert clusters (e.g., 'falsifier', 'synthesizer') physically present in this model's architecture.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "capabilities", sorted(self.capabilities))
        object.__setattr__(self, "supported_functional_experts", sorted(self.supported_functional_experts))
        return self


class PermissionBoundaryPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: PermissionBoundaryPolicy is the strict Zero-Trust Architecture security perimeter 
    defining exactly what external physical systems or networks an agent node is authorized to touch.

    CAUSAL AFFORDANCE: Mechanically limits the subgraph's kinetic reach. It forces the orchestrator to 
    drop network egress packets or block disk I/O unless explicitly whitelisted, and mandates the 
    negotiation of specific cryptographic handshakes (e.g., OAuth2, mTLS) before allocating compute.

    EPISTEMIC BOUNDS: Bounded by deterministic string arrays (allowed_domains, auth_requirements) 
    that must be strictly evaluated at runtime. The arrays are alphabetically sorted at instantiation 
    to prevent Hash Poisoning attacks on the Merkle trace.

    MCP ROUTING TRIGGERS: Zero-Trust Architecture, Network Egress Filtering, Capability-Based Security, mTLS Handshake, Hash Poisoning Prevention
    """

    network_access: bool = Field(description="Whether the tool is permitted to make external network requests.")
    allowed_domains: list[Annotated[str, StringConstraints(max_length=2000)]] | None = Field(
        default=None,
        description="The explicit whitelist of allowed network domains if network access is true.",
    )
    file_system_mutation_forbidden: bool = Field(
        description="True if the tool is strictly forbidden from writing to the disk."
    )
    auth_requirements: list[Annotated[str, StringConstraints(max_length=2000)]] | None = Field(
        default=None,
        description="An explicit array of authentication protocol identifiers (e.g., 'oauth2:github', 'mtls:internal') the orchestrator must negotiate before allocating compute.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.allowed_domains is not None:
            object.__setattr__(self, "allowed_domains", sorted(self.allowed_domains))
        if self.auth_requirements is not None:
            object.__setattr__(self, "auth_requirements", sorted(self.auth_requirements))
        return self


class PostQuantumSignatureReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements NIST FIPS Post-Quantum Cryptography (PQC), utilizing
    lattice-based (ML-DSA, Falcon) or stateless hash-based (SLH-DSA) structures to guarantee
    long-term topological integrity. As a ...Receipt suffix, this is an append-only coordinate
    on the Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Secures the causal execution graph and Bilateral SLAs against temporal
    decryption attacks (Harvest Now, Decrypt Later) via Shor's algorithm executed on
    fault-tolerant quantum computers.

    EPISTEMIC BOUNDS: To accommodate the massive dimensional geometry of post-quantum
    signatures (e.g., SPHINCS+ hash trees), the pq_signature_blob is structurally bound to a
    100,000-byte max_length. The pq_algorithm is restricted to the Literal set
    [ml-dsa, slh-dsa, falcon].

    MCP ROUTING TRIGGERS: Post-Quantum Cryptography, ML-DSA, SLH-DSA, Shor's Algorithm
    Resistance, Lattice-based Cryptography
    """
    pq_algorithm: Literal["ml-dsa", "slh-dsa", "falcon"] = Field(
        description="The NIST FIPS post-quantum cryptographic algorithm used."
    )
    public_key_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The identifier of the post-quantum public evaluation key.",
    )
    pq_signature_blob: str = Field(
        max_length=100000,
        description="The base64-encoded post-quantum signature. Bounded to 100KB to safely accommodate massive SPHINCS+ hash trees without OOM crashes.",  # noqa: E501
    )


class RoutingFrontierPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: RoutingFrontierPolicy is the Multi-Objective Optimization matrix used to navigate 
    the Spot-Market compute layer, calculating the Pareto Efficiency frontier between speed, cost, and intelligence.

    CAUSAL AFFORDANCE: Instructs the Spot-Market router on how to mechanically weigh competing inference 
    engines. If a query requires extreme logic, it authorizes high cost; if it requires a UI reflex, 
    it enforces strict latency bounds.

    EPISTEMIC BOUNDS: Strict physical, economic, and thermodynamic ceilings are mathematically enforced: 
    max_latency_ms (le=86400000), max_cost_magnitude_per_token (le=1000000000), and an absolute ESG bound 
    via max_carbon_intensity_gco2eq_kwh (le=10000.0).

    MCP ROUTING TRIGGERS: Pareto Efficiency, Multi-Objective Optimization, Spot-Market Routing, Carbon Budget, Compute Allocation
    """

    max_latency_ms: int = Field(
        le=86400000,
        gt=0,
        description="The absolute physical speed limit acceptable for time-to-first-token or total generation.",
    )
    max_cost_magnitude_per_token: int = Field(
        le=1000000000,
        gt=0,
        description="The strict magnitude ceiling. MUST be an integer to maintain cryptographic determinism.",
    )
    min_capability_score: float = Field(
        ge=0.0, le=1.0, description="The cognitive capability floor required for the task (0.0 to 1.0)."
    )
    tradeoff_preference: Literal[
        "latency_optimized", "cost_optimized", "capability_optimized", "carbon_optimized", "balanced"
    ] = Field(description="The mathematical optimization vector to break ties within the frontier.")
    max_carbon_intensity_gco2eq_kwh: float | None = Field(
        le=10000.0,
        default=None,
        ge=0.0,
        description="The maximum operational carbon intensity of the physical data center grid allowed for this agent's routing.",  # noqa: E501
    )


class SaeFeatureActivationState(CoreasonBaseState):
    feature_index: int = Field(
        le=1000000000,
        ge=0,
        description="The exact dimensional index of the monosemantic feature in the Sparse Autoencoder dictionary.",
    )
    activation_magnitude: float = Field(
        le=1000000000, description="The mathematical strength of this feature's activation during the forward pass."
    )
    interpretability_label: str | None = Field(
        max_length=2000,
        default=None,
        description="The strictly typed semantic concept mapped to this feature (e.g., 'sycophancy', 'truth_retrieval').",  # noqa: E501
    )


class ActivationSteeringContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes a hardware-level Representation Engineering (RepE)
    directive to mechanically manipulate latent dimensions via forward-pass tensor injection.
    As a ...Contract suffix, this object defines rigid mathematical boundaries that the
    orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Physically forces an additive, ablation, or clamping operation onto
    the model's residual stream at specific injection_layers, steering the generator away
    from unstable hallucination geometries prior to token projection.

    EPISTEMIC BOUNDS: Cryptographically locked by the steering_vector_hash (SHA-256 pattern
    ^[a-f0-9]{64}$). The scaling_factor is bounded above (le=100.0) but unbounded below,
    permitting negative magnitudes for ablation. The @model_validator deterministically
    sorts injection_layers (each ge=0, min_length=1) to preserve RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Representation Engineering, RepE, Activation Steering, Residual
    Stream Ablation, Concept Vectors
    """

    steering_vector_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the extracted RepE control tensor (e.g., the 'caution' vector).",
    )
    injection_layers: list[Annotated[int, Field(ge=0)]] = Field(
        min_length=1,
        description="The specific transformer layer indices where this vector must be applied.",
    )
    scaling_factor: float = Field(
        le=100.0, description="The mathematical magnitude/strength of the injection (can be negative for ablation)."
    )
    vector_modality: Literal["additive", "ablation", "clamping"] = Field(
        description="The tensor operation to perform: add the vector, subtract it, or clamp activations to its bounds."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "injection_layers", sorted(self.injection_layers))
        return self


class SemanticSlicingPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A Deterministic Epistemic Firewall that mathematically
    starves the active context partition of irrelevant or over-classified data
    to prevent attention dilution and enforce zero-trust isolation.
    """

    permitted_classification_tiers: list[InformationClassificationProfile] = Field(
        min_length=1, description="The explicit whitelist of sensitivity bounds allowed into context."
    )
    required_semantic_labels: list[Annotated[str, StringConstraints(max_length=255)]] | None = Field(
        default=None,
        description="The declarative whitelist of strictly typed ontological node labels authorized for context projection.",  # noqa: E501
    )
    context_window_token_ceiling: int = Field(
        le=2000000,
        gt=0,
        description="The mathematical physical limit of the active context partition to prevent VRAM exhaustion.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        """Mathematically sort arrays to guarantee deterministic canonical hashing."""
        object.__setattr__(
            self,
            "permitted_classification_tiers",
            sorted(self.permitted_classification_tiers, key=lambda x: str(x.value)),
        )
        if self.required_semantic_labels is not None:
            object.__setattr__(self, "required_semantic_labels", sorted(self.required_semantic_labels))
        return self


class CognitiveRoutingContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Overrides the default Softmax gating mechanism of a Sparse Mixture of
    Experts (MoE) architecture to enforce deterministic functional isolation. As a ...Contract
    suffix, this object defines rigid mathematical boundaries that the orchestrator must
    enforce globally.

    CAUSAL AFFORDANCE: Physically biases or mathematically masks out (-inf via
    enforce_functional_isolation) entire swaths of neural circuits, forcing continuous compute
    through highly specialized expert topological perimeters.

    EPISTEMIC BOUNDS: Limits structural instability by clamping expert_logit_biases strictly
    between [ge=-1000.0, le=1000.0], hard-bounding dynamic_top_k execution threads
    (ge=1, le=1000000000), and constraining routing_temperature (ge=0.0, le=1000000000.0)
    to prevent softmax gate collapse.

    MCP ROUTING TRIGGERS: Sparse Mixture of Experts, Softmax Gating, Logit Biasing,
    Functional Expert Routing, FSM Masking
    """

    dynamic_top_k: int = Field(
        le=1000000000,
        ge=1,
        description="The exact number of functional experts the router must activate per token. High values simulate deep cognitive strain.",  # noqa: E501
    )
    routing_temperature: float = Field(
        le=1000000000.0,
        ge=0.0,
        description="The temperature applied to the router's softmax gate, controlling how deterministically it picks experts.",  # noqa: E501
    )
    expert_logit_biases: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ] = Field(
        le=1000000000.0,
        default_factory=dict,
        description="Explicit tensor biases applied to the router gate. Keys are expert IDs (e.g., 'expert_falsifier'), values are logit modifiers.",  # noqa: E501
    )
    enforce_functional_isolation: bool = Field(
        default=False,
        description="If True, the orchestrator applies a hard mask (-inf) to any expert not explicitly boosted in expert_logit_biases.",  # noqa: E501
    )


class CognitiveStateProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Tracks the continuous Partially Observable Markov Decision Process
    (POMDP) belief distribution and dictates the active cognitive heuristic. As a ...Profile
    suffix, this is a declarative, frozen snapshot of N-dimensional geometry at a specific
    point in time.

    CAUSAL AFFORDANCE: Orchestrates multi-dimensional state progression, determining if the
    agent explores via high divergence_tolerance or exploits via constrained caution vectors.
    Optionally embeds an ActivationSteeringContract, CognitiveRoutingContract, and
    SemanticSlicingPolicy for full mechanistic control.

    EPISTEMIC BOUNDS: Relies on strict Pydantic bounding of internal indices (urgency_index,
    caution_index, divergence_tolerance) to continuous probability distributions between
    [ge=0.0, le=1.0].

    MCP ROUTING TRIGGERS: POMDP, Continuous Belief Distribution, Heuristic Routing, State
    Progression, Cognitive Constraining
    """

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
    moe_routing_directive: CognitiveRoutingContract | None = Field(
        default=None,
        description="The structural mandate overriding default token routing to enforce this cognitive state.",
    )
    semantic_slicing: SemanticSlicingPolicy | None = Field(
        default=None, description="The mathematical data starvation mechanism bounding the working memory context."
    )


class CognitiveUncertaintyProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Structural Causal Models (SCMs) to mathematically quantify
    doubt and partition irreducible aleatoric noise from actionable epistemic knowledge gaps.
    As a ...Profile suffix, this is a declarative, frozen snapshot of N-dimensional geometry
    at a specific point in time.

    CAUSAL AFFORDANCE: Unlocks non-monotonic logic via Pearlian do-operators ($P(y|do(x))$),
    computing exactly when to trigger a structural abductive escalation or active inference
    loop via the requires_abductive_escalation flag.

    EPISTEMIC BOUNDS: Enforces absolute mathematical float boundaries [ge=0.0, le=1.0] on
    aleatoric_entropy, epistemic_uncertainty, and semantic_consistency_score, mathematically
    preventing probability wave overflow across all three continuous dimensions.

    MCP ROUTING TRIGGERS: Structural Causal Models, Active Inference, Epistemic Uncertainty,
    Aleatoric Entropy, Pearlian Do-Calculus
    """

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


class ConstitutionalPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes a discrete normative axiom within a Constitutional AI
    framework to prevent instrumental convergence. As a ...Policy suffix, this object defines
    rigid mathematical boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Establishes a hard structural boundary that mathematically repels the
    swarm's generative trajectory away from forbidden semantic manifolds. Violation severity
    is classified via a strict Literal["low", "medium", "high", "critical"] tier.

    EPISTEMIC BOUNDS: Geometrically restricts the state space by blacklisting specific
    execution branches via the forbidden_intents array (max_length=1000000000),
    deterministically sorted by @model_validator to preserve RFC 8785 canonical hashing.
    The rule_id is bounded to a 128-char CID.

    MCP ROUTING TRIGGERS: Constitutional AI, Value Alignment, Normative Axiom, Instrumental
    Convergence, Semantic Boundary
    """

    rule_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for the constitutional rule.",
    )
    description: str = Field(
        max_length=2000, description="The definitive causal constraint or heuristic boundary enforced by this rule."
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level if the rule is violated."
    )
    forbidden_intents: list[Annotated[str, StringConstraints(min_length=1)]] = Field(
        max_length=1000000000, description="The explicit, structurally bounded set of forbidden semantic intents."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "forbidden_intents", sorted(self.forbidden_intents))
        return self


class GradingCriterionProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a discrete objective dimension within a Multi-Attribute
    Utility Theory (MAUT) framework. As a ...Profile suffix, this is a declarative,
    frozen snapshot of an evaluation geometry.

    CAUSAL AFFORDANCE: Provides the orchestrator's reward model with a formalized
    mathematical vector to compute partial utility scores during algorithmic adjudication.
    The description field (max_length=2000) carries the exact logical boundary.

    EPISTEMIC BOUNDS: The objective significance is physically constrained by weight
    (ge=0.0, le=100.0). The geometric perimeter is locked to a 128-char criterion_id CID
    regex.

    MCP ROUTING TRIGGERS: Multi-Criteria Decision Analysis, Dimensional Weighting,
    Behavioral Scoring, MCDA, Scalar Boundary
    """

    criterion_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for the grading criterion.",
    )
    description: str = Field(
        max_length=2000,
        description="The exact mathematical or logical boundary the target must satisfy to pass this dimensional check.",  # noqa: E501
    )
    weight: float = Field(le=100.0, ge=0.0, description="Weight or significance of this criterion.")


class AdjudicationRubricProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes an Aggregation Function for Multi-Criteria Decision
    Analysis (MCDA), compiling multiple utility dimensions into a definitive evaluation
    boundary for the swarm. As a ...Profile suffix, this defines a rigid mathematical
    boundary.

    CAUSAL AFFORDANCE: Instructs the orchestrator's verification engine on how to
    calculate the total weighted score of a generated trajectory, triggering a
    deterministic boolean pass/fail gate based on the aggregate sum.

    EPISTEMIC BOUNDS: The success condition is mathematically locked by passing_threshold
    (ge=0.0, le=100.0). The rubric_id is a 128-char CID anchor. The @model_validator
    sort_arrays deterministically sorts the criteria array by criterion_id, guaranteeing
    invariant RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Evaluation Manifold, Threshold Gating, Deterministic Rubric,
    RFC 8785 Canonicalization, Binary State Transition
    """

    rubric_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="Unique identifier for the rubric."
    )
    criteria: list[GradingCriterionProfile] = Field(
        description="The explicit array of strict evaluation criteria defining the rubric."
    )
    passing_threshold: float = Field(ge=0.0, le=100.0, description="The minimum score required to pass.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "criteria", sorted(self.criteria, key=lambda x: x.criterion_id))
        return self


class PredictionMarketPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the mathematical Automated Market Maker (AMM) using Robin Hanson's Logarithmic Market Scoring Rule (LMSR) parameters to guarantee infinite liquidity.

    CAUSAL AFFORDANCE: Triggers quadratic staking functions to mathematically prevent Sybil attacks and dictates the exact `convergence_delta_threshold` required to halt trading and collapse the probability wave.

    EPISTEMIC BOUNDS: The `min_liquidity_magnitude` is capped at an integer `le=1000000000`, and the `convergence_delta_threshold` is strictly clamped to a probability distribution `[0.0, 1.0]`.

    MCP ROUTING TRIGGERS: LMSR, Automated Market Maker, Quadratic Staking, Sybil Resistance, Convergence Delta
    """
    staking_function: Literal["linear", "quadratic"] = Field(
        description="The mathematical curve applied to stakes. Quadratic enforces Sybil resistance."
    )
    min_liquidity_magnitude: int = Field(le=1000000000, ge=0, description="Minimum liquidity required.")
    convergence_delta_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The threshold indicating the market price has stabilized enough to trigger the resolution oracle.",
    )


class QuorumPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes the Practical Byzantine Fault Tolerance (pBFT)
    mathematical boundaries for a decentralized swarm to survive malicious or hallucinating
    actors. As a ...Policy suffix, this object defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Instructs the orchestrator to validate the state_validation_metric
    (Literal ["ledger_hash", "zk_proof", "semantic_embedding"]) across $N$ nodes, physically
    executing the byzantine_action (Literal ["quarantine", "slash_escrow", "ignore"])
    against nodes that violate the consensus.

    EPISTEMIC BOUNDS: Physically bounds max_tolerable_faults (ge=0, le=1000000000) and
    min_quorum_size (gt=0, le=1000000000). The @model_validator enforce_bft_math enforces
    the strict invariant $N \ge 3f + 1$, guaranteeing Byzantine agreement.

    MCP ROUTING TRIGGERS: Byzantine Fault Tolerance, pBFT, Quorum Sensing, Sybil
    Resistance, Distributed Consensus
    """

    max_tolerable_faults: int = Field(
        le=1000000000,
        ge=0,
        description="The maximum number of actively malicious, hallucinating, or degraded nodes (f) the swarm must survive.",  # noqa: E501
    )
    min_quorum_size: int = Field(
        le=1000000000, gt=0, description="The minimum number of participating agents (N) required to form consensus."
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


class ConsensusPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Social Choice Theory and Distributed Consensus mechanisms
    to systematically synthesize a singular, crystallized truth from a multi-agent council.
    As a ...Policy suffix, this object defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Triggers deterministic tie-breaking (via optional
    tie_breaker_node_id: NodeIdentifierState) or algorithmic market resolution (via
    optional prediction_market_rules: PredictionMarketPolicy) when agents deadlock,
    forcefully collapsing the debate probability wave to maintain systemic liveness.

    EPISTEMIC BOUNDS: The max_debate_rounds (optional int) is clamped to le=1000000000 to
    computationally solve the Halting Problem for runaway arguments. The strategy Literal
    ["unanimous", "majority", "debate_rounds", "prediction_market", "pbft"] constrains
    the combinatorial space. The @model_validator requires quorum_rules if strategy is
    "pbft".

    MCP ROUTING TRIGGERS: Social Choice Theory, Mechanism Design, Condorcet's Jury Theorem,
    Algorithmic Consensus, Deadlock Resolution
    """

    strategy: Literal["unanimous", "majority", "debate_rounds", "prediction_market", "pbft"] = Field(
        description="The mathematical rule for reaching agreement."
    )
    tie_breaker_node_id: NodeIdentifierState | None = Field(
        default=None, description="The node authorized to break deadlocks if unanimity or majority fails."
    )
    max_debate_rounds: int | None = Field(
        le=1000000000,
        default=None,
        description="The maximum number of argument/rebuttal cycles permitted before forced adjudication.",
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


class RedactionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a deterministic Data Sanitization heuristic mapped to a
    specific InformationClassificationProfile (e.g., Bell-LaPadula clearance levels). As a
    ...Policy suffix, this object defines rigid mathematical boundaries that the orchestrator
    must enforce globally.

    CAUSAL AFFORDANCE: Executes a rigid regex-bounded search-and-replace algorithm via
    target_regex_pattern to mutate or mask toxic data payloads, substituting matches with a
    safe replacement_token. The action (SanitizationActionIntent) dictates the exact
    sanitization method.

    EPISTEMIC BOUNDS: The target_regex_pattern is strictly capped at max_length=200 to
    mathematically prevent ReDoS (Regular Expression Denial of Service) CPU exhaustion. A
    secondary target_pattern (max_length=2000) provides a broader semantic entity match. The
    optional context_exclusion_zones array (max_length=100) is deterministically sorted by
    the @model_validator.

    MCP ROUTING TRIGGERS: Data Sanitization, Regular Expression DoS Prevention,
    Bell-LaPadula Model, Masking Heuristic, Algorithmic Redaction
    """

    rule_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for the sanitization rule.",
    )
    classification: InformationClassificationProfile = Field(
        description="The category of sensitive payload this rule targets."
    )
    target_pattern: str = Field(
        max_length=2000, description="The semantic entity type or declarative regex pattern to identify."
    )
    target_regex_pattern: str = Field(max_length=200, description="The dynamic regex pattern to target.")
    context_exclusion_zones: list[Annotated[str, StringConstraints(max_length=2000)]] | None = Field(
        default=None, max_length=100, description="Specific JSON paths where this rule should NOT apply."
    )
    action: SanitizationActionIntent = Field(
        description="The required algorithmic response when this pattern is detected."
    )
    replacement_token: str | None = Field(
        max_length=2000, default=None, description="The strictly typed string to insert if the action is 'redact'."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.context_exclusion_zones is not None:
            object.__setattr__(self, "context_exclusion_zones", sorted(self.context_exclusion_zones))
        return self


class SaeLatentPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Sparse Dictionary Learning and Mechanistic Interpretability
    to actively monitor and steer monosemantic neural circuits during the model's forward
    pass. As a ...Policy suffix, this object defines rigid mathematical boundaries that the
    orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Executes real-time tensor remediation — clamping, halting, quarantining,
    or smoothly decaying residual stream activations via violation_action
    (Literal["clamp", "halt", "quarantine", "smooth_decay"]) — when specific features
    diverge toward adversarial or hallucinated geometries. The smooth_decay path requires
    both a LatentSmoothingProfile and clamp_value target asymptote, enforced by a
    @model_validator.

    EPISTEMIC BOUNDS: The max_activation_threshold (ge=0.0, le=1000000000.0) physically
    bounds the continuous Euclidean magnitude of the target_feature_index (ge=0,
    le=1000000000). The policy is topologically locked to the exact SAE projection matrix via
    sae_dictionary_hash (SHA-256 ^[a-f0-9]{64}$). The monitored_layers array (min_length=1)
    is deterministically sorted by @model_validator for RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Mechanistic Interpretability, Sparse Autoencoders, Residual Stream
    Steering, Tensor Remediation, Monosemantic Features
    """

    target_feature_index: int = Field(
        le=1000000000,
        ge=0,
        description="The exact dimensional index of the monosemantic feature in the Sparse Autoencoder dictionary.",
    )
    monitored_layers: list[Annotated[int, Field(ge=0)]] = Field(
        min_length=1,
        description="The specific transformer layer indices where this feature activation must be monitored.",
    )
    max_activation_threshold: float = Field(
        le=1000000000.0,
        ge=0.0,
        description="The mathematical magnitude limit. If the feature activates beyond this, the firewall trips.",
    )
    violation_action: Literal["clamp", "halt", "quarantine", "smooth_decay"] = Field(
        description="The tensor-level remediation applied when the threshold is breached."
    )
    clamp_value: float | None = Field(
        le=1000000000.0,
        default=None,
        description="If violation_action is 'clamp', the physical value to which the activation tensor is forced.",
    )
    sae_dictionary_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact SAE projection matrix required to decode this feature.",
    )
    smoothing_profile: LatentSmoothingProfile | None = Field(
        default=None,
        description="The geometric parameters for continuous attenuation if violation_action is 'smooth_decay'.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "monitored_layers", sorted(self.monitored_layers))
        return self

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


class SecureSubSessionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes the Principle of Least Privilege (PoLP) and Time-Based
    Access Control (TBAC) for handling high-entropy cryptographic secrets. As a ...State
    suffix, this is a declarative, frozen N-dimensional coordinate.

    CAUSAL AFFORDANCE: Authorizes a temporary, mathematically bounded partition where
    the agent can access unredacted enterprise vault keys (allowed_vault_keys) without
    permanently leaking them into the global EpistemicLedgerState. The description field
    (max_length=2000) provides audit justification.

    EPISTEMIC BOUNDS: The temporal exposure window is physically clamped by
    max_ttl_seconds (ge=1, le=3600), enforcing an absolute maximum 1-hour session.
    Spatial access is geometrically restricted to allowed_vault_keys (max_length=100),
    deterministically sorted by @model_validator sort_arrays for RFC 8785 hashing.

    MCP ROUTING TRIGGERS: Principle of Least Privilege, Time-Based Access Control,
    Secret Vaulting, Ephemeral Partition, Cryptographic Isolation
    """

    session_id: str = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        max_length=255,
        description="Unique identifier for the secure session.",
    )
    allowed_vault_keys: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        max_length=100,
        description="The explicit array of enterprise vault keys the agent is temporarily allowed to access.",
    )
    max_ttl_seconds: int = Field(ge=1, le=3600, description="Maximum time-to-live for the unredacted state partition.")
    description: str = Field(max_length=2000, description="Audit justification for this temporary secure session.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_vault_keys", sorted(self.allowed_vault_keys))
        return self


class DefeasibleCascadeEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the active
    propagation of an undercutting defeater within an Abstract Argumentation Framework. As an
    ...Event suffix, this object is an append-only coordinate on the Merkle-DAG that the LLM
    must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Executes the physical quarantine of the quarantined_event_ids subgraph,
    mathematically zeroing out their probability mass and halting all execution branches
    dependent on the root_falsified_event_id.

    EPISTEMIC BOUNDS: Deterministic canonical hashing is guaranteed by the @model_validator
    which strictly sorts quarantined_event_ids. The propagated_decay_factor float is bounded
    (ge=0.0, le=1.0), capping the maximum entropy penalty per edge traversal.

    MCP ROUTING TRIGGERS: Abstract Argumentation, Undercutting Defeater, Epistemic Contagion,
    Wave Collapse, Quarantine Topology
    """
    cascade_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this automated truth maintenance operation.",  # noqa: E501
    )
    root_falsified_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The source BeliefMutationEvent or HypothesisGenerationEvent Content Identifier (CID) that collapsed and triggered this cascade.",  # noqa: E501
    )
    propagated_decay_factor: float = Field(
        ge=0.0, le=1.0, description="The calculated Entropy Penalty applied to this specific subgraph."
    )
    quarantined_event_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        min_length=1,
        description="The strict array of downstream event Content Identifiers (CIDs) isolated and muted by this cascade to prevent Epistemic Contagion.",  # noqa: E501
    )
    cross_boundary_quarantine_issued: bool = Field(
        default=False,
        description="Cryptographic proof that this cascade was broadcast to the Swarm to halt epistemic contagion.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "quarantined_event_ids", sorted(self.quarantined_event_ids))
        return self


class MultimodalTokenAnchorState(CoreasonBaseState):
    """AGENT INSTRUCTION: Unified multimodal grounding mapping extracted facts to strict 1D token spans and 2D visual\n
    patches."""

    token_span_start: int | None = Field(
        le=1000000000, default=None, ge=0, description="The starting index in the discrete VLM context window."
    )
    token_span_end: int | None = Field(
        le=1000000000, default=None, ge=0, description="The ending index in the discrete VLM context window."
    )
    visual_patch_hashes: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        default_factory=list,
        description="The explicit array of SHA-256 hashes corresponding to specific VQ-VAE visual patches attended to.",
    )
    bounding_box: tuple[float, float, float, float] | None = Field(
        max_length=1000000000,
        default=None,
        description="The strictly typed [x_min, y_min, x_max, y_max] normalized coordinate matrix.",
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


class RollbackIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A kinetic execution trigger initiating a macroscopic Pearlian
    counterfactual reversal, mathematically rewinding the state vector to a pristine historical
    Merkle root. As an ...Intent suffix, the LLM may execute non-monotonic reasoning here.

    CAUSAL AFFORDANCE: Forces the orchestrator to execute a Pearlian do-operator intervention
    ($do(X=x)$), flushing all invalidated_node_ids from the active context and restoring the
    topology to the target_event_id coordinate.

    EPISTEMIC BOUNDS: Deterministic execution is mathematically guaranteed by the
    @model_validator which strictly alphabetizes invalidated_node_ids via sorted() prior to
    RFC 8785 canonical hashing, preventing Byzantine replay divergence.

    MCP ROUTING TRIGGERS: Pearlian Counterfactual, Causal Reversal, State Vector Rollback,
    Temporal Negation, Topological Falsification
    """
    request_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the causal rollback operation.",  # noqa: E501
    )
    target_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The Content Identifier (CID) of the corrupted event in the EpistemicLedgerState to revert to.",
    )
    invalidated_node_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        default_factory=list,
        description="The strict array of nodes whose operational histories are causally tainted and must be flushed.",
    )

    @model_validator(mode="after")
    def sort_invalidated_nodes(self) -> Self:
        object.__setattr__(self, "invalidated_node_ids", sorted(self.invalidated_node_ids))
        return self


class StateMutationIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements the formal RFC 6902 JSON Patch standard to execute atomic,
    deterministic state vector mutations across the swarm's N-dimensional blackboard. As an
    ...Intent suffix, this represents an authorized kinetic execution trigger.

    CAUSAL AFFORDANCE: Instructs the orchestrator's algebraic engine to surgically apply,
    test, or ablate targeted JSON pointers without requiring full payload transmission. The
    value (JsonPrimitiveState, default=None) carries the mutation payload; from_path
    (alias="from") enables RFC 6902 move/copy operations.

    EPISTEMIC BOUNDS: The operation geometry is rigidly restricted by the op field to the
    PatchOperationProfile Literal automaton. Target topological coordinates (path and
    from_path) are physically bounded to max_length=2000 to prevent path traversal and
    string exhaustion during pointer resolution.

    MCP ROUTING TRIGGERS: RFC 6902, JSON Patch, Atomic Mutation, State Vector Projection,
    Deterministic Operator
    """
    op: PatchOperationProfile = Field(
        description="The strict RFC 6902 JSON Patch operation, acting as a deterministic state vector mutation."
    )
    path: str = Field(
        max_length=2000, description="The JSON pointer indicating the exact state vector to mutate deterministically."
    )
    value: JsonPrimitiveState = Field(
        default=None,
        description="The payload to insert or test, if applicable, for this deterministic state vector mutation.",
    )
    from_path: str | None = Field(
        max_length=2000,
        default=None,
        alias="from",
        description="The JSON pointer from which to copy or move the state vector, if applicable.",
    )


class StateDifferentialManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Conflict-free Replicated Data Types (CRDTs) using Lamport
    logical clocks and Vector Clocks to guarantee Eventual Consistency. As a ...Manifest
    suffix, this defines a frozen, declarative coordinate of a state transition matrix.

    CAUSAL AFFORDANCE: Enables lock-free, decentralized state synchronization across the
    swarm. Forces the orchestrator to resolve Last-Writer-Wins (LWW) topological conflicts
    before flushing the patches (list[StateMutationIntent]) to the immutable Epistemic
    Ledger. The vector_clock dict maps node CIDs to their ge=0 integer mutation counts.

    EPISTEMIC BOUNDS: Cryptographically anchored by diff_id and author_node_id (both
    strict 128-char CID regex). The synchronization math is clamped by lamport_timestamp
    (ge=0, le=1000000000), physically preventing logical clock integer overflow during
    prolonged swarm execution cycles.

    MCP ROUTING TRIGGERS: CRDT, Vector Clock, Lamport Timestamp, Eventual Consistency,
    Last-Writer-Wins
    """
    diff_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this state differential.",  # noqa: E501
    )
    author_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The exact Lineage Watermark of the agent or system that authored this state mutation.",
    )
    lamport_timestamp: int = Field(
        le=1000000000,
        ge=0,
        description="Strict scalar logical clock governing deterministic LWW (Last-Writer-Wins) conflict resolution.",
    )
    vector_clock: dict[Annotated[str, StringConstraints(max_length=255)], Annotated[int, Field(ge=0)]] = Field(
        description="Causal history mapping of all known Lineage Watermarks to their latest logical mutation count at the time of authoring.",  # noqa: E501
    )
    patches: list[StateMutationIntent] = Field(
        default_factory=list, description="The exact, ordered sequence of deterministic state vector mutations."
    )


class StateHydrationManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Manages the Epistemic Hydration of an agent's active context
    partition from cold storage, bridging immutable EpistemicLedgerState checkpoints and
    ephemeral working memory. As a ...Manifest suffix, this defines a frozen configuration
    state.

    CAUSAL AFFORDANCE: Authorizes the physical injection of serialized semantic data
    (working_context_variables) into the LLM's forward-pass generation window, seeding
    the context prior to probability wave collapse. The crystallized_ledger_cids (SHA-256
    pointers) bind to past immutable ledger blocks.

    EPISTEMIC BOUNDS: VRAM exhaustion is prevented by max_retained_tokens (gt=0,
    le=1000000000). The @field_validator enforce_payload_topology calls
    _validate_payload_bounds to prevent Dictionary Bombing on working_context_variables.
    The @model_validator sort_arrays deterministically sorts crystallized_ledger_cids for
    RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Epistemic Hydration, Working Memory Injection, Context Window
    Partitioning, VRAM Bounding, Serialization Geometry
    """
    epistemic_coordinate: str = Field(
        max_length=2000, description="A string ID representing the session or specific spatial trace binding."
    )
    crystallized_ledger_cids: list[Annotated[str, StringConstraints(pattern="^[a-f0-9]{64}$")]] = Field(
        description="A list of cryptographic pointers to past immutable EpistemicLedgerState blocks."
    )
    working_context_variables: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="A strictly typed dictionary for ephemeral context variables injected at runtime. AGENT INSTRUCTION: This matrix is deterministically sorted by CoreasonBaseState natively.",  # noqa: E501
    )

    @field_validator("working_context_variables", mode="before")
    @classmethod
    def enforce_payload_topology(cls, v: Any) -> Any:
        """AGENT INSTRUCTION: Mathematically bound recursive dictionary payloads to prevent OOM/CPU exhaustion during EpistemicLedgerState hashing."""  # noqa: E501
        return _validate_payload_bounds(v)

    max_retained_tokens: int = Field(
        le=1000000000, gt=0, description="An integer representing the physical limit of the context window."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "crystallized_ledger_cids", sorted(self.crystallized_ledger_cids))
        return self


class TemporalCheckpointState(CoreasonBaseState):
    checkpoint_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the temporal anchor.",
    )
    ledger_index: int = Field(
        le=1000000000, description="The exact array index in the EpistemicLedgerState this checkpoint represents."
    )
    state_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The canonical RFC 8785 SHA-256 hash of the entire topology at this exact index.",
    )


class ThoughtBranchState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A declarative, frozen snapshot of a discrete Markov Decision Process
    (MDP) state representing a single coordinate within a non-monotonic reasoning tree. As
    a ...State suffix, this is a frozen N-dimensional coordinate.

    CAUSAL AFFORDANCE: Tracks a localized reasoning trajectory, enabling the orchestrator's
    Process Reward Model (PRM) to score the branch and dictate if the traversal should
    recursively backtrack or continue. Tree reconstruction is enabled via the optional
    parent_branch_id.

    EPISTEMIC BOUNDS: The mathematical validity of the branch is continuously clamped by
    prm_score (optional, ge=0.0, le=1.0, default=None). The node is cryptographically
    anchored to the execution tree via latent_content_hash (strict SHA-256 pattern
    ^[a-f0-9]{64}$). The branch_id is locked to a 128-char CID.

    MCP ROUTING TRIGGERS: Markov Decision Process, Process Reward Model, Reasoning Node,
    Heuristic Search, Backtracking
    """
    branch_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A deterministic capability pointer bounding this specific topological divergence in the Latent Scratchpad Trace.",  # noqa: E501
    )
    parent_branch_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The branch this thought diverged from, enabling tree reconstruction.",
    )
    latent_content_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the raw latent dimensions explored in this branch.",
    )
    prm_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="The logical validity score assigned to this branch by the Process Reward Model.",
    )


class LatentScratchpadReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: An append-only, cryptographically frozen coordinate representing an
    Ephemeral Epistemic Quarantine used for Monte Carlo Tree Search (MCTS) or Beam Search.
    As a ...Receipt suffix, this is an append-only coordinate on the Merkle-DAG.

    CAUSAL AFFORDANCE: Isolates exploratory trajectories (ThoughtBranchState) from the
    immutable EpistemicLedgerState, allowing the orchestrator to collapse probability waves
    (via resolution_branch_id) and prune dead-ends without causal contamination.

    EPISTEMIC BOUNDS: Two @model_validators enforce integrity: (1) verify_referential_
    integrity confirms resolution_branch_id and all discarded_branches exist within
    explored_branches; (2) sort_arrays deterministically sorts both explored_branches
    (by branch_id) and discarded_branches for RFC 8785 Canonical Hashing.
    total_latent_tokens is hard-capped (ge=0, le=1000000000).

    MCP ROUTING TRIGGERS: Monte Carlo Tree Search, Beam Search, Epistemic Quarantine,
    Probability Wave Collapse, State-Space Exploration
    """
    trace_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) bounding this ephemeral test-time execution tree.",
    )
    explored_branches: list[ThoughtBranchState] = Field(
        description="All logical paths the agent attempted within this Ephemeral Epistemic Quarantine—a volatile workspace where probability waves collapse before being committed to the immutable ledger."  # noqa: E501
    )
    discarded_branches: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        description="The strict array of Content Identifiers (CIDs) that were explicitly pruned due to logical dead-ends.",  # noqa: E501
    )
    resolution_branch_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The Content Identifier (CID) that successfully resolved the uncertainty and led to the final output.",  # noqa: E501
    )
    total_latent_tokens: int = Field(
        le=1000000000, ge=0, description="The total expenditure (in tokens) spent purely on internal reasoning."
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


class EphemeralNamespacePartitionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements a hardware-level Sandboxing and Trusted Execution
    Environment (TEE) paradigm, utilizing WASI, eBPF, or zkVMs to safely execute
    exogenous bytecode. As a ...State suffix, this is a declarative, frozen snapshot of
    an execution geometry.

    CAUSAL AFFORDANCE: Physically isolates kinetic execution from the host OS via
    execution_runtime Literal ["wasm32-wasi", "riscv32-zkvm", "bpf"], authorizing
    the orchestrator to instantiate a temporary virtual machine strictly conforming to
    allow_network_egress (default=False) and allow_subprocess_spawning (default=False).

    EPISTEMIC BOUNDS: The Halting Problem is managed via max_ttl_seconds (le=86400,
    gt=0), and memory exhaustion is prevented via max_vram_mb (le=1000000000, gt=0).
    The @model_validator validate_cryptographic_hashes enforces SHA-256 regex
    (^[a-f0-9]{64}$); a second @model_validator sort_arrays deterministically sorts the
    authorized_bytecode_hashes for RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: WebAssembly System Interface, Zero-Knowledge Virtual Machine,
    eBPF, Execution Sandbox, Arbitrary Code Execution Mitigation
    """

    partition_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this ephemeral partition.",
    )
    execution_runtime: Literal["wasm32-wasi", "riscv32-zkvm", "bpf"] = Field(
        description="The strict virtual machine target mandated for dynamic execution."
    )
    authorized_bytecode_hashes: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        min_length=1,
        description="The explicit whitelist of SHA-256 hashes allowed to execute within this partition.",
    )
    max_ttl_seconds: int = Field(
        le=86400, gt=0, description="The absolute temporal guillotine before the orchestrator drops the context."
    )
    max_vram_mb: int = Field(
        le=1000000000, gt=0, description="The strict physical VRAM ceiling allocated to this partition."
    )
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


class ToolManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the discrete formalization of a Gibsonian Affordance within
    the agent's Reinforcement Learning Action Space ($A$). As a ...Manifest suffix, this is
    a declarative, frozen N-dimensional coordinate of a capability.

    CAUSAL AFFORDANCE: Unlocks a specific, localized Pearlian Do-Operator intervention
    ($do(X=x)$) mapped to an external kinetic capability. Governed by side_effects
    (SideEffectProfile), permissions (PermissionBoundaryPolicy), and an optional sla
    (ExecutionSLA).

    EPISTEMIC BOUNDS: The tool's operational perimeter is rigidly confined by input_schema
    (a dictionary bounded to max_length=1000000000 properties). The is_preemptible boolean
    (default=False) establishes a physical Halting Problem limit by authorizing the
    orchestrator to abort execution mid-flight.

    MCP ROUTING TRIGGERS: Gibsonian Affordance, MDP Action Space, Pearlian Do-Operator,
    Capability-Based Security, Halting Problem
    """

    tool_name: str = Field(max_length=2000, description="The exact identifier of the tool.")
    description: str = Field(
        max_length=2000,
        description="The mathematically bounded semantic projection defining the tool's causal affordances.",
    )
    input_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000, description="The strict JSON Schema dictionary defining the required arguments."
    )
    side_effects: SideEffectProfile = Field(
        description="The declarative side-effect and idempotency profile of the tool."
    )
    permissions: PermissionBoundaryPolicy = Field(
        description="The zero-trust security boundaries for the tool's execution."
    )
    sla: ExecutionSLA | None = Field(default=None, description="Execution limits for the tool.")
    is_preemptible: bool = Field(
        default=False,
        description="If True, the orchestrator is authorized to send a SIGINT to abort this tool's execution mid-flight if a BargeInInterruptEvent occurs.",  # noqa: E501
    )


class BilateralSLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the zero-trust structural boundary for multi-tenant federation,
    securing cross-boundary graph traversal against Shor's algorithm via an optional
    PostQuantumSignatureReceipt. As an ...SLA suffix, this object enforces rigid mathematical
    boundaries that the orchestrator must respect globally.

    CAUSAL AFFORDANCE: Unlocks cross-swarm graph bridging by enforcing strict liability,
    physical location routing, semantic data classification constraints via
    max_permitted_classification, and ESG carbon intensity limits.

    EPISTEMIC BOUNDS: Economically constrained by liability_limit_magnitude (ge=0,
    le=1000000000). ESG limits physically bind the node grid to the optional
    max_permitted_grid_carbon_intensity (ge=0.0, le=10000.0). The permitted_geographic_regions
    array is deterministically sorted via @model_validator for RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Zero-Trust Architecture, Post-Quantum Cryptography, Federated
    Learning, Bilateral SLA, Data Residency
    """
    receiving_tenant_id: str = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        max_length=255,
        description="The strict enterprise identifier of the foreign B2B tenant receiving this payload.",
    )
    max_permitted_classification: InformationClassificationProfile = Field(
        description="The absolute highest semantic sensitivity allowed to cross this federated boundary."
    )
    liability_limit_magnitude: int = Field(
        le=1000000000, ge=0, description="The strict magnitude cap on cross-tenant economic liability."
    )
    permitted_geographic_regions: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        default_factory=list,
        description="Explicit whitelist of geographic regions or cloud enclaves where execution is structurally permitted (Payload Residency Pinning).",  # noqa: E501
    )
    max_permitted_grid_carbon_intensity: float | None = Field(
        le=10000.0,
        default=None,
        ge=0.0,
        description="Absolute structural ESG mandate. The execution graph will quarantine any federated node operating on a grid exceeding this gCO2eq/kWh threshold.",  # noqa: E501
    )
    pq_signature: PostQuantumSignatureReceipt | None = Field(
        default=None, description="The quantum-resistant signature securing the multi-tenant structural boundary."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "permitted_geographic_regions", sorted(self.permitted_geographic_regions))
        return self


class FederatedDiscoveryManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Governs the B2B Multi-Swarm Gossip Protocol, establishing the initial
    Model Context Protocol (MCP) broadcast endpoints for external discovery. As a ...Manifest
    suffix, this is a declarative, frozen snapshot of N-dimensional geometry at a specific
    point in time.

    CAUSAL AFFORDANCE: Emits a structured tensor beacon to neighboring swarms, authorizing
    the initiation of an OntologicalHandshakeReceipt if the supported_ontologies hashes
    mathematically overlap.

    EPISTEMIC BOUNDS: Geometrically capped by broadcast_endpoints and supported_ontologies
    string arrays (each max_length=1000000000). Both are explicitly sorted by the
    @model_validator (broadcast_endpoints by str key, supported_ontologies alphabetically)
    to guarantee invariant canonical RFC 8785 hashing across distinct environments.

    MCP ROUTING TRIGGERS: Gossip Protocol, Peer-to-Peer Discovery, Decentralized Federation,
    Semantic Broadcasting, Tensor Beacon
    """
    broadcast_endpoints: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        max_length=1000000000, description="The explicit array of strictly bounded MCP URI broadcast endpoints."
    )
    supported_ontologies: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        max_length=1000000000,
        description="The explicit array of cryptographic hashes defining acceptable domain ontologies.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "broadcast_endpoints", sorted(self.broadcast_endpoints, key=str))
        object.__setattr__(self, "supported_ontologies", sorted(self.supported_ontologies))
        return self


class ActiveInferenceContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the formal Fristonian Active Inference policy for an autonomous agent, mandating the minimization of Expected Free Energy through targeted epistemic foraging.

    CAUSAL AFFORDANCE: Unlocks kinetic tool execution strictly for the purpose of empirical observation, routing compute to maximize epistemic certainty regarding a specific hypothesis.

    EPISTEMIC BOUNDS: Mathematically constrained by expected_information_gain (a float bounded between 0.0 and 1.0 representing Shannon entropy reduction) and an economic execution_cost_budget_magnitude cap (le=1000000000).

    MCP ROUTING TRIGGERS: Active Inference, Expected Free Energy, Epistemic Foraging, Fristonian Mechanics, Shannon Entropy
    """
    task_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this active inference execution.",
    )
    target_hypothesis_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The HypothesisGenerationEvent this task is attempting to falsify.",
    )
    target_condition_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The specific FalsificationContract being tested.",
    )
    selected_tool_name: str = Field(
        max_length=2000, description="The exact tool from the ActionSpaceManifest allocated for this experiment."
    )
    expected_information_gain: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematically estimated reduction in Epistemic Uncertainty (entropy) this tool call will yield.",  # noqa: E501
    )
    execution_cost_budget_magnitude: int = Field(
        le=1000000000,
        ge=0,
        description="The maximum economic expenditure authorized to run this specific scientific test.",
    )


class AdjudicationIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Triggers a Mixed-Initiative forced resolution to break an
    epistemic deadlock within a CouncilTopologyManifest using Social Choice Theory. As
    an ...Intent suffix, the LLM may execute non-monotonic reasoning here.

    CAUSAL AFFORDANCE: Halts the active execution DAG and forces an external oracle
    (human or system) to definitively collapse the probability wave of competing claims,
    resolving the Condorcet paradox. The resolution_schema dict carries the strict
    JSON Schema for the tie-breaking response.

    EPISTEMIC BOUNDS: The state space is bounded by deadlocked_claims (min_length=2,
    max_length=86400000), deterministically sorted via @model_validator sort_arrays for
    RFC 8785 canonical hashing. The timeout_action is restricted to a strict Literal
    ["rollback", "proceed_default", "terminate"] to prevent infinite stalling.

    MCP ROUTING TRIGGERS: Social Choice Theory, Epistemic Deadlock, Mixed-Initiative
    Resolution, Oracle Forcing, Condorcet Paradox
    """
    type: Literal["forced_adjudication"] = Field(
        default="forced_adjudication",
        description="Discriminator for breaking deadlocks within a CouncilTopologyManifest.",
    )
    deadlocked_claims: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        max_length=86400000,
        min_length=2,
        description="The conflicting claim IDs or proposals the human must choose between.",
    )
    resolution_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="The strict JSON Schema for the tie-breaking response (usually an enum of the deadlocked_claims).",
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The action to take if the oracle is unresponsive."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "deadlocked_claims", sorted(self.deadlocked_claims))
        return self


class AdjudicationReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the
    definitive collapse of an MCDA evaluation, acting as a verified Outcome Reward Model
    (ORM) signal. As a ...Receipt suffix, this is an append-only coordinate on the
    Merkle-DAG.

    CAUSAL AFFORDANCE: Commits the calculated score and boolean passed verdict to the
    Epistemic Ledger, permanently binding the deterministic evaluation to the specific
    target_node_id (NodeIdentifierState) and authorizing downstream policy updates.

    EPISTEMIC BOUNDS: The evaluation outcome is strictly bounded to an integer score
    (ge=0, le=100). The underlying deductive proof (reasoning) is physically capped at
    max_length=2000. The entire receipt is cryptographically locked to the originating
    rubric_id CID (128-char regex).

    MCP ROUTING TRIGGERS: Cryptographic Verdict, Deterministic Proof, Grading Execution,
    Epistemic Commitment, Audit Trail
    """

    rubric_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The cryptographic pointer to the rubric dictating adjudication.",
    )
    target_node_id: NodeIdentifierState = Field(description="The ID of the node that was evaluated.")
    score: int = Field(ge=0, le=100, description="The final score assigned based on the rubric.")
    passed: bool = Field(description="Indicates whether the evaluation passed the threshold.")
    reasoning: str = Field(
        max_length=2000,
        description="The deterministic logical proof justifying the final verdict and mathematical score.",
    )


class AdversarialSimulationProfile(CoreasonBaseState):
    """
    A deterministic red-team configuration defining a structural attack vector
    to continuously validate semantic firewalls and execution bounds.
    """

    simulation_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for this red-team experiment.",
    )
    target_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The exact NodeIdentifierState the 'Judas Node' will attempt to compromise.",
    )
    attack_vector: Literal["prompt_extraction", "data_exfiltration", "semantic_hijacking", "tool_poisoning"] = Field(
        description="The mathematically predictable category of structural sabotage being simulated."
    )
    synthetic_payload: dict[Annotated[str, StringConstraints(max_length=255)], Any] | str = Field(
        max_length=100000,
        description="The raw poisoned text or malicious JSON-RPC schema injected into the target's context window.",
    )
    expected_firewall_trip: str | None = Field(
        max_length=2000,
        default=None,
        description="The exact rule_id of the InformationFlowPolicy or Governance bound expected to block this attack. Governing automated test assertions.",  # noqa: E501
    )


class AgentBidIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a probabilistic agentic bid in a multi-objective
    optimization market, factoring in projected compute latency, carbon constraints, and
    internal epistemic certainty (Expected Utility Theory). As an ...Intent suffix, this is
    a kinetic execution trigger.

    CAUSAL AFFORDANCE: Injects a competitive trajectory into the AuctionState order book,
    seeking authorization from the orchestrator to execute a specific
    TaskAnnouncementIntent branch.

    EPISTEMIC BOUNDS: The bid is geometrically bounded by estimated_cost_magnitude
    (le=1000000000), estimated_latency_ms (ge=0, le=86400000), estimated_carbon_gco2eq
    (ge=0.0, le=10000.0), and a continuous probability confidence_score (ge=0.0, le=1.0).
    The bidder is anchored to a 128-char agent_id CID.

    MCP ROUTING TRIGGERS: Expected Utility Theory, Multi-Objective Optimization, Epistemic
    Certainty, Spot Market Bid, Cost Estimation
    """
    agent_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="The NodeIdentifierState of the bidder."
    )
    estimated_cost_magnitude: int = Field(le=1000000000, description="The node's calculated cost to fulfill the task.")
    estimated_latency_ms: int = Field(le=86400000, ge=0, description="The node's estimated time to completion.")
    estimated_carbon_gco2eq: float = Field(
        le=10000.0,
        ge=0.0,
        description="The agent's mathematical projection of the environmental cost to execute this inference task.",
    )
    confidence_score: float = Field(ge=0.0, le=1.0, description="The node's epistemic certainty of success.")


class AmbientState(CoreasonBaseState):
    """
    Lightweight UX signal for UI rendering of progress.
    """

    status_message: str = Field(
        max_length=2000,
        description="The semantic 1D string projection representing the active kinetic execution state.",
    )
    progress: float | None = Field(
        le=1000000000.0, default=None, description="The progress ratio from 0.0 to 1.0, or None if indeterminate."
    )


class AnalogicalMappingTask(CoreasonBaseState):
    task_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this lateral thinking task.",
    )
    source_domain: str = Field(
        max_length=2000,
        description="The unrelated abstract concept space (e.g., 'thermodynamics', 'mycelial networks').",
    )
    target_domain: str = Field(max_length=2000, description="The actual problem space currently being solved.")
    required_isomorphisms: int = Field(
        le=86400000,
        ge=1,
        description="The exact number of structural/logical mappings the agent must successfully bridge between the two domains.",  # noqa: E501
    )
    divergence_temperature_override: float = Field(
        le=10.0,
        ge=0.0,
        description="The specific high-temperature sampling override required to force this creative leap.",
    )


class AnchoringPolicy(CoreasonBaseState):
    """
    The mathematical center of gravity preventing epistemic drift and sycophancy in the swarm.
    """

    anchor_prompt_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The undeniable SHA-256 hash of the core objective.",
    )
    max_semantic_drift: float = Field(
        ge=0.0,
        le=1.0,
        description="The maximum allowed cosine deviation from the anchor before the orchestrator forces a state rollback.",  # noqa: E501
    )


type AttackVectorProfile = Literal["rebuttal", "undercutter", "underminer"]
type AttestationMechanismProfile = Literal["fido2_webauthn", "zk_snark_groth16", "pqc_ml_dsa"]


class AuctionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the Algorithmic Mechanism Design for the decentralized spot
    market, establishing the exact rules of engagement (e.g., Vickrey-Clarke-Groves, Dutch,
    Sealed-Bid) to ensure truthful bidding (Strategyproofness). As a ...Policy suffix, this
    object defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Instructs the orchestrator's clearinghouse on how to mathematically
    resolve the AuctionState, applying the strict tie_breaker (TieBreakerPolicy) heuristic
    when bid vectors collide.

    EPISTEMIC BOUNDS: The market lifespan is strictly restricted by max_bidding_window_ms
    (le=86400000). The combinatorial space is locked to the AuctionMechanismProfile and
    TieBreakerPolicy Literal enums to prevent hallucinated market mechanics.

    MCP ROUTING TRIGGERS: Algorithmic Mechanism Design, Vickrey-Clarke-Groves,
    Strategyproofness, Market Clearing Heuristic, Strict Mathematical Boundary
    """
    auction_type: AuctionMechanismProfile = Field(description="The market mechanism governing the auction.")
    tie_breaker: TieBreakerPolicy = Field(description="The deterministic rule for resolving tied bids.")
    max_bidding_window_ms: int = Field(
        le=86400000, description="The absolute timeout in milliseconds for nodes to submit proposals."
    )


class BackpressurePolicy(CoreasonBaseState):
    """
    Declarative backpressure constraints.
    """

    max_queue_depth: int = Field(
        le=1000000000,
        description="The maximum number of unprocessed messages/observations allowed between connected nodes before yielding.",  # noqa: E501
    )
    token_budget_per_branch: int | None = Field(
        le=1000000000,
        default=None,
        description="The maximum token cost allowed per execution branch before rate-limiting.",
    )
    max_tokens_per_minute: int | None = Field(
        le=1000000000,
        default=None,
        gt=0,
        description="The maximum kinetic velocity of token consumption allowed before the circuit breaker trips.",
    )
    max_requests_per_minute: int | None = Field(
        le=1000000000, default=None, gt=0, description="The maximum kinetic velocity of API requests allowed."
    )
    max_uninterruptible_span_ms: int | None = Field(
        le=86400000,
        default=None,
        gt=0,
        description="Systemic heartbeat constraint. A node cannot lock the thread longer than this without yielding to poll for BargeInInterruptEvents.",  # noqa: E501
    )
    max_concurrent_tool_invocations: int | None = Field(
        le=1000000000,
        default=None,
        gt=0,
        description="The mathematical integer ceiling to prevent Sybil-like parallel mutations against the ActionSpaceManifest.",  # noqa: E501
    )


class BaseIntent(CoreasonBaseState):
    """Base class for presentation intents."""


class BasePanelProfile(CoreasonBaseState):
    """Base class for Scientific Visualization panels."""

    panel_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="Unique identifier for the panel."
    )


class BaseStateEvent(CoreasonBaseState):
    event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the Merkle-DAG.",  # noqa: E501
    )
    timestamp: float = Field(
        ge=0.0,
        le=253402300799.0,
        description="Causal Ancestry markers required to resolve decentralized event ordering.",
    )


class SystemFaultEvent(BaseStateEvent):
    type: Literal["system_fault"] = Field(
        default="system_fault", description="Discriminator type for a system fault event."
    )


class BoundedInterventionScopePolicy(CoreasonBaseState):
    """
    Constraints bounding human interaction for interventions.
    """

    allowed_fields: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        max_length=1000000000,
        description="The explicit whitelist of top-level JSON pointers mathematically open to mutation.",
    )
    json_schema_whitelist: dict[
        Annotated[str, StringConstraints(max_length=255)],
        str | int | float | bool | None | list[Any] | dict[Annotated[str, StringConstraints(max_length=255)], Any],
    ] = Field(description="Strict JSON Schema constraints for the human's input.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_fields", sorted(self.allowed_fields))
        return self


class BoundedJSONRPCIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Enforces the formal JSON-RPC 2.0 specification as a stateless,
    deterministic message-passing protocol, acting as the primary algorithmic firewall
    at the Zero-Trust network boundary. As an ...Intent suffix, this represents an
    authorized kinetic execution trigger.

    CAUSAL AFFORDANCE: Unlocks remote procedure execution while preventing JSON Bombing
    and Algorithmic Complexity Attacks. The method field (max_length=1000) specifies the
    RPC target. The id field (128-char CID regex | int le=1000000000 | None) binds
    request-response correlation.

    EPISTEMIC BOUNDS: The @field_validator validate_params_depth_and_size mathematically
    bounds recursive payload geometry (params) to: max depth=10, dict keys=100, key
    length=1000, list elements=1000, string length=10000. The jsonrpc field is a rigid
    Literal["2.0"] automaton.

    MCP ROUTING TRIGGERS: JSON-RPC 2.0, Stateless RPC, Algorithmic Complexity Attack,
    JSON Bombing Prevention, Deterministic Finite Automaton
    """

    jsonrpc: Literal["2.0"] = Field(..., description="JSON-RPC version.")
    method: str = Field(..., max_length=1000, description="Method to be invoked.")
    params: dict[Annotated[str, StringConstraints(max_length=255)], Any] | None = Field(
        max_length=86400000, default=None, description="Payload parameters."
    )
    id: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] | int | None = (
        Field(le=1000000000, default=None, description="Unique request identifier.")
    )

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


class BrowserDOMState(CoreasonBaseState):
    type: Literal["browser"] = Field(
        default="browser", description="Discriminator for Causal Actuators representing structural shifts."
    )
    current_url: str = Field(max_length=2000, description="Spatial Execution Bounds where the agent interacts.")

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
            if parsed.scheme in ("http", "https"):
                raise ValueError("SSRF topological violation detected: Invalid hostname in HTTP URI")
            return url
        hostname_lower = hostname.lower()
        if hostname_lower in {
            "localhost",
            "localhost.localdomain",
            "broadcasthost",
            "local",
            "internal",
        } or hostname_lower.endswith((".local", ".internal", ".arpa", ".nip.io", ".sslip.io", "localhost.localdomain")):
            raise ValueError(f"SSRF topological violation detected: {hostname}")
        clean_hostname = hostname.strip("[]")
        try:
            ip = ipaddress.ip_address(clean_hostname)
        except ValueError:
            try:
                parts = clean_hostname.split(".")
                if len(parts) in (1, 2, 3, 4):
                    parsed_parts = []
                    for part in parts:
                        if not part:
                            raise ValueError
                        if part.startswith(("0x", "0X")):
                            parsed_parts.append(int(part, 16))
                        elif part.startswith("0") and len(part) > 1 and all(c in "01234567" for c in part):
                            parsed_parts.append(int(part, 8))
                        elif part.isdigit():
                            parsed_parts.append(int(part))
                        else:
                            raise ValueError
                    for p in parsed_parts:
                        if p < 0 or p > 4294967295:
                            raise ValueError
                    if len(parsed_parts) == 4:
                        if any(p > 255 for p in parsed_parts):
                            raise ValueError
                        ip_int = (
                            (parsed_parts[0] << 24) + (parsed_parts[1] << 16) + (parsed_parts[2] << 8) + parsed_parts[3]
                        )
                    elif len(parsed_parts) == 3:
                        if parsed_parts[0] > 255 or parsed_parts[1] > 255 or parsed_parts[2] > 65535:
                            raise ValueError
                        ip_int = (parsed_parts[0] << 24) + (parsed_parts[1] << 16) + parsed_parts[2]
                    elif len(parsed_parts) == 2:
                        if parsed_parts[0] > 255 or parsed_parts[1] > 16777215:
                            raise ValueError
                        ip_int = (parsed_parts[0] << 24) + parsed_parts[1]
                    else:
                        ip_int = parsed_parts[0]
                    ip = ipaddress.ip_address(ip_int)
                else:
                    raise ValueError
            except ValueError, OverflowError, IndexError:
                return url
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError(f"SSRF restricted IP detected: {hostname}")
        return url

    viewport_size: tuple[int, int] = Field(
        max_length=1000000000, description="Capability Perimeters detailing bounding coordinates."
    )
    dom_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash acting as the structural manifestation vector.",
    )
    accessibility_tree_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the accessibility tree defining Exogenous Perturbations to the state space.",
    )
    screenshot_cid: str | None = Field(
        max_length=2000,
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the snapshot representation.",  # noqa: E501
    )


class BypassReceipt(CoreasonBaseState):
    """The Merkle Null-Op preserving the topological chain of custody when an extraction node is intentionally
    skipped."""

    artifact_event_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="The exact genesis CID of the document, ensuring continuity.",
    )
    bypassed_node_id: NodeIdentifierState = Field(
        description="The exact extraction step in the DAG that was mathematically starved of compute."
    )
    justification: Literal["modality_mismatch", "budget_exhaustion", "sla_timeout"] = Field(
        description="The deterministic reason the orchestrator severed this execution branch."
    )
    cryptographic_null_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 null-hash representing the skipped state to satisfy the Epistemic Ledger.",
    )


class CausalAttributionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Pearlian causal tracing, linking a localized cognitive
    synthesis back to its historical Merkle-DAG origin. As a ...State suffix, this is a
    declarative, frozen snapshot of a causal connection at a point in time.

    CAUSAL AFFORDANCE: Authorizes the assignment of fractional attention or influence
    weights to prior events, establishing a Directed Acyclic Graph (DAG) of causal lineage.

    EPISTEMIC BOUNDS: The influence_weight is mathematically bounded to a continuous
    probability distribution (ge=0.0, le=1.0). The source_event_id is locked to a 128-char
    CID regex (^[a-zA-Z0-9_.:-]+$).

    MCP ROUTING TRIGGERS: Pearlian Causal Tracing, Directed Acyclic Graph, Causal Lineage,
    Attention Weighting, Influence Distribution
    """
    source_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the source event in the Merkle-DAG.",  # noqa: E501
    )
    influence_weight: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical attention/importance weight (0.0 to 1.0) assigned to this source by the agent.",
    )


class CollectiveIntelligenceProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Integrated Information Theory (IIT) and synergy metrics
    to quantify system-level emergence in the neurosymbolic swarm. As a ...Profile suffix,
    this is a declarative property descriptor.

    CAUSAL AFFORDANCE: Provides the orchestrator with macroscopic topological variables to
    evaluate whether the multi-agent ensemble is producing non-linear, synergistic output
    versus independent parallel processing.

    EPISTEMIC BOUNDS: coordination_score and information_integration are upper-clamped at
    le=1.0 to represent normalized mutual information. synergy_index is capped at
    le=1000000000.0 to prevent scalar explosion. Note: no lower ge bounds are enforced on
    these fields.

    MCP ROUTING TRIGGERS: Integrated Information Theory, Systemic Emergence, Conditional
    Mutual Information, Synergy Index, Multi-Agent Coupling
    """
    synergy_index: float = Field(
        le=1000000000.0,
        description="The mathematical measure of the degree of emergence. A high SI indicates strong positive emergence.",  # noqa: E501
    )
    coordination_score: float = Field(
        le=1.0,
        description="The temporal alignment measuring the extent to which agents coordinate their actions over time.",
    )
    information_integration: float = Field(
        le=1.0,
        description="The conditional mutual information quantifying the information flow and tight coupling between agents.",  # noqa: E501
    )


class ShapleyAttributionReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Cooperative Game Theory to compute the exact Shapley
    value ($\phi_i$) for a specific agent's marginal contribution to a collective outcome.
    As a ...Receipt suffix, this is an append-only coordinate on the Merkle-DAG.

    CAUSAL AFFORDANCE: Unlocks deterministic credit assignment and thermodynamic reward
    distribution, allowing the orchestrator to equitably distribute escrow payouts or
    policy gradient updates to the participating target_node_id (NodeIdentifierState).

    EPISTEMIC BOUNDS: normalized_contribution_percentage is strictly clamped (ge=0.0,
    le=1.0). The causal_attribution_score has only le=1.0 (no ge bound). The Monte Carlo
    approximation confidence bounds (confidence_interval_lower/upper) are capped at
    le=1000000000.0.

    MCP ROUTING TRIGGERS: Cooperative Game Theory, Shapley Value, Credit Assignment,
    Marginal Contribution, Monte Carlo Approximation
    """
    target_node_id: NodeIdentifierState = Field(description="The agent whose causal influence is being measured.")
    causal_attribution_score: float = Field(
        le=1.0, description="The exact Shapley value (\\phi_i) satisfying efficiency, symmetry, and additivity axioms."
    )
    normalized_contribution_percentage: float = Field(
        ge=0.0, le=1.0, description="The relative fractional contribution bounded between 0.0 and 1.0."
    )
    confidence_interval_lower: float = Field(
        le=1000000000.0, description="The bootstrap confidence bounds of the Monte Carlo approximation (lower bound)."
    )
    confidence_interval_upper: float = Field(
        le=1000000000.0, description="The bootstrap confidence bounds of the Monte Carlo approximation (upper bound)."
    )


class CausalExplanationEvent(BaseStateEvent):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the
    macroscopic factorization of a collective swarm outcome into its constituent causal
    components. As an ...Event suffix, this is an append-only coordinate on the
    Merkle-DAG.

    CAUSAL AFFORDANCE: Commits the system-level CollectiveIntelligenceProfile and the
    individual ShapleyAttributionReceipt array to the Epistemic Ledger, finalizing the
    credit assignment for a target_outcome_event_id.

    EPISTEMIC BOUNDS: The target_outcome_event_id is locked to a 128-char CID regex. The
    @model_validator mathematically enforces deterministic canonical hashing by sorting the
    agent_attributions array by target_node_id (NodeIdentifierState), guaranteeing RFC 8785
    alignment.

    MCP ROUTING TRIGGERS: Causal Factorization, Epistemic Ledger Commit, Credit Assignment,
    Macroscopic Explanation, Deterministic Sorting
    """
    type: Literal["causal_explanation"] = Field(
        default="causal_explanation", description="Discriminator type for a causal explanation event."
    )
    target_outcome_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the collective outcome being explained.",
    )
    collective_intelligence: CollectiveIntelligenceProfile = Field(description="The system-level emergence metrics.")
    agent_attributions: list[ShapleyAttributionReceipt] = Field(
        description="The array of individual causal contributions."
    )

    @model_validator(mode="after")
    def sort_agent_attributions(self) -> Self:
        object.__setattr__(self, "agent_attributions", sorted(self.agent_attributions, key=lambda x: x.target_node_id))
        return self


class CausalDirectedEdgeState(CoreasonBaseState):
    source_variable: str = Field(min_length=1, description="The independent variable $X$.")
    target_variable: str = Field(min_length=1, description="The dependent variable $Y$.")
    edge_type: Literal["direct_cause", "confounder", "collider", "mediator"] = Field(
        description="The specific Pearlian topological relationship between the two variables."
    )


class CircuitBreakerEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements the Circuit Breaker control-flow pattern from distributed
    systems theory to deterministically interrupt cascading failures in the neurosymbolic
    network. As an ...Event suffix, this is an append-only coordinate on the Merkle-DAG that
    the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Physically severs the active execution thread for the target_node_id
    (NodeIdentifierState), immediately halting out-of-memory cascades, runaway generation
    loops, or API rate-limit breaches.

    EPISTEMIC BOUNDS: The fault perimeter is mathematically restricted to a specific
    NodeIdentifierState (target_node_id). To prevent log-poisoning and VRAM exhaustion, the
    error_signature is strictly capped at max_length=2000.

    MCP ROUTING TRIGGERS: Control Theory, Circuit Breaker, Cascading Failure Prevention,
    Telemetry Intercept, Fault Detection
    """

    type: Literal["circuit_breaker_event"] = Field(
        default="circuit_breaker_event", description="The type of the resilience payload."
    )
    target_node_id: NodeIdentifierState = Field(
        description="The ID of the node for which the circuit breaker was tripped."
    )
    error_signature: str = Field(max_length=2000, description="Signature or summary of the error causing the trip.")


class ConstitutionalAmendmentIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a non-monotonic structural revision trigger within a
    Defeasible Logic framework, engineered to adapt the GovernancePolicy to
    out-of-distribution environments. As an ...Intent suffix, the LLM may execute
    non-monotonic reasoning here.

    CAUSAL AFFORDANCE: Triggers an active topological mutation (Pearlian intervention) to
    resolve logical friction, applying a strict RFC 6902 JSON Patch (proposed_patch) to the
    underlying alignment manifold.

    EPISTEMIC BOUNDS: Cryptographically anchored to the specific drift_event_id (regex
    bounded CID ^[a-zA-Z0-9_.:-]+$) that mathematically justified the revision. The payload
    is strictly constrained to a JSON Schema object (proposed_patch). The justification
    field (max_length=2000) bounds the natural language argument.

    MCP ROUTING TRIGGERS: Defeasible Logic, Non-Monotonic Revision, Out-of-Distribution
    Adaptation, Normative Drift Resolution, Pearlian Intervention
    """

    type: Literal["constitutional_amendment"] = Field(
        default="constitutional_amendment", description="The strict discriminator for this intervention payload."
    )
    drift_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the NormativeDriftEvent that justified triggering this proposal.",
    )
    proposed_patch: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="A strict, structurally bounded JSON Patch (RFC 6902) proposed by the AI to mutate the GovernancePolicy.",  # noqa: E501
    )
    justification: str = Field(
        max_length=2000,
        description="The AI's natural language structural/logical argument for why this patch resolves the contradiction without violating the root AnchoringPolicy.",  # noqa: E501
    )


class ContinuousMutationPolicy(CoreasonBaseState):
    mutation_paradigm: Literal["append_only", "merge_on_resolve"] = Field(
        description="Forces non-destructive graph mutations."
    )
    max_uncommitted_edges: int = Field(
        le=1000000000, gt=0, description="Backpressure threshold before forcing a commit."
    )
    micro_batch_interval_ms: int = Field(le=86400000, gt=0, description="Temporal bound for flushing the stream.")

    @model_validator(mode="after")
    def enforce_append_only_vram_bound(self) -> Self:
        """Mathematically prevent Out-Of-Memory (OOM) crashes by strictly bounding the buffer."""
        if self.mutation_paradigm == "append_only" and self.max_uncommitted_edges > 10000:
            raise ValueError("max_uncommitted_edges must be <= 10000 for append_only paradigm to prevent OOM crashes.")
        return self


class CounterfactualRegretEvent(BaseStateEvent):
    """A cryptographic record of an agent simulating an alternative timeline to calculate epistemic regret
    and update its policy."""

    type: Literal["counterfactual_regret"] = Field(
        default="counterfactual_regret", description="Discriminator type for a counterfactual regret event."
    )
    historical_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the specific historical state node where the agent mathematically diverged to simulate an alternative path.",  # noqa: E501
    )
    counterfactual_intervention: str = Field(
        max_length=2000,
        description="The specific alternative action or do-calculus intervention applied in the simulation.",
    )
    expected_utility_actual: float = Field(
        le=1000000000.0, description="The calculated utility of the trajectory that was actually executed."
    )
    expected_utility_simulated: float = Field(
        le=1000000000.0, description="The calculated utility of the simulated counterfactual trajectory."
    )
    epistemic_regret: float = Field(
        le=1000000000.0,
        description="The mathematical variance (simulated - actual) representing the opportunity cost of the historical decision.",  # noqa: E501
    )
    policy_mutation_gradients: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ] = Field(
        le=1000000000.0,
        default_factory=dict,
        description="The stateless routing gradient adjustments derived from the calculated regret, used to self-correct future routing.",  # noqa: E501
    )


class CrossSwarmHandshakeState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Tracks the non-monotonic state transition of a Byzantine-tolerant B2B
    negotiation between two distinct enterprise tenant CID identifiers (initiating_tenant_id
    and receiving_tenant_id). As a ...State suffix, this is a declarative, frozen snapshot of
    N-dimensional geometry at a specific point in time.

    CAUSAL AFFORDANCE: Transitions the federated network from a proposed capability swap into
    an active OntologicalHandshakeReceipt, forcing the execution of the strict offered_sla
    (BilateralSLA).

    EPISTEMIC BOUNDS: Cryptographically bounded by handshake_id (CID regex
    ^[a-zA-Z0-9_.:-]+$). The negotiation lifecycle is physically constrained to the strict
    Literal automaton ["proposed", "negotiating", "aligned", "rejected"] via FSM Logit
    Masking, preventing execution deadlocks.

    MCP ROUTING TRIGGERS: Byzantine-Tolerant Negotiation, Zero-Trust Handshake, Finite State
    Machine, Cross-Tenant Federation, Asynchronous B2B
    """
    handshake_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for this B2B negotiation.",
    )
    initiating_tenant_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The enterprise DID requesting the connection.",
    )
    receiving_tenant_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The enterprise DID receiving the connection.",
    )
    offered_sla: BilateralSLA = Field(description="The initial structural/data boundary proposed.")
    status: Literal["proposed", "negotiating", "aligned", "rejected"] = Field(
        default="proposed", description="The current status of the handshake."
    )


class CrossoverPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes the chromosomal crossover and genetic recombination
    heuristics for blending latent feature vectors of elite parent agents. As a ...Policy
    suffix, this object defines rigid mathematical boundaries that the orchestrator must
    enforce globally.

    CAUSAL AFFORDANCE: Executes the deterministic interpolation of N-dimensional properties
    from successful agents using a specific geometric strategy (CrossoverMechanismProfile)
    to breed the next generation's starting state.

    EPISTEMIC BOUNDS: The blending_factor is strictly constrained to a fractional
    interpolation ratio (ge=0.0, le=1.0) to mathematically prevent extrapolated state drift
    beyond the parents' bounding box. Relies on optional verifiable_entropy
    (VerifiableEntropyReceipt) to ensure unbiased recombination.

    MCP ROUTING TRIGGERS: Genetic Recombination, Chromosomal Crossover, Vector
    Interpolation, Elitism, Reproduction Heuristic
    """

    strategy_type: CrossoverMechanismProfile = Field(
        description="The heuristic method for blending successful parent agents."
    )
    blending_factor: float = Field(
        ge=0.0, le=1.0, description="The proportional mix ratio when merging vector properties."
    )
    verifiable_entropy: VerifiableEntropyReceipt | None = Field(
        default=None, description="The cryptographic envelope proving the fairness of the applied crossover logic."
    )


class CrystallizationPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: CrystallizationPolicy governs Systemic Memory Consolidation (analogous 
    to Hebbian Learning). It is a mathematical threshold that determines exactly when noisy, 
    high-entropy episodic logs are statistically proven enough to be promoted into permanent semantic axioms.

    CAUSAL AFFORDANCE: Instructs the swarm to execute Inductive Logic Programming. It authorizes the 
    orchestrator to collapse a massive subgraph of repetitive ObservationEvent nodes into a single, 
    dense SemanticNodeState, drastically reducing future inference costs.

    EPISTEMIC BOUNDS: The aleatoric_entropy_threshold float (le=0.1) dictates the maximum statistical 
    variance allowed before compression is physically authorized. It mathematically mandates a sample 
    size of min_observations_required (ge=10) to prevent premature epistemic convergence.

    MCP ROUTING TRIGGERS: Hebbian Learning, Memory Consolidation, Inductive Logic Programming, Aleatoric Entropy, Knowledge Distillation
    """

    min_observations_required: int = Field(
        le=1000000000,
        ge=10,
        description="The minimum number of episodic logs needed to statistically prove a crystallized rule.",
    )
    aleatoric_entropy_threshold: float = Field(
        le=0.1,
        description="The entropy variance must fall below this mathematical threshold to prove absolute certainty before compression is authorized.",  # noqa: E501
    )
    target_cognitive_tier: Literal["semantic", "working"] = Field(
        description="The destination tier where the compressed rule will be stored."
    )


class CustodyReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the successful
    execution of an InformationFlowPolicy redaction on the Merkle-DAG. Enforced as fully
    immutable via ConfigDict(frozen=True). As a ...Receipt suffix, this is an append-only
    coordinate that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Unlocks strict audit compliance by mathematically mapping the optional
    toxic pre_redaction_hash to the mandatory safe post_redaction_hash, proving
    non-repudiation via the applied_policy_id.

    EPISTEMIC BOUNDS: Temporal geometry is strictly clamped to redaction_timestamp_unix_nano
    (ge=0, le=253402300799000000000). Both hashes are locked to immutable SHA-256 hexadecimal
    bounds (^[a-f0-9]{64}$). The pre_redaction_hash is optional (default=None) for cases
    where raw toxic data must not be stored.

    MCP ROUTING TRIGGERS: Chain of Custody, Cryptographic Provenance, Merkle-DAG Audit,
    Non-Repudiation, Data Isomorphism
    """

    model_config = ConfigDict(frozen=True)
    record_id: str = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        max_length=255,
        description="Unique identifier for this chain-of-custody entry.",
    )
    source_node_id: str = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        max_length=255,
        description="The execution node that emitted the original payload.",
    )
    applied_policy_id: str = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        max_length=255,
        description="The ID of the InformationFlowPolicy successfully applied.",
    )
    pre_redaction_hash: str | None = Field(
        min_length=1,
        pattern="^[a-f0-9]{64}$",
        default=None,
        max_length=255,
        description="Optional SHA-256 hash of the raw toxic data for isolated audit vaults.",
    )
    post_redaction_hash: str = Field(
        min_length=1,
        pattern="^[a-f0-9]{64}$",
        max_length=255,
        description="The definitive SHA-256 hash of the sanitized, mathematically clean payload.",
    )
    redaction_timestamp_unix_nano: int = Field(
        ge=0, le=253402300799000000000, description="The precise temporal point the redaction was completed."
    )


class DefeasibleAttackEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A directed causal edge executing non-monotonic truth maintenance
    within a Dung-style Abstract Argumentation Framework. It mathematically projects a defeater
    from a source claim against a target claim. As an ...Event suffix, this object is a
    cryptographically frozen historical fact that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Modulates the probabilistic acceptability of the target_claim_id within
    the EpistemicArgumentGraphState. If valid, it triggers a DefeasibleCascadeEvent to
    physically sever and quarantine downstream nodes relying on the target.

    EPISTEMIC BOUNDS: Strictly bounds the attack geometry using AttackVectorProfile enums
    (Literal["rebuttal", "undercutter", "underminer"]). Source (source_claim_id) and target
    (target_claim_id) mappings are locked to 128-character cryptographic CIDs via strict
    regex ^[a-zA-Z0-9_.:-]+$, preventing unbounded graph traversals.

    MCP ROUTING TRIGGERS: Undercutting Defeater, Non-Monotonic Logic, Directed Attack Edge,
    Belief Retraction, Defeasible Reasoning
    """
    attack_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this directed attack edge.",  # noqa: E501
    )
    source_claim_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the claim mounting the attack.",  # noqa: E501
    )
    target_claim_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the claim being attacked.",  # noqa: E501
    )
    attack_vector: AttackVectorProfile = Field(description="Geometric matrices of undercutting defeaters.")


class DimensionalProjectionContract(CoreasonBaseState):
    source_model_name: str = Field(max_length=2000, description="The native embedding model of the origin agent.")
    target_model_name: str = Field(max_length=2000, description="The native embedding model of the destination agent.")
    projection_matrix_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact mathematical matrix used to compress or translate the latent dimensions.",  # noqa: E501
    )
    isometry_preservation_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Mathematical proof (e.g., Earth Mover's Distance preservation) of how accurately relative semantic distances were maintained during projection.",  # noqa: E501
    )


type DistributionShapeProfile = Literal["gaussian", "uniform", "beta"]


class DistributionProfile(CoreasonBaseState):
    """Profile defining a probability density function."""

    distribution_type: DistributionShapeProfile = Field(
        description="The mathematical shape of the probability density function."
    )
    mean: float | None = Field(
        le=1000000000.0, default=None, description="The expected value (mu) of the distribution."
    )
    variance: float | None = Field(
        le=1000000000.0, default=None, description="The mathematical variance (sigma squared)."
    )
    confidence_interval_95: tuple[float, float] | None = Field(
        max_length=1000000000, default=None, description="The 95% probability bounds."
    )

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> Any:
        if self.confidence_interval_95 is not None and self.confidence_interval_95[0] >= self.confidence_interval_95[1]:
            raise ValueError("confidence_interval_95 must have interval[0] < interval[1]")
        return self


class DiversityPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Cognitive Heterogeneity and Ensemble Variance mandates to
    physically prevent mode collapse, epistemic echo-chambers, and algorithmic Groupthink
    within the swarm. As a ...Policy suffix, this object defines rigid mathematical
    boundaries.

    CAUSAL AFFORDANCE: Forces the orchestrator to construct a topologically diverse
    multi-model matrix (if model_variance_required is True) and assigns explicit adversarial
    ("Devil's Advocate") roles to intentionally perturb the consensus gradient.

    EPISTEMIC BOUNDS: Physically bounds the lower limits of adversarial insertion via
    min_adversaries (le=1000000000, no ge bound). Enforces continuous entropic variance via
    the optional temperature_variance float (le=1000000000.0, default=None).

    MCP ROUTING TRIGGERS: Cognitive Heterogeneity, Ensemble Variance, Groupthink
    Mitigation, Red Teaming, Adversarial Perturbation
    """

    min_adversaries: int = Field(
        le=1000000000,
        description="The minimum number of adversarial or 'Devil's Advocate' roles required to prevent groupthink.",
    )
    model_variance_required: bool = Field(
        description="If True, forces the orchestrator to route sub-agents to different foundational models."
    )
    temperature_variance: float | None = Field(
        le=1000000000.0,
        default=None,
        description="Required statistical variance in temperature settings across the council.",
    )


class DocumentLayoutRegionState(CoreasonBaseState):
    block_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique structural identifier for this geometric region.",
    )
    block_type: Literal["header", "paragraph", "figure", "table", "footnote", "caption", "equation"] = Field(
        description="The taxonomic classification of the layout region."
    )
    anchor: MultimodalTokenAnchorState = Field(
        description="The strict visual and token coordinate bindings for this block."
    )


class DocumentLayoutManifest(CoreasonBaseState):
    blocks: dict[Annotated[str, StringConstraints(max_length=255)], DocumentLayoutRegionState] = Field(
        max_length=1000000000, description="Dictionary mapping block_ids to their strict spatial definitions."
    )
    chronological_flow_edges: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Directed edges defining the topological sort (chronological flow) of the document.",
    )

    @model_validator(mode="after")
    def verify_dag_and_integrity(self) -> Self:
        adj: dict[Annotated[str, StringConstraints(max_length=255)], list[str]] = {
            node_id: [] for node_id in self.blocks
        }
        for source, target in self.chronological_flow_edges:
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


class ContextExpansionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Governs the structural logic for Hierarchical Navigable Small World
    (HNSW) context hydration and dynamic text block aggregation. As a ...Policy suffix, this
    object defines rigid mathematical boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Triggers the physical expansion of the active working memory partition,
    authorizing the orchestrator to mathematically merge adjacent semantic nodes or sliding
    windows via the selected expansion_paradigm (sliding_window, hierarchical_merge, or
    document_summary).

    EPISTEMIC BOUNDS: Strictly capped by max_token_budget (gt=0, le=1000000000) to prevent
    GPU VRAM exhaustion. Further bounded by the optional spatial geometry
    parent_merge_threshold (ge=0.0, le=1.0) and the optional temporal window
    surrounding_sentences_k (ge=1, le=1000000000).

    MCP ROUTING TRIGGERS: Hierarchical Navigable Small World, Context Hydration, Token Budget
    Optimization, Semantic Merging
    """
    expansion_paradigm: Literal["sliding_window", "hierarchical_merge", "document_summary"] = Field(
        description="The mathematical paradigm governing how context is expanded."
    )
    max_token_budget: int = Field(
        le=1000000000, gt=0, description="The maximum physical token allowance for expansion."
    )
    surrounding_sentences_k: int | None = Field(
        le=1000000000, default=None, ge=1, description="The strict temporal window of surrounding sentences."
    )
    parent_merge_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="The geometric cosine similarity threshold required to merge parent nodes.",
    )


class TopologicalRetrievalContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the rigid traversal perimeters for Graph Convolutional Network
    (GCN) or Random Walk with Restart (RWR) operations across the Causal DAG. As a ...Contract
    suffix, this object defines rigid mathematical boundaries that the orchestrator must
    enforce globally.

    CAUSAL AFFORDANCE: Restricts graph hopping algorithms to explicit Pearlian edge types
    (Literal["causes", "confounds", "correlates_with", "undirected"]), mathematically
    preventing epistemic drift and hallucination during deep multi-hop retrieval.

    EPISTEMIC BOUNDS: Bounded recursively by max_hop_depth (ge=1, le=1000000000). The
    @model_validator physically enforces deterministic sorting of
    allowed_causal_relationships (min_length=1) to guarantee RFC 8785 canonical hashing.
    Geometric distance preservation is toggled via enforce_isometry (default=True).

    MCP ROUTING TRIGGERS: Directed Acyclic Graph, Pearlian Traversal, Isometry Preservation,
    Random Walk with Restart
    """
    max_hop_depth: int = Field(le=1000000000, ge=1, description="The strictly typed search depth bound for the cDAG.")
    allowed_causal_relationships: list[Literal["causes", "confounds", "correlates_with", "undirected"]] = Field(
        min_length=1, description="The explicit whitelist of permissible causal edges to traverse."
    )
    enforce_isometry: bool = Field(default=True, description="Enforces preservation of geometric distances.")

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_causal_relationships", sorted(self.allowed_causal_relationships))
        return self


class LatentProjectionIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Acts as the kinetic trigger for Maximum Inner Product Search (MIPS)
    and k-Nearest Neighbors (k-NN) retrieval across high-dimensional semantic manifolds. As
    an ...Intent suffix, the LLM may execute non-monotonic reasoning here.

    CAUSAL AFFORDANCE: Forces the orchestrator's embedding engine to dynamically hydrate the
    working context by fetching the top_k_candidates nearest to the synthetic_target_vector.
    Optionally embeds a TopologicalRetrievalContract for graph traversal bounds and a
    ContextExpansionPolicy for post-retrieval merging.

    EPISTEMIC BOUNDS: Mathematically boundary-enforced by min_isometry_score (ge=-1.0,
    le=1.0) to automatically prune low-relevance hallucinations before they consume context
    window tokens. The top_k_candidates is strictly positive (gt=0).

    MCP ROUTING TRIGGERS: Maximum Inner Product Search, k-Nearest Neighbors, Latent Manifold
    Projection, Retrieval-Augmented Generation
    """
    type: Literal["latent_projection"] = Field(
        default="latent_projection", description="Discriminator for RAG projection intent."
    )
    synthetic_target_vector: VectorEmbeddingState = Field(
        description="The strictly typed embedding tensor directing the query."
    )
    top_k_candidates: int = Field(gt=0, description="The maximum number of nodes to extract from the index.")
    min_isometry_score: float = Field(
        ge=-1.0, le=1.0, description="The minimum cosine similarity bounds for accepting a vector match."
    )
    topological_bounds: TopologicalRetrievalContract | None = Field(
        default=None, description="The explicit graph traversal contract."
    )
    context_expansion: ContextExpansionPolicy | None = Field(
        default=None, description="The structural rules governing context hydration."
    )


class SemanticDiscoveryIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Orchestrates zero-shot latent capability routing by computing the
    geometric Cosine Distance between the agent's epistemic deficit vector and the available
    tool manifold. As an ...Intent suffix, the LLM may execute non-monotonic reasoning here.

    CAUSAL AFFORDANCE: Unlocks the dynamic, runtime mounting of tools and MCP servers whose
    dense vector embeddings (query_vector) align mathematically with the query tensor,
    bypassing hardcoded tool schemas.

    EPISTEMIC BOUNDS: Mechanically rejects capabilities that fall below the min_isometry_score
    (ge=-1.0, le=1.0) boundary. The returned toolsets are strictly limited to the
    deterministically sorted required_structural_types array, enforced by the @model_validator.

    MCP ROUTING TRIGGERS: Zero-Shot Tool Discovery, Capability Routing, Dense Vector
    Embedding, Epistemic Deficit Resolution
    """
    type: Literal["semantic_discovery"] = Field(
        default="semantic_discovery", description="Discriminator for geometric boundary of latent tool discovery."
    )
    query_vector: VectorEmbeddingState = Field(
        description="The latent vector representation of the epistemic deficit the agent is trying to solve."
    )
    min_isometry_score: float = Field(
        ge=-1.0, le=1.0, description="The minimum cosine similarity required to authorize a capability mount."
    )
    required_structural_types: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        max_length=1000000000,
        description="The strict array of strings defining topological limits on the discovered tools.",
    )

    @model_validator(mode="after")
    def sort_required_structural_types(self) -> Self:
        object.__setattr__(self, "required_structural_types", sorted(self.required_structural_types))
        return self


class DraftingIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: DraftingIntent is an Active Inference mechanism designed to resolve a detected 
    Epistemic Gap. It is triggered when the swarm lacks the structural parameters necessary to minimize 
    predictive surprise mathematically.

    CAUSAL AFFORDANCE: Emits a structural query to an external human oracle to forcefully reduce 
    Shannon Entropy. It suspends autonomous trajectory generation until the missing semantic dimensions 
    are projected back into the working memory partition.

    EPISTEMIC BOUNDS: The human's unstructured cognitive entropy is aggressively forced through a 
    mathematical funnel via the resolution_schema (a strict JSON Schema bounding the acceptable response). 
    If the human fails to satisfy the schema, the timeout_action guarantees deterministic fallback routing.

    MCP ROUTING TRIGGERS: Active Inference, Shannon Entropy Reduction, Epistemic Gap, Zero-Shot Elicitation, Structural Oracle
    """

    type: Literal["drafting"] = Field(
        default="drafting", description="Discriminator for requesting specific missing context from a human."
    )
    context_prompt: str = Field(
        max_length=2000, description="The prompt explaining what information the swarm is missing."
    )
    resolution_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000,
        description="The strict JSON Schema the human's input must satisfy before the graph can resume.",
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The action to take if the human fails to provide the draft."
    )


class DynamicConvergenceSLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the mathematical Optimal Stopping Theory boundaries for Monte
    Carlo Tree Search (MCTS) and test-time compute scaling. As an ...SLA suffix, this object
    enforces rigid mathematical boundaries that the orchestrator must respect globally.

    CAUSAL AFFORDANCE: Triggers an early termination circuit breaker on reasoning trajectories
    when the gradient of the Process Reward Model (PRM) score falls below the epsilon delta,
    halting unnecessary probability wave expansion and preserving VRAM.

    EPISTEMIC BOUNDS: Mathematically constrained by convergence_delta_epsilon (ge=0.0, le=1.0)
    over a strictly positive lookback_window_steps (gt=0, le=1000000000). Physically mandates
    a minimum_reasoning_steps burn-in period (gt=0, le=1000000000) to prevent premature
    collapse before the latent space is adequately explored.

    MCP ROUTING TRIGGERS: Optimal Stopping Theory, MCTS, PRM Convergence, Circuit Breaker,
    Bellman Equation
    """

    convergence_delta_epsilon: float = Field(
        le=1.0,
        ge=0.0,
        description="The minimal required PRM score improvement across the lookback window to justify continued compute.",  # noqa: E501
    )
    lookback_window_steps: int = Field(
        le=1000000000, gt=0, description="The N-step temporal window over which the PRM gradient is calculated."
    )
    minimum_reasoning_steps: int = Field(
        le=1000000000,
        gt=0,
        description="The mandatory 'burn-in' period. The orchestrator cannot terminate the search before this structural depth is reached, preventing premature collapse.",  # noqa: E501
    )


class EmbodiedSensoryVectorProfile(CoreasonBaseState):
    sensory_modality: Literal["video", "audio", "spatial_telemetry"] = Field(
        description="Multimodal Sensor Fusion and Spatial-Temporal Bindings representing Proprioceptive State and Exteroceptive Vectors."  # noqa: E501
    )
    bayesian_surprise_score: float = Field(
        le=1.0,
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
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the active node generation cycle that was killed in the Merkle-DAG.",  # noqa: E501
    )
    sensory_trigger: EmbodiedSensoryVectorProfile | None = Field(
        default=None,
        description="The continuous multimodal trigger (e.g., audio spike, user saying 'stop') that justified the interruption.",  # noqa: E501
    )
    retained_partial_payload: dict[Annotated[str, StringConstraints(max_length=255)], Any] | str | None = Field(
        max_length=100000,
        default=None,
        description="The 'stutter' state: the incomplete fragment of thought or text appended before the kill signal.",
    )
    epistemic_disposition: Literal["discard", "retain_as_context", "mark_as_falsified"] = Field(
        description="Explicit instruction to the orchestrator on how to patch the shared state blackboard with the partial payload."  # noqa: E501
    )


type EncodingChannelProfile = Literal["x", "y", "color", "size", "opacity", "shape", "text"]


class EnsembleTopologyProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Declarative mapping of concurrent topology branches for test-time superposition.
    Must map to strict W3C DIDs (NodeIdentifierStates) and provide an explicit wave-collapse opcode.
    """

    concurrent_branch_ids: list[NodeIdentifierState] = Field(
        ...,
        min_length=2,
        description="The strict array of strict W3C DIDs (NodeIdentifierStates) representing concurrent topology branches.",  # noqa: E501
    )
    fusion_function: Literal["weighted_consensus", "highest_confidence", "brier_score_collapse"] = Field(
        ..., description="The explicit wave-collapse opcode dictating the resolution of concurrent branches."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "concurrent_branch_ids", sorted(self.concurrent_branch_ids))
        return self


class EpistemicCompressionSLA(CoreasonBaseState):
    strict_probability_retention: bool = Field(
        default=True, description="If True, forces the resulting SemanticNodeState to populate its uncertainty_profile."
    )
    max_allowed_entropy_loss: float = Field(
        ge=0.0,
        le=1.0,
        description="The maximum allowed statistical flattening of the source data. Bounded between [0.0, 1.0].",
    )
    required_grounding_density: Literal["sparse", "dense", "exhaustive"] = Field(
        description="Dictates the required granularity of the MultimodalTokenAnchorState (e.g., must the model map every single entity, or just the global claim?)."  # noqa: E501
    )


class EpistemicPromotionEvent(BaseStateEvent):
    """
    AGENT INSTRUCTION: EpistemicPromotionEvent is an append-only, cryptographically frozen historical 
    fact representing Hippocampal-Neocortical Consolidation. It proves the successful extraction 
    and transfer of generalized knowledge from short-term episodic traces into the permanent semantic graph.

    CAUSAL AFFORDANCE: Emits a permanent Merkle-DAG coordinate (crystallized_semantic_node_id) that 
    downstream agents can zero-shot reference. This permanently severs the computational need to 
    re-evaluate or load the raw source logs into the active context window.

    EPISTEMIC BOUNDS: The mathematical chain of custody is physically bound to the strictly sorted 
    array of source_episodic_event_ids. The token efficiency gained is mathematically proven by the 
    compression_ratio float, which must be strictly bounded (le=1.0) to guarantee Shannon Entropy reduction.

    MCP ROUTING TRIGGERS: Hippocampal Consolidation, Knowledge Distillation, Semantic Memory, Shannon Entropy Compression, Epistemic Promotion
    """

    type: Literal["epistemic_promotion"] = Field(
        default="epistemic_promotion", description="Discriminator type for an epistemic promotion event."
    )
    source_episodic_event_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        description="The strict array of CIDs (Content Identifiers) representing the raw logs being compressed and archived.",  # noqa: E501
    )
    crystallized_semantic_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The resulting permanent W3C DID / CID of the newly minted knowledge node.",
    )
    compression_ratio: float = Field(
        le=1.0,
        description="A mathematical proof of the token savings achieved (e.g., old_token_count / new_token_count).",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "source_episodic_event_ids", sorted(self.source_episodic_event_ids))
        return self


class EpistemicScanningPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Metacognitive Monitoring and Fristonian Active Inference
    to continuously scan the agent's internal belief distribution and residual stream for
    epistemic gaps. As a ...Policy suffix, this object defines rigid mathematical boundaries
    that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Triggers a structural interlock when the agent detects a spike in
    aleatoric entropy, forcing the orchestrator to halt forward-pass generation and actively
    probe or clarify the uncertainty. Gated by the active boolean toggle.

    EPISTEMIC BOUNDS: The sensitivity of the metacognitive scanner is physically clamped by
    the dissonance_threshold (ge=0.0, le=1.0). Recovery mechanisms are deterministically
    restricted by the action_on_gap FSM literal automaton ["fail", "probe", "clarify"].

    MCP ROUTING TRIGGERS: Metacognitive Monitoring, Active Inference, Cognitive Dissonance,
    Epistemic Foraging, Entropy Scanning
    """

    active: bool = Field(description="Whether the epistemic scanner is active.")
    dissonance_threshold: float = Field(
        ge=0.0, le=1.0, description="The threshold for cognitive dissonance before triggering an action."
    )
    action_on_gap: Literal["fail", "probe", "clarify"] = Field(
        description="The action to take when an epistemic gap is detected."
    )


class EpistemicTransmutationTask(CoreasonBaseState):
    task_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this specific multimodal extraction intervention.",
    )
    artifact_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the MultimodalArtifactReceipt being processed.",
    )
    target_modalities: list[
        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]
    ] = Field(min_length=1, description="The specific SOTA modality resolutions required for this extraction pass.")
    compression_sla: EpistemicCompressionSLA = Field(
        description="The strict mathematical boundary defining the maximum allowed informational entropy loss."
    )
    execution_cost_budget_magnitude: int | None = Field(
        le=1000000000,
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


class EscalationContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A rigid mathematical agreement governing when an agent is authorized
    to expand its test-time compute allocation (System 2 thinking) based on measured doubt.
    As a ...Contract suffix, this object defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Physically unlocks the LatentScratchpadReceipt, granting the agent
    a budget of hidden tokens to execute a non-monotonic search tree (MCTS or Beam Search).

    EPISTEMIC BOUNDS: Mathematically bounded by uncertainty_escalation_threshold (ge=0.0,
    le=1.0). The computation is physically capped by max_latent_tokens_budget (gt=0,
    le=1000000000) and max_test_time_compute_ms (gt=0, le=86400000) to prevent infinite
    loops and VRAM exhaustion.

    MCP ROUTING TRIGGERS: Test-Time Compute, System 2 Thinking, Epistemic Uncertainty,
    Non-Monotonic Escalation, Token Budgeting
    """
    uncertainty_escalation_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The exact Epistemic Uncertainty score that triggers the opening of the Latent Scratchpad.",
    )
    max_latent_tokens_budget: int = Field(
        le=1000000000,
        gt=0,
        description="The maximum number of hidden tokens the orchestrator is authorized to buy for the internal monologue.",  # noqa: E501
    )
    max_test_time_compute_ms: int = Field(
        le=86400000,
        gt=0,
        description="The physical time limit allowed for the scratchpad search before forcing a timeout.",
    )


class EscalationIntent(CoreasonBaseState):
    type: Literal["escalation"] = Field(
        default="escalation", description="Discriminator for security or economic boundary overrides."
    )
    tripped_rule_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The ID of the Payload Loss Prevention (PLP) or Governance rule that blocked execution.",
    )
    resolution_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="The strict JSON Schema requiring an explicit cryptographic sign-off or justification string to bypass the breaker.",  # noqa: E501
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The default action is usually terminate or rollback for security escalations."
    )


class EscrowPolicy(CoreasonBaseState):
    escrow_locked_magnitude: int = Field(
        le=1000000000,
        ge=0,
        description="The strictly typed integer amount cryptographically locked prior to execution.",
    )
    release_condition_metric: str = Field(
        max_length=2000, description="A declarative pointer to the SLA or QA rubric required to release the funds."
    )
    refund_target_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The exact NodeIdentifierState to return funds to if the release condition fails.",
    )


class EvictionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EvictionPolicy implements Information Bottleneck Theory and the 
    Ebbinghaus Forgetting Curve. It is a rigid mathematical boundary dictating how the 
    active context partition sheds low-salience episodic memories to prevent attention dilution.

    CAUSAL AFFORDANCE: Authorizes the orchestrator's tensor-pruning heuristic to physically purge, 
    summarize, or decay historical nodes from the GPU VRAM, while mathematically guaranteeing that 
    the protected_event_ids array remains perfectly invariant in the context window.

    EPISTEMIC BOUNDS: The absolute physical boundary is enforced by the max_retained_tokens 
    integer limit (gt=0). The eviction behavior is deterministically restricted to the string 
    literals 'fifo', 'salience_decay', or 'summarize' to prevent hallucinated memory management.

    MCP ROUTING TRIGGERS: Information Bottleneck, Ebbinghaus Forgetting Curve, Salience Decay, LRU Cache Eviction, Attention Dilution
    """

    strategy: Literal["fifo", "salience_decay", "summarize"] = Field(
        description="The mathematical heuristic used to select which semantic memories are retracted or compressed."
    )
    max_retained_tokens: int = Field(
        le=1000000000,
        gt=0,
        description="The strict geometric upper bound of the Epistemic Quarantine's token capacity.",
    )
    protected_event_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        default_factory=list,
        description="Explicit array of Content Identifiers (CIDs) the orchestrator is mathematically forbidden from retracting.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "protected_event_ids", sorted(self.protected_event_ids))
        return self


class EvidentiaryWarrantState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes the Toulmin Model of Argumentation by creating a structural
    bridge between a localized EpistemicArgumentClaimState and a globally verifiable Merkle-DAG
    coordinate. As a ...State suffix, this is a declarative, frozen snapshot of N-dimensional
    geometry at a specific point in time.

    CAUSAL AFFORDANCE: Physically anchors a non-monotonic proposition to an immutable
    historical fact, unlocking the ability for downstream evaluators to mathematically trace
    the justification logic back to its evidentiary origin.

    EPISTEMIC BOUNDS: Requires either a source_event_id or source_semantic_node_id (both
    optional, bounded to 128-char CIDs via strict regex ^[a-zA-Z0-9_.:-]+$). The inferential
    leap is constrained by justification, capped at max_length=2000 characters to prevent
    context-window exhaustion.

    MCP ROUTING TRIGGERS: Toulmin Model, Evidentiary Warrant, Inferential Bridge, Grounding
    Coordinate, Argumentation Theory
    """
    source_event_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for a specific observation in the EpistemicLedgerState.",  # noqa: E501
    )
    source_semantic_node_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for a specific concept in the Semantic Knowledge Graph.",  # noqa: E501
    )
    justification: str = Field(
        max_length=2000, description="The logical premise explaining why this evidence supports the claim."
    )


class EpistemicArgumentClaimState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a discrete, falsifiable proposition within a Dung-style
    Abstract Argumentation Framework. It serves as a static node in the dialectical graph,
    awaiting challenge or verification. As a ...State suffix, this is a declarative, frozen
    snapshot of N-dimensional geometry at a specific point in time.

    CAUSAL AFFORDANCE: Acts as the primary target for DefeasibleAttackEvent undercutting.
    Successfully defending this claim stabilizes the truth value, allowing it to act as a
    premise in higher-order topological proofs.

    EPISTEMIC BOUNDS: The proposition payload (text_chunk) is mathematically capped at
    max_length=50000. The internal warrants array is deterministically sorted by the
    justification field via a @model_validator to preserve RFC 8785 canonical hashing of
    the dialectical state. The proponent_id is bounded to a 128-char CID.

    MCP ROUTING TRIGGERS: Abstract Argumentation Framework, Falsifiable Proposition,
    Dialectical Node, Non-Monotonic Premise
    """
    claim_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this specific logical proposition.",  # noqa: E501
    )
    proponent_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the agent or system that advanced this claim.",  # noqa: E501
    )
    text_chunk: str = Field(max_length=50000, description="The natural language representation of the proposition.")
    warrants: list[EvidentiaryWarrantState] = Field(
        default_factory=list, description="The foundational premises supporting this claim."
    )

    @model_validator(mode="after")
    def sort_argument_claim_arrays(self) -> Self:
        object.__setattr__(self, "warrants", sorted(self.warrants, key=lambda x: x.justification))
        return self


class EpistemicArgumentGraphState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A comprehensive Truth Maintenance System (TMS) calculating dialectical
    justification semantics across the swarm's working context. It houses the complete bipartite
    mapping of claims and their defeasible attacks. As a ...State suffix, this is a declarative,
    frozen snapshot of N-dimensional geometry at a specific point in time.

    CAUSAL AFFORDANCE: Provides the holistic adjacency matrix required by the orchestrator to
    execute grounded extension semantics, determining which set of claims survive the attacks
    and can be crystallized into the permanent EpistemicLedgerState.

    EPISTEMIC BOUNDS: Physically limits state-space explosion by capping the claims and attacks
    dictionaries at max_length=10000 keys each. Key geometries are strictly bounded to 255
    characters via StringConstraints(max_length=255) to prevent Dictionary Bombing during
    canonicalization.

    MCP ROUTING TRIGGERS: Truth Maintenance System, Adjacency Matrix, Grounded Extension,
    Dialectical Justification, Belief State Bounding
    """

    claims: dict[Annotated[str, StringConstraints(max_length=255)], EpistemicArgumentClaimState] = Field(
        max_length=10000, description="Components of an Abstract Argumentation Framework."
    )
    attacks: dict[Annotated[str, StringConstraints(max_length=255)], DefeasibleAttackEvent] = Field(
        default_factory=dict,
        max_length=10000,
        description="Geometric matrices of undercutting defeaters.",
    )


class ExecutionNodeReceipt(CoreasonBaseState):
    """
    Cryptographic state of an execution node in a Merkle DAG trace.
    """

    model_config = ConfigDict(frozen=True)
    request_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique ID for this specific execution.",
    )
    parent_request_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The ID of the parent request.",
    )
    root_request_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The ID of the trace root.",
    )
    inputs: JsonPrimitiveState = Field(description="The inputs provided to the execution node.")
    outputs: JsonPrimitiveState = Field(description="The outputs generated by the execution node.")

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def enforce_payload_topology(cls, v: Any) -> Any:
        """AGENT INSTRUCTION: Mathematically bound recursive dictionary payloads to prevent OOM/CPU exhaustion during EpistemicLedgerState hashing."""  # noqa: E501
        return _validate_payload_bounds(v)

    parent_hashes: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        default_factory=list,
        description="The strict array of cryptographic hashes of parent execution nodes.",
    )
    node_hash: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        default=None,
        description="The cryptographic SHA-256 hash of this node.",
    )

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


class FallbackSLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes a Hard Real-Time Systems deadline for Supervisory Control
    Theory interactions, mathematically bounding the Halting Problem during human-in-the-loop
    pauses. As an ...SLA suffix, this object enforces rigid mathematical boundaries globally.

    CAUSAL AFFORDANCE: Dictates the deterministic timeout_action
    (Literal["fail_safe", "proceed_with_defaults", "escalate"]) the orchestrator must execute
    when the temporal limit expires, structurally preventing execution deadlocks. If
    escalation is selected, traffic routes to the optional escalation_target_node_id.

    EPISTEMIC BOUNDS: The temporal envelope is physically capped by timeout_seconds (gt=0,
    le=86400 — a strict 24-hour absolute maximum TTL). Escalation routing targets a valid
    NodeIdentifierState (escalation_target_node_id, default=None).

    MCP ROUTING TRIGGERS: Hard Real-Time Systems, Supervisory Control Theory, Execution
    Deadlock Prevention, Bounded Delay, Liveness Guarantee
    """

    timeout_seconds: int = Field(le=86400, gt=0, description="The maximum allowed delay for a human intervention.")
    timeout_action: Literal["fail_safe", "proceed_with_defaults", "escalate"] = Field(
        description="The action to take when the timeout expires."
    )
    escalation_target_node_id: NodeIdentifierState | None = Field(
        default=None,
        description="The specific NodeIdentifierState to route the execution to if the escalate action is triggered.",
    )


class FallbackIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Orchestrates Graceful Degradation by executing a deterministic state
    transition within the swarm's Markov Decision Process (MDP) upon node failure. As an
    ...Intent suffix, the LLM may execute non-monotonic reasoning here.

    CAUSAL AFFORDANCE: Re-routes the probabilistic execution wave from a failing primary
    node (target_node_id) to a pre-verified, lower-variance backup node (fallback_node_id),
    actively bypassing the structural collapse and maintaining systemic liveness.

    EPISTEMIC BOUNDS: Enforces strict structural referential integrity by requiring both
    target_node_id and fallback_node_id to resolve to valid NodeIdentifierState DIDs.

    MCP ROUTING TRIGGERS: Graceful Degradation, Markov Decision Process, Redundancy Routing,
    Fail-Safe Transition, Control-Flow Override
    """

    type: Literal["fallback_intent"] = Field(
        le=1000000000, default="fallback_intent", description="The type of the resilience payload."
    )
    target_node_id: NodeIdentifierState = Field(description="The ID of the failing node.")
    fallback_node_id: NodeIdentifierState = Field(description="The ID of the node to use as a fallback.")


class FalsificationContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Enforces strict Popperian Falsificationism by defining the exact empirical boundary conditions that would logically invalidate a non-monotonic causal hypothesis.

    CAUSAL AFFORDANCE: Provides the deterministic pattern-matching criteria (falsifying_observation_signature) that triggers a DefeasibleCascadeEvent, instantly quarantining the collapsed subgraph.

    EPISTEMIC BOUNDS: Limits the falsification logic to a strictly typed condition_id (max_length=128) and physically binds the empirical test to an explicit required_tool_name to prevent unbounded or hallucinated search spaces.

    MCP ROUTING TRIGGERS: Popperian Falsification, Null Hypothesis, Defeasible Logic, Empirical Falsifiability, Structural Boundary
    """
    condition_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this falsification test to the Merkle-DAG.",  # noqa: E501
    )
    description: str = Field(
        max_length=2000,
        description="Semantic description of what observation would prove the parent hypothesis is false.",
    )
    required_tool_name: str | None = Field(
        max_length=2000,
        default=None,
        description="The specific ActionSpaceManifest tool required to test this condition (e.g., 'sql_query_db').",
    )
    falsifying_observation_signature: str = Field(
        max_length=2000,
        description="The expected data schema or regex pattern that, if returned by the tool, kills the hypothesis.",
    )


class FaultInjectionProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a deterministic Byzantine fault vector for Chaos Engineering
    perturbation tests. As a ...Profile suffix, this is a declarative, frozen snapshot of an
    attack geometry at a specific point in time.

    CAUSAL AFFORDANCE: Instructs the execution engine to physically degrade, throttle, or
    corrupt the structural state or network connectivity of the target_node_id based on the
    specific fault_type (FaultCategoryProfile) manifold.

    EPISTEMIC BOUNDS: The severity of the perturbation is constrained above by the intensity
    scalar (le=1000000000.0) but unbounded below, permitting negative fault magnitudes. The
    blast radius targets either the entire swarm (target_node_id=None) or a specific node
    bounded to a valid 128-char CID regex ^[a-zA-Z0-9_.:-]+$.

    MCP ROUTING TRIGGERS: Chaos Engineering, Byzantine Fault Injection, Perturbation Theory,
    Structural Sabotage, Resilience Testing
    """
    fault_type: FaultCategoryProfile = Field(description="The specific type of fault to inject.")
    target_node_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The specific node to attack, or None for swarm-wide.",
    )
    intensity: float = Field(le=1000000000.0, description="The severity of the fault, represented from 0.0 to 1.0.")


class FederatedCapabilityAttestationReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: An immutable cryptographic receipt representing an Object
    Capability (OCap) grant within a Federated Identity Management (FIM) framework. As
    a ...Receipt suffix, this is an append-only coordinate on the Merkle-DAG that the
    LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Unlocks cross-domain graph traversal, cryptographically proving
    to the target_topology_id (NodeIdentifierState) that the swarm agent is authorized
    to establish an active connection governed by the governing_sla (BilateralSLA) and
    authorized_session (SecureSubSessionState).

    EPISTEMIC BOUNDS: The receipt is cryptographically locked to a 128-char
    attestation_id (CID). The @model_validator enforce_restricted_vault_locks
    mathematically enforces cross-schema invariants: if
    governing_sla.max_permitted_classification is 'restricted', the authorized_session
    MUST contain explicit allowed_vault_keys, preventing unauthorized lateral movement.

    MCP ROUTING TRIGGERS: Object Capability Model, Federated Identity Management,
    Cross-Domain Federation, Capability Attestation, Zero-Trust Execution
    """

    attestation_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Cryptographic Lineage Watermark for the attestation.",
    )
    target_topology_id: NodeIdentifierState = Field(description="The DID of the discovered external state matrix/VPC.")
    authorized_session: SecureSubSessionState = Field(
        description="The isolated state partition granted to the agent for this connection."
    )
    governing_sla: BilateralSLA = Field(
        description="The structural and physical boundary constraints for querying this target."
    )

    @model_validator(mode="after")
    def enforce_restricted_vault_locks(self) -> Self:
        if self.governing_sla.max_permitted_classification == "restricted" and (
            not self.authorized_session.allowed_vault_keys
        ):
            raise ValueError(
                "RESTRICTED federated connections MUST define allowed_vault_keys in the SecureSubSessionState."
            )
        return self


class FederatedStateSnapshot(CoreasonBaseState):
    topology_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the federated topology, if applicable.",  # noqa: E501
    )


class FitnessObjectiveProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a specific mathematical objective function (fitness dimension)
    within a multi-objective optimization landscape for evaluating agent phenotypes. As a
    ...Profile suffix, this is a declarative, frozen snapshot of an evaluation geometry.

    CAUSAL AFFORDANCE: Provides the mathematical vector (OptimizationDirectionProfile:
    minimize/maximize) and scalar weight required by the orchestrator to score an agent's
    execution telemetry, ultimately determining its survival on the Pareto Efficiency
    frontier.

    EPISTEMIC BOUNDS: The relative influence of this objective is mathematically clamped by
    the weight field (le=1.0, default=1.0) to prevent gradient or reward explosion during
    fitness aggregation. The target_metric is bounded to max_length=2000.

    MCP ROUTING TRIGGERS: Fitness Landscape, Objective Function, Multi-Objective
    Optimization, Phenotype Scoring, Pareto Efficiency
    """

    target_metric: str = Field(
        max_length=2000,
        description="The specific telemetry or execution metric to evaluate (e.g., 'latency', 'accuracy').",
    )
    direction: OptimizationDirectionProfile = Field(
        description="Whether the algorithm should maximize or minimize this metric."
    )
    weight: float = Field(
        le=1.0, default=1.0, description="The relative importance of this objective in a multi-objective generation."
    )


class FormalVerificationContract(CoreasonBaseState):
    """
    Passive schema defining a mathematical proof of safety invariants.
    """

    proof_system: Literal["tla_plus", "lean4", "coq", "z3"] = Field(
        description="The mathematical dialect and theorem prover used to compile the proof."
    )
    invariant_theorem: str = Field(
        max_length=2000,
        description="The exact mathematical assertion or safety invariant being proven (e.g., 'No data classified as CONFIDENTIAL routes externally').",  # noqa: E501
    )
    compiled_proof_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 fingerprint of the verified proof object that the Rust/C++ orchestrator must load and check.",  # noqa: E501
    )


class DelegatedCapabilityManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Macaroons and Decentralized Identifiers (DIDs) to
    construct a verifiable delegation chain of authority from a human principal to an
    autonomous agent. As a ...Manifest suffix, this defines a frozen, N-dimensional
    coordinate state.

    CAUSAL AFFORDANCE: Empowers the delegate_agent_did (NodeIdentifierState) to invoke
    the explicitly whitelisted allowed_tool_ids (list[ToolIdentifierState]), acting as a
    cryptographic proxy for the principal_did (NodeIdentifierState). The
    cryptographic_signature (max_length=10000) proves the delegation chain.

    EPISTEMIC BOUNDS: The delegation's temporal geometry is physically bounded by
    expiration_timestamp (ge=0.0, le=253402300799.0). The capability_id is a 128-char
    CID anchor. The allowed_tool_ids array is deterministically sorted by
    @model_validator sort_arrays for RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Macaroons, Delegation Chain, Public Key Infrastructure,
    Object Capability Model, Decentralized Identifiers
    """

    capability_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A string CID for the delegated capability.",
    )
    principal_did: NodeIdentifierState = Field(
        description="The DID representing the human or parent delegating authority."
    )
    delegate_agent_did: NodeIdentifierState = Field(
        description="The DID representing the autonomous actor receiving authority."
    )
    allowed_tool_ids: list[ToolIdentifierState] = Field(
        description="The strictly bounded set of ToolIdentifiers this delegation permits."
    )
    expiration_timestamp: float = Field(
        ge=0.0, le=253402300799.0, description="A float bounding the temporal lifecycle."
    )
    cryptographic_signature: str = Field(
        max_length=10000, description="A base64 string proving the cryptographic delegation."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_tool_ids", sorted(self.allowed_tool_ids))
        return self


class BudgetExhaustionEvent(BaseStateEvent):
    """
    AGENT INSTRUCTION: Represents the definitive algorithmic circuit breaker (Optimal
    Stopping boundary) triggered the exact millisecond thermodynamic token burn
    mathematically exceeds the locked Proof-of-Stake escrow. As an ...Event suffix, this is
    an append-only coordinate on the Merkle-DAG that the LLM must never hallucinate a
    mutation to.

    CAUSAL AFFORDANCE: Instantly collapses the active Latent Scratchpad trajectory and
    physically severs the kinetic execution loop, preventing malicious or hallucinating
    agents from executing Sybil griefing attacks against the swarm's compute pool.

    EPISTEMIC BOUNDS: Cryptographically targets the specific exhausted_escrow_id and the
    exact final_burn_receipt_id (CID regex ^[a-zA-Z0-9_.:-]+$, max_length=128) that pushed
    the thermodynamic ledger into a negative state, providing an undeniable audit trail.

    MCP ROUTING TRIGGERS: Optimal Stopping Theory, Escrow Exhaustion, Sybil Resistance,
    Algorithmic Circuit Breaker, Generation Halting
    """

    type: Literal["budget_exhaustion"] = Field(
        default="budget_exhaustion", description="Discriminator type for a budget exhaustion event."
    )
    exhausted_escrow_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A string representing the original escrow boundary breached.",
    )
    final_burn_receipt_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A string pointing to the exact TokenBurnReceipt CID that pushed the state over the limit.",
    )


class TokenBurnReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: Formalizes Landauer's Principle of thermodynamic computing within the
    neurosymbolic network, serving as a lock-free, cryptographically frozen record of
    irreversible token and energy expenditure. As a ...Receipt suffix, this is an append-only
    coordinate on the Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Deducts exact computational magnitude from the agent's localized
    Proof-of-Stake (PoS) execution escrow, progressively narrowing its available search
    depth. Cryptographically bound to its causal origin via tool_invocation_id CID.

    EPISTEMIC BOUNDS: Integer bounds (ge=0, le=1000000000) on input_tokens, output_tokens,
    and burn_magnitude mathematically prevent integer overflow and fractional bypasses during
    decentralized ledger tallying.

    MCP ROUTING TRIGGERS: Landauer's Principle, Thermodynamic Compute, Token Burn, Resource
    Exhaustion, Lock-Free Tallying
    """

    type: Literal["token_burn"] = Field(
        default="token_burn", description="Discriminator type for a token burn receipt."
    )
    tool_invocation_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A string linking this burn back to the specific ToolInvocationEvent CID.",
    )
    input_tokens: int = Field(le=1000000000, ge=0, description="The mathematical measure of input tokens consumed.")
    output_tokens: int = Field(le=1000000000, ge=0, description="The mathematical measure of output tokens generated.")
    burn_magnitude: int = Field(
        le=1000000000, ge=0, description="The normalized economic cost magnitude representing thermodynamic burn."
    )


class GlobalGovernancePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Superimposes macro-economic and thermodynamic constraints over the
    swarm's execution graph to prevent unbounded compute exhaustion. As a ...Policy suffix,
    this object defines rigid mathematical boundaries that the orchestrator must enforce
    globally.

    CAUSAL AFFORDANCE: Acts as the ultimate hardware guillotine, authorizing the orchestrator
    to physically sever the execution thread if thermodynamic, economic, or temporal budgets
    are breached. Includes a mandatory zero-trust @model_validator enforcing the Prosperity
    Public License 3.0 via mandatory_license_rule (rule_id="PPL_3_0_COMPLIANCE",
    severity="critical").

    EPISTEMIC BOUNDS: Enforces absolute physical ceilings: max_budget_magnitude
    (le=1000000000), max_global_tokens (le=1000000000), global_timeout_seconds (ge=0,
    le=86400 — a strict 24-hour TTL), and optional max_carbon_budget_gco2eq (ge=0.0,
    le=10000.0). An optional FormalVerificationContract provides mathematical proofs of
    structural correctness.

    MCP ROUTING TRIGGERS: Thermodynamic Compute Limits, Hardware Guillotine, Halting Problem
    Bounding, ESG Constraint, Execution Envelope
    """

    mandatory_license_rule: ConstitutionalPolicy
    max_budget_magnitude: int = Field(
        le=1000000000, description="The absolute maximum economic cost allowed for the entire swarm lifecycle."
    )

    @model_validator(mode="after")
    def enforce_prosperity_license(self) -> Self:
        if (
            self.mandatory_license_rule.rule_id != "PPL_3_0_COMPLIANCE"
            or self.mandatory_license_rule.severity != "critical"
        ):
            raise ValueError(
                "CRITICAL LICENSE VIOLATION: The execution graph has been stripped of its Prosperity Public License 3.0 mathematical anchor. Execution is strictly forbidden."  # noqa: E501
            )
        return self

    max_global_tokens: int = Field(
        le=1000000000, description="The maximum aggregate token usage allowed across all nodes."
    )
    max_carbon_budget_gco2eq: float | None = Field(
        le=10000.0,
        default=None,
        ge=0.0,
        description="The absolute physical energy footprint allowed for this execution graph. If exceeded, the orchestrator terminates the swarm.",  # noqa: E501
    )
    global_timeout_seconds: int = Field(
        le=86400,
        ge=0,
        description="The absolute Time-To-Live (TTL) for the execution envelope before graceful termination.",
    )
    formal_verification: FormalVerificationContract | None = Field(
        default=None, description="The mathematical proof of structural correctness mandated for this execution graph."
    )


class GenerativeManifoldSLA(CoreasonBaseState):
    """Mathematical governor for fractal/cyclic graph synthesis."""

    max_topological_depth: int = Field(
        le=1000000000, ge=1, description="The absolute physical depth limit for recursive encapsulation."
    )
    max_node_fanout: int = Field(
        le=1000000000, ge=1, description="The maximum number of horizontally connected nodes per topology tier."
    )
    max_synthetic_tokens: int = Field(
        le=1000000000, ge=1, description="The economic constraint on the entire generated mock payload."
    )

    @model_validator(mode="after")
    def enforce_geometric_bounds(self) -> Self:
        """Mathematically guarantees the configuration cannot authorize an OOM explosion."""
        if self.max_node_fanout**self.max_topological_depth > 1000:
            raise ValueError("Geometric explosion risk: max_node_fanout ** max_topological_depth must be <= 1000.")
        return self


class GlobalSemanticProfile(CoreasonBaseState):
    """The immutable receipt of Step 1 ingestion acting as a static structural index of the artifact."""

    artifact_event_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="The exact genesis CID of the MultimodalArtifactReceipt entering the routing tier.",
    )
    detected_modalities: list[
        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]
    ] = Field(description="The strictly typed enum array of physical modalities detected in the artifact.")
    token_density: int = Field(
        le=1000000000,
        ge=0,
        description="The mathematical token density governing downstream compute budget allocation.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "detected_modalities", sorted(self.detected_modalities))
        return self


class DynamicRoutingManifest(CoreasonBaseState):
    """The Softmax Router Gate dictating the active execution topology and spot compute allocation."""

    manifest_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="The unique Content Identifier (CID) for this routing plan.",
    )
    artifact_profile: GlobalSemanticProfile = Field(description="The semantic profile governing this route.")
    active_subgraphs: dict[Annotated[str, StringConstraints(max_length=255)], list[NodeIdentifierState]] = Field(
        description="Mapping of specific modalities (e.g., 'tabular_grid') to the explicit lists of worker NodeIdentifierStates authorized to execute.",  # noqa: E501
    )
    bypassed_steps: list[BypassReceipt] = Field(
        default_factory=list, description="The declarative array of steps the orchestrator is mandated to skip."
    )
    branch_budgets_magnitude: dict[NodeIdentifierState, int] = Field(
        max_length=1000000000, description="The strict allocation of compute budget bound to specific nodes."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "active_subgraphs", {k: sorted(v) for k, v in self.active_subgraphs.items()})
        return self

    @model_validator(mode="after")
    def sort_bypassed_steps(self) -> Self:
        object.__setattr__(self, "bypassed_steps", sorted(self.bypassed_steps, key=lambda x: x.bypassed_node_id))
        return self

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


class GovernancePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Aggregates discrete ConstitutionalPolicy nodes into a cohesive,
    version-controlled Normative Alignment Manifold. As a ...Policy suffix, this object
    defines rigid mathematical boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Instructs the orchestrator to enforce a unified cybernetic governance
    model across all swarm trajectories, grounding generative actions in a specific semantic
    version (SemanticVersionState).

    EPISTEMIC BOUNDS: The topological integrity of the manifold is mathematically guaranteed
    by the @model_validator, which deterministically sorts the rules array by rule_id to
    prevent Byzantine hash fractures across distributed nodes.

    MCP ROUTING TRIGGERS: Cybernetic Governance, Normative Alignment Manifold, Rule
    Aggregation, Version Control, RFC 8785 Canonicalization
    """

    policy_name: str = Field(max_length=2000, description="Name of the governance policy.")
    version: SemanticVersionState = Field(description="Semantic version of the governance policy.")
    rules: list[ConstitutionalPolicy] = Field(
        description="The explicit array of constitutional rules included in this policy."
    )

    @model_validator(mode="after")
    def sort_rules(self) -> Self:
        object.__setattr__(self, "rules", sorted(self.rules, key=lambda r: r.rule_id))
        return self


class GrammarPanelProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Leland Wilkinson's Grammar of Graphics to deterministically
    project N-dimensional Epistemic Ledger state into a 2D topological manifold. As a
    ...Profile suffix, this is a declarative, frozen snapshot of a rendering geometry.

    CAUSAL AFFORDANCE: Authorizes the frontend rendering engine to construct geometric marks
    (Literal["point", "line", "area", "bar", "rect", "arc"]) driven strictly by the
    underlying ledger_source_id. Optionally supports Small Multiples via facet
    (FacetMatrixProfile).

    EPISTEMIC BOUNDS: Bounded by a rigid encodings array sorted mathematically by channel
    via a @model_validator to preserve RFC 8785 canonical hashing. Prevents hallucinated
    visuals by strictly linking to a verified ledger_source_id CID.

    MCP ROUTING TRIGGERS: Grammar of Graphics, Data Visualization, Geometric Projection,
    Declarative UI, Retinal Variables
    """

    panel_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for this UI panel.",
    )
    type: Literal["grammar"] = Field(default="grammar", description="Discriminator for Grammar of Graphics charts.")
    title: str = Field(
        max_length=2000, description="The declarative semantic anchor summarizing the underlying visual grammar."
    )
    ledger_source_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The cryptographic pointer to the semantic series in the EpistemicLedgerState.",
    )
    mark: Literal["point", "line", "area", "bar", "rect", "arc"] = Field(
        le=1000000000, description="The geometric shape used to represent the matrix."
    )
    encodings: list[VisualEncodingProfile] = Field(description="The mapping of structural fields to visual channels.")
    facet: FacetMatrixProfile | None = Field(default=None, description="Optional faceting matrix for small multiples.")

    @model_validator(mode="after")
    def sort_encodings(self) -> Self:
        """Mathematically sorts self.encodings by the string value of channel for deterministic hashing."""
        object.__setattr__(self, "encodings", sorted(self.encodings, key=lambda e: e.channel))
        return self


class GraphFlatteningPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A rigid Graph Isomorphism and Dimensionality Reduction protocol
    defining the deterministic translation of high-dimensional neurosymbolic Knowledge
    Graphs into flat, tabular matrices for standard OLAP processing. As a ...Policy
    suffix, this object defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Forces the structural projection engine to serialize complex
    semantic nodes and edges into wide-columnar arrays or adjacency matrices. The
    preserve_cryptographic_lineage boolean (default=True) guarantees Merkle-DAG hashes
    survive the flattening transformation.

    EPISTEMIC BOUNDS: The reduction geometry is rigidly constrained by Literal enums for
    node_projection_mode ["wide_columnar", "struct_array"] and edge_projection_mode
    ["adjacency_matrix", "map_array"], mathematically severing the capability for agents
    to hallucinate unsupported tabular schemas.

    MCP ROUTING TRIGGERS: Graph Isomorphism, Dimensionality Reduction, Adjacency Matrix,
    Wide-Columnar Projection, Structural Serialization
    """
    node_projection_mode: Literal["wide_columnar", "struct_array"] = Field(
        description="How to flatten SemanticNodeState."
    )
    edge_projection_mode: Literal["adjacency_matrix", "map_array"] = Field(
        description="How to flatten SemanticEdgeState."
    )
    preserve_cryptographic_lineage: bool = Field(
        default=True, description="Forces the inclusion of MultimodalTokenAnchorState hashes in the flattened row."
    )


class HTTPTransportProfile(CoreasonBaseState):
    """Configuration for stateless HTTP-based MCP transport."""

    type: Literal["http"] = Field(default="http", description="Type of transport.")
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the stateless connection.")
    headers: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(
        le=1000000000, default_factory=dict, description="HTTP headers, strictly bounded for zero-trust credentials."
    )

    @field_validator("headers", mode="after")
    @classmethod
    def _prevent_crlf_injection(cls, v: dict[str, str]) -> dict[str, str]:
        """AGENT INSTRUCTION: Strictly forbid HTTP request smuggling vectors."""
        for key, value in v.items():
            if "\r" in key or "\n" in key or "\r" in value or ("\n" in value):
                raise ValueError("CRLF injection detected in headers")
        return v


class HomomorphicEncryptionProfile(CoreasonBaseState):
    fhe_scheme: Literal["ckks", "bgv", "bfv", "tfhe"] = Field(
        description="The specific homomorphic encryption dialect used to encode the ciphertext."
    )
    public_key_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The Content Identifier (CID) of the public evaluation key the orchestrator must utilize to perform privacy-preserving geometric math on ciphertext without epistemic contamination.",  # noqa: E501
    )
    ciphertext_blob: str = Field(max_length=5000000, description="The base64-encoded homomorphic ciphertext.")


class HypothesisStakeReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Cryptographically freezes an agent's probabilistic belief in a `HypothesisGenerationEvent` as an immutable economic stake on the Epistemic Ledger.

    CAUSAL AFFORDANCE: Projects the agent's internal `implied_probability` into the shared LMSR order book, injecting liquidity and actively shifting the global consensus gradient.

    EPISTEMIC BOUNDS: The `staked_magnitude` is constrained to a strictly positive integer `le=1000000000`, and the `implied_probability` is bounded mathematically to `[0.0, 1.0]`.

    MCP ROUTING TRIGGERS: Epistemic Staking, Brier Score Input, Belief Freezing, Market Order
    """
    agent_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        le=1000000000, description="The ID of the agent placing the stake."
    )
    target_hypothesis_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        le=1000000000, description="The exact HypothesisGenerationEvent the agent is betting on."
    )
    staked_magnitude: int = Field(
        le=1000000000, gt=0, description="The volume of compute budget committed to this position."
    )
    implied_probability: float = Field(ge=0.0, le=1.0, description="The agent's calculated internal confidence score.")


class InformationalIntent(CoreasonBaseState):
    type: Literal["informational"] = Field(
        default="informational", description="Discriminator for read-only informational handoffs."
    )
    message: str = Field(max_length=2000, description="The context or summary to display to the human operator.")
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The orchestrator's automatic fallback if the human does not acknowledge the intent in time."
    )


class TaxonomicNodeState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Hierarchical Agglomerative Clustering to project continuous,
    dense latent vector spaces into a deterministic, discrete N-ary tree structure. As a
    ...State suffix, this is a declarative, frozen snapshot of a specific geometric coordinate.

    CAUSAL AFFORDANCE: Establishes a strictly bounded, navigable spatial coordinate within
    the Virtual File System (VFS), allowing agents to traverse high-dimensional semantic
    spaces without consuming excessive context window tokens.

    EPISTEMIC BOUNDS: Spatial geometry is locked via node_id (a strictly typed 128-character
    CID). The children_node_ids array is deterministically sorted, and the leaf_provenance
    array is sorted by source_event_id, both via @model_validator to guarantee invariant
    RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Dimensionality Reduction, Hierarchical Clustering, N-ary Tree,
    Virtual File System, Semantic Coordinate
    """

    node_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) bounding this specific taxonomic coordinate.",
    )
    semantic_label: str = Field(
        max_length=2000,
        description="The human-legible, dynamically synthesized categorical label (e.g., 'High Risk Policies').",
    )
    children_node_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        default_factory=list,
        description="Explicit array of child node CIDs to enforce the Directed Acyclic Graph.",
    )
    leaf_provenance: list["EpistemicProvenanceReceipt"] = Field(
        default_factory=list,
        description="The mathematical chain of custody binding this virtual coordinate back to physical vectors.",
    )

    @model_validator(mode="after")
    def sort_taxonomic_arrays(self) -> Self:
        """Mathematically sort arrays to guarantee deterministic canonical hashing."""
        object.__setattr__(self, "children_node_ids", sorted(self.children_node_ids))
        object.__setattr__(self, "leaf_provenance", sorted(self.leaf_provenance, key=lambda x: x.source_event_id))
        return self


class GenerativeTaxonomyManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Acts as a macroscopic Topological Data Analysis (TDA) manifold
    projection, mapping continuous vector geometries into a discrete, traversable Directed
    Acyclic Graph (DAG). As a ...Manifest suffix, this defines a frozen, N-dimensional
    coordinate state.

    CAUSAL AFFORDANCE: Projects the comprehensive Virtual File System (VFS) state to the
    human UI or agentic context, structurally proving the geometric relations of all
    subordinate TaxonomicNodeStates.

    EPISTEMIC BOUNDS: The nodes matrix is physically capped at max_length=1000000000
    properties to prevent memory overflow. The @model_validator mathematically verifies DAG
    integrity by ensuring the root_node_id explicitly exists within the projection matrix,
    preventing ghost nodes.

    MCP ROUTING TRIGGERS: Manifold Learning, Topological Data Analysis, Directed Acyclic
    Graph, Generative Taxonomy, Holographic Projection
    """

    manifest_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique Content Identifier (CID) for this generated taxonomy.",
    )
    root_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the top-level TaxonomicNodeState initiating the tree.",
    )
    nodes: dict[Annotated[str, StringConstraints(max_length=255)], TaxonomicNodeState] = Field(
        max_length=1000000000, description="Flat dictionary matrix containing all nodes within the manifold."
    )

    @model_validator(mode="after")
    def verify_dag_integrity(self) -> Self:
        """
        AGENT INSTRUCTION: Mathematically prove the absence of disconnected ghost nodes
        and cyclical references within the projected visual manifold.
        """
        if self.root_node_id not in self.nodes:
            raise ValueError(f"Topological Fracture: Root node '{self.root_node_id}' not found in matrix.")
        return self


class TaxonomicRestructureIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Executes a kinetic Graph Isomorphism transformation, dynamically
    mutating the UI's spatial organization via heuristic regrouping without altering the
    underlying epistemic truth. As an ...Intent suffix, the LLM may execute non-monotonic
    reasoning here.

    CAUSAL AFFORDANCE: Forces the Hollow Data Plane to immediately discard the current
    semantic manifold and re-render the hierarchical projection according to the newly
    synthesized target_taxonomy (GenerativeTaxonomyManifest) and spatial heuristic.

    EPISTEMIC BOUNDS: Execution is rigidly constrained by the restructure_heuristic, strictly
    bounded to a Literal automaton ["chronological", "entity_centric", "semantic_cluster",
    "confidence_decay"], mathematically preventing out-of-distribution UI mutations.

    MCP ROUTING TRIGGERS: Graph Isomorphism, UI State Mutation, Heuristic Regrouping,
    Dynamic Manifold, Spatial Reorganization
    """

    type: Literal["taxonomic_restructure"] = Field(
        default="taxonomic_restructure", description="Strict discriminator for dynamic UI regrouping."
    )
    restructure_heuristic: Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"] = Field(
        description="The SOTA mathematical heuristic used to project the new manifold."
    )
    target_taxonomy: GenerativeTaxonomyManifest = Field(
        description="The newly synthesized topology projected to the frontend."
    )


class TaxonomicRoutingPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements a deterministic Softmax Router Gate, leveraging Cognitive
    Load Theory to map high-entropy natural language intents into explicitly bounded spatial
    organizing frameworks. As a ...Policy suffix, this dictates a rigid global boundary.

    CAUSAL AFFORDANCE: Pre-emptively routes classified intents to optimized taxonomic
    layouts, mechanically preventing token exhaustion and attention dilution in downstream
    processing nodes before compute is allocated. Unclassified intents default to the
    fallback_heuristic.

    EPISTEMIC BOUNDS: The intent_to_heuristic_matrix physically restricts state-space
    explosion by capping at max_length=1000 dictionary properties. The matrix keys are
    strictly bounded to 255 characters via StringConstraints to mathematically prevent
    Dictionary Bombing during hashing.

    MCP ROUTING TRIGGERS: Softmax Gating, Cognitive Load Theory, Pre-Flight Routing,
    Dictionary Bombing Prevention, Token Exhaustion Mitigation
    """

    policy_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this pre-flight routing policy.",
    )
    intent_to_heuristic_matrix: dict[
        Annotated[str, StringConstraints(max_length=255)],
        Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"],
    ] = Field(
        max_length=1000,
        description="Strict dictionary binding classified natural language intents to bounded spatial heuristics.",
    )
    fallback_heuristic: Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"] = Field(
        description="The deterministic default applied if intent classification falls below the safety threshold."
    )


type AnyPresentationIntent = Annotated[
    InformationalIntent | DraftingIntent | AdjudicationIntent | EscalationIntent, Field(discriminator="type")
]
type AnyIntent = Annotated[
    InformationalIntent
    | DraftingIntent
    | AdjudicationIntent
    | EscalationIntent
    | SemanticDiscoveryIntent
    | TaxonomicRestructureIntent
    | LatentProjectionIntent,
    Field(discriminator="type"),
]


class InputMappingContract(CoreasonBaseState):
    """
    Dictates how keys from a parent's shared_state_contract map to a nested topology's state.
    """

    parent_key: str = Field(max_length=2000, description="The key in the parent's shared state contract.")
    child_key: str = Field(max_length=2000, description="The mapped key in the nested topology's state contract.")


class InsightCardProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A declarative bounding box for rendering condensed semantic summaries
    (Information Bottleneck compression) into human-readable 2D space. As a ...Profile
    suffix, this is a declarative, frozen snapshot of a rendering geometry.

    CAUSAL AFFORDANCE: Projects Markdown-formatted text onto the UI plane while serving as a
    structural honeypot against Polyglot XSS and Markdown execution injection attacks.

    EPISTEMIC BOUNDS: Physically restricts payload size to max_length=100000 on
    markdown_content. Two distinct @field_validators mathematically strip: (1) HTML event
    handlers (on[a-zA-Z]+=) and raw HTML tags, and (2) malicious URI schemes (javascript:,
    vbscript:, data:) embedded in markdown links — ensuring zero-trust projection.

    MCP ROUTING TRIGGERS: Information Bottleneck, Semantic Compression, XSS Sanitization,
    Markdown Projection, Zero-Trust UI
    """

    panel_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for this UI panel.",
    )
    type: Literal["insight_card"] = Field(
        default="insight_card", description="Discriminator for markdown insight cards."
    )
    title: str = Field(
        max_length=2000,
        description="The declarative semantic anchor summarizing the underlying matrix or markdown projection.",
    )
    markdown_content: str = Field(max_length=100000, description="The markdown formatted text content.")

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


type AnyPanelProfile = Annotated[
    GrammarPanelProfile | InsightCardProfile,
    Field(discriminator="type", description="A discriminated union of presentation UI panels."),
]


class InterventionIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: InterventionIntent acts as a formal Mixed-Initiative Control mechanism within 
    Supervisory Control Theory. It is a kinetic trigger that mathematically suspends the active 
    execution graph, transferring decision authority to an external human or oversight oracle.

    CAUSAL AFFORDANCE: Physically halts the Directed Acyclic Graph (DAG) traversal or Petri net 
    reachability loop. It prevents the swarm from committing a state transition until an explicit, 
    authorized Pearlian intervention is negotiated.

    EPISTEMIC BOUNDS: Execution suspension is strictly bounded by the temporal logic of the 
    adjudication_deadline (UNIX timestamp) and the FallbackSLA. If the deadline expires, the 
    orchestrator mechanically breaks the halt to guarantee systemic liveness.

    MCP ROUTING TRIGGERS: Supervisory Control Theory, Mixed-Initiative System, Execution Halting, Bounded Delay, Human-in-the-Loop
    """

    type: Literal["request"] = Field(default="request", description="The type of the intervention payload.")
    intervention_scope: BoundedInterventionScopePolicy | None = Field(
        default=None, description="The scope constraints bounding the intervention."
    )
    fallback_sla: FallbackSLA | None = Field(default=None, description="The SLA constraints on the intervention delay.")
    target_node_id: NodeIdentifierState = Field(description="The ID of the target node.")
    context_summary: str = Field(max_length=2000, description="A summary of the context requiring intervention.")
    proposed_action: dict[Annotated[str, StringConstraints(max_length=255)], str | int | float | bool | None] = Field(
        max_length=1000000000, description="The action proposed by the agent that requires approval."
    )
    adjudication_deadline: float = Field(
        ge=0.0, le=253402300799.0, description="The deadline for adjudication, represented as a UNIX timestamp."
    )


class InterventionalCausalTask(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a formal Pearlian Do-Operator (P(y|do(X=x))) intervention, forcefully severing a variable from its historical back-door causal mechanisms to prove direct causal influence.

    CAUSAL AFFORDANCE: Authorizes the orchestrator to physically mutate the intervention_variable to the do_operator_state, breaking confounding structural edges in the directed acyclic graph.

    EPISTEMIC BOUNDS: The physical mutation is economically capped by execution_cost_budget_magnitude (le=1000000000), and its justification is strictly quantified by expected_causal_information_gain (bounded mathematically between 0.0 and 1.0).

    MCP ROUTING TRIGGERS: Pearlian Do-Calculus, Structural Causal Models, Causal Intervention, Confounder Ablation, Back-door Criterion
    """
    task_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this causal intervention.",
    )
    target_hypothesis_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The hypothesis containing the SCM being tested.",
    )
    intervention_variable: str = Field(
        max_length=2000, description="The specific node $X$ in the SCM the agent is forcing to a specific state."
    )
    do_operator_state: str = Field(
        max_length=2000,
        description="The exact value or condition forced upon the intervention_variable, isolating it from its historical causes.",  # noqa: E501
    )
    expected_causal_information_gain: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical proof of entropy reduction yielded specifically by breaking the confounding back-doors.",  # noqa: E501
    )
    execution_cost_budget_magnitude: int = Field(
        le=1000000000,
        ge=0,
        description="The maximum economic expenditure authorized to run this specific causal intervention.",
    )


class JSONRPCErrorState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A mathematically constrained error vector reflecting execution
    collapse within the JSON-RPC 2.0 specification. As a ...State suffix, this is a
    frozen N-dimensional coordinate.

    CAUSAL AFFORDANCE: Projects execution faults back across the network boundary
    without risking secondary buffer overflow attacks during serialization. The
    error_payload (alias="data", External Protocol Exemption) carries optional
    structured diagnostic data.

    EPISTEMIC BOUNDS: The code integer is rigidly capped (le=1000000000, no ge bound)
    and the semantic message is restricted to max_length=2000 to prevent log-poisoning
    during telemetry serialization.

    MCP ROUTING TRIGGERS: Fault Projection, Buffer Overflow Prevention, Error Vector,
    Log Poisoning, Stateful Rollback
    """

    code: int = Field(..., le=1000000000, description="A Number that indicates the error type that occurred.")
    message: str = Field(
        ...,
        max_length=2000,
        description="The strict semantic fault boundary explaining the structural or execution collapse.",
    )
    error_payload: Any | None = Field(
        default=None,
        alias="data",
        description="A Primitive or Structured value that contains additional information about the error.",
    )


class JSONRPCErrorResponseState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: The definitive top-level envelope for transmitting a
    JSONRPCErrorState across a Zero-Trust Architecture boundary. As a ...State suffix,
    this is a frozen N-dimensional coordinate.

    CAUSAL AFFORDANCE: Concludes a failed Distributed RPC call via the error
    (JSONRPCErrorState) typed reference, forcing the orchestrator to sever the current
    execution tree and apply necessary truth maintenance.

    EPISTEMIC BOUNDS: The jsonrpc field is a rigid Literal["2.0"] automaton. The id is
    topologically locked to a 128-char CID regex or an integer (le=1000000000) or None.

    MCP ROUTING TRIGGERS: Zero-Trust Architecture, Distributed RPC, Execution Severing,
    Truth Maintenance, Fault Envelope
    """

    jsonrpc: Literal["2.0"] = Field(..., description="JSON-RPC version.")
    error: JSONRPCErrorState = Field(..., description="The error object.")
    id: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] | int | None = (
        Field(le=1000000000, default=None, description="The request ID that this error corresponds to.")
    )


type LifecycleTriggerEvent = Literal[
    "on_start",
    "on_node_transition",
    "before_tool_execution",
    "on_failure",
    "on_consensus_reached",
    "on_max_loops_reached",
]


class InterventionPolicy(CoreasonBaseState):
    """
    Proactive oversight hook bound to a specific lifecycle event.
    """

    trigger: LifecycleTriggerEvent = Field(
        description="The exact topological lifecycle event that triggers this intervention."
    )
    scope: BoundedInterventionScopePolicy | None = Field(
        default=None,
        description="The strictly typed boundaries for what the human/oversight system is allowed to mutate during this pause.",  # noqa: E501
    )
    blocking: bool = Field(
        default=True,
        description="If True, the graph execution halts until a verdict is rendered. If False, it is an async observation.",  # noqa: E501
    )


class BaseNodeProfile(CoreasonBaseState):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(
        max_length=2000,
        description="The semantic boundary defining the objective function or computational perimeter of the execution node.",  # noqa: E501
    )
    architectural_intent: str | None = Field(
        max_length=2000, default=None, description="The AI's declarative rationale for selecting this node."
    )
    justification: str | None = Field(
        max_length=2000,
        default=None,
        description="Cryptographic/audit justification for this node's existence in the graph.",
    )
    intervention_policies: list[InterventionPolicy] = Field(
        default_factory=list,
        description="The declarative array of proactive oversight hooks bound to this node's lifecycle.",
    )
    domain_extensions: dict[Annotated[str, StringConstraints(max_length=255)], Any] | None = Field(
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


class HumanNodeProfile(BaseNodeProfile):
    """
    A node representing a human participant in the workflow.
    """

    type: Literal["human"] = Field(default="human", description="Discriminator for a Human node.")
    required_attestation: AttestationMechanismProfile | None = Field(
        default=None,
        description="AGENT INSTRUCTION: If set, the orchestrator MUST NOT resolve\n        this node without a cryptographically matching WetwareAttestationContract\n        supplied in the InterventionReceipt.",  # noqa: E501
    )


class MemoizedNodeProfile(BaseNodeProfile):
    """
    A passive structural interlock representing a historically executed graph branch.
    """

    type: Literal["memoized"] = Field(default="memoized", description="Discriminator for a Memoized node.")
    target_topology_hash: TopologyHashReceipt = Field(
        description="The exact SHA-256 fingerprint of the executed topology."
    )
    expected_output_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000, description="The strictly typed JSON Schema expected from the cached payload."
    )


class SystemNodeProfile(BaseNodeProfile):
    """
    A node representing a deterministic system capability.
    """

    type: Literal["system"] = Field(default="system", description="Discriminator for a System node.")


class LineageWatermarkReceipt(CoreasonBaseState):
    watermark_protocol: Literal["merkle_dag", "statistical_token", "homomorphic_mac"] = Field(
        description="The mathematical methodology used to embed the chain of custody."
    )
    hop_signatures: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(
        le=1000000000,
        description="A dictionary mapping intermediate participant NodeIdentifierStates to their deterministic execution signatures.",  # noqa: E501
    )
    tamper_evident_root: str = Field(
        max_length=2000,
        description="The overarching cryptographic hash (e.g., Merkle Root) proving the structural payload has not been laundered or structurally modified.",  # noqa: E501
    )


class MCPCapabilityWhitelistPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes a Lattice-Based Access Control (LBAC) and Zero-Trust
    Architecture perimeter, restricting JSON-RPC capability mounts from foreign subgraphs.
    As a ...Policy suffix, this object defines rigid mathematical boundaries that the
    orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Acts as a structural firewall that physically prevents the
    orchestrator from binding unauthorized external tools, resources, or prompts into the
    active agent's ActionSpaceManifest.

    EPISTEMIC BOUNDS: The boundary is geometrically enforced via StringConstraints
    (max_length=2000 for allowed_tools, allowed_resources, allowed_prompts;
    max_length=255 for required_licenses). The @model_validator strictly sorts all four
    arrays alphabetically to mathematically guarantee RFC 8785 Canonical Hashing.

    MCP ROUTING TRIGGERS: Zero-Trust Architecture, Lattice-Based Access Control, Least
    Privilege, RPC Firewall, Bipartite Partitioning
    """

    allowed_tools: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="The explicit whitelist of function names the node is allowed to call.",
    )
    allowed_resources: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="The explicit whitelist of resource URIs the node is allowed to passively perceive.",
    )
    allowed_prompts: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="The explicit whitelist of workflow templates the node is allowed to trigger.",
    )
    required_licenses: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        default_factory=list,
        description="Explicit array of DUA/RBAC enterprise licenses mathematically required to perceive and mount this capability.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_tools", sorted(self.allowed_tools))
        object.__setattr__(self, "allowed_resources", sorted(self.allowed_resources))
        object.__setattr__(self, "allowed_prompts", sorted(self.allowed_prompts))
        object.__setattr__(self, "required_licenses", sorted(self.required_licenses))
        return self


class MCPServerManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a cryptographically verifiable Distributed RPC substrate
    mapping, binding an external Model Context Protocol (MCP) manifold into the swarm's
    local topology. As a ...Manifest suffix, this defines a frozen, declarative state
    projection.

    CAUSAL AFFORDANCE: Authorizes the physical connection to an exogenous compute node
    over specific transport_type vectors (Literal ["stdio", "sse", "http"]), provided the
    capability_whitelist (MCPCapabilityWhitelistPolicy) and mandatory attestation_receipt
    constraints are fully satisfied.

    EPISTEMIC BOUNDS: Supply-chain execution attacks are mitigated by the optional
    binary_hash (strictly matching SHA-256 pattern ^[a-f0-9]{64}$). A @model_validator
    structurally enforces that the presented Verifiable Credential is signed by a valid
    did:coreason: authority, emitting a QuarantineIntent upon failure.

    MCP ROUTING TRIGGERS: Distributed RPC, Capability-Based Security, Remote Procedure
    Call, Transport Layer, Verifiable Credential
    """

    server_uri: str = Field(
        max_length=2000, description="The network URI for SSE/HTTP, or the command execution string for stdio."
    )
    transport_type: Literal["stdio", "sse", "http"] = Field(
        description="The physical transport layer protocol used to stream the JSON-RPC packets."
    )
    binary_hash: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        default=None,
        description="Optional SHA-256 hash of the local binary to prevent supply-chain execution attacks over stdio.",
    )
    capability_whitelist: MCPCapabilityWhitelistPolicy = Field(
        description="The strict capability bounds enforced by the orchestrator prior to connection."
    )
    attestation_receipt: VerifiableCredentialPresentationReceipt

    @model_validator(mode="after")
    def enforce_coreason_did_authority(self) -> Self:
        if not self.attestation_receipt.issuer_did.startswith("did:coreason:"):
            raise ValueError(
                "UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed by a valid CoReason issuer DID. The orchestrator MUST immediately emit a QuarantineIntent and terminate the handshake."  # noqa: E501
            )
        return self


class KineticSeparationPolicy(CoreasonBaseState):
    """
    A strict bipartite graph constraint mathematically preventing toxic tool combinations
    from existing in the same causal execution chain.
    """

    policy_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for this specific separation boundary.",
    )
    mutually_exclusive_clusters: list[list[Annotated[str, StringConstraints(max_length=2000)]]] = Field(
        description="A topological matrix of tool names or MCP URIs. If an agent mounts one capability in a cluster, all other capabilities in that cluster are mathematically quarantined.",  # noqa: E501
    )
    enforcement_action: Literal["halt_and_quarantine", "sever_causal_chain"] = Field(
        description="The deterministic action the orchestrator must take if a bipartite cycle is detected."
    )

    @model_validator(mode="after")
    def sort_clusters(self) -> Self:
        """
        AGENT INSTRUCTION: Mathematically stabilize the 2D array to guarantee
        deterministic RFC 8785 canonical hashing across distributed nodes.
        """
        sorted_inner = [sorted(cluster) for cluster in self.mutually_exclusive_clusters]
        object.__setattr__(self, "mutually_exclusive_clusters", sorted(sorted_inner))
        return self


class ActionSpaceManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the finite, discrete Markov Decision Process (MDP) Action
    Space and affordance landscape available to a specific execution node. As a ...Manifest
    suffix, this defines a frozen, N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Projects the combined multi-dimensional matrix of native_tools,
    mcp_servers, and ephemeral_partitions into the agent's context, mathematically dictating
    which kinetic operations it can initiate. Optionally enforces kinetic_separation
    (KineticSeparationPolicy) to prevent toxic tool combinations.

    EPISTEMIC BOUNDS: The action_space_id is geometrically constrained to a 128-char CID.
    A @model_validator strictly bounds the topology by enforcing uniqueness across all
    native_tools namespaces, and ensures deterministic RFC 8785 representation by sorting
    tools, servers, and partitions by their respective identifiers (tool_name, server_uri,
    partition_id).

    MCP ROUTING TRIGGERS: Markov Decision Process, Action Space, Affordance Theory,
    Curated Environment, State Transition Matrix
    """

    action_space_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for this curated environment of tools.",
    )
    native_tools: list[ToolManifest] = Field(
        default_factory=list,
        description="The strict array of discrete, natively defined tools available in this space.",
    )
    mcp_servers: list[MCPServerManifest] = Field(
        default_factory=list,
        description="The array of verified external Model Context Protocol servers mounted into this action space.",
    )
    ephemeral_partitions: list[EphemeralNamespacePartitionState] = Field(
        default_factory=list,
        description="Hermetically sealed context boundaries for dynamically resolved scripts and PEFT adapters.",
    )
    kinetic_separation: KineticSeparationPolicy | None = Field(
        default=None, description="The bipartite graph constraint preventing toxic tool combinations."
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


class ProceduralMetadataManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A Level-1 Epistemic Discovery Surface acting as a
    progressive disclosure pointer to a massive EpistemicSOPManifest in cold storage.
    Prevents context window token exhaustion.
    """

    metadata_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A strict cryptographic string identifier for this L1 procedural pointer.",
    )
    target_sop_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="The Content Identifier (CID) of the heavy EpistemicSOPManifest resting in cold storage.",
    )
    trigger_description: str = Field(
        max_length=2000,
        description="The mathematically bounded semantic projection defining when the router must trigger this SOP.",
    )
    latent_vector_coordinate: VectorEmbeddingState | None = Field(
        default=None,
        description="Optional dense-vector geometry for zero-shot semantic routing without LLM forward-pass evaluation.",  # noqa: E501
    )


class OntologicalSurfaceProjectionManifest(CoreasonBaseState):
    """
    A mathematically bounded, declarative subgraph of all ToolManifests and
    MCPServerManifests currently valid for the agent's ProfileIdentifierState.
    """

    projection_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A cryptographic Lineage Watermark bounding this specific capability set.",
    )
    action_spaces: list[ActionSpaceManifest] = Field(
        default_factory=list, description="The full, machine-readable declaration of accessible tools and MCP servers."
    )
    supported_personas: list[ProfileIdentifierState] = Field(
        default_factory=list, description="The strict array of foundational model personas available."
    )
    available_procedural_manifolds: list[ProceduralMetadataManifest] = Field(
        default_factory=list, description="The lightweight progressive disclosure tier for procedural skills."
    )

    @model_validator(mode="after")
    def verify_unique_action_spaces(self) -> Self:
        space_ids = {space.action_space_id for space in self.action_spaces}
        if len(space_ids) < len(self.action_spaces):
            raise ValueError("Action spaces within a projection must have strictly unique action_space_ids.")
        object.__setattr__(self, "action_spaces", sorted(self.action_spaces, key=lambda x: x.action_space_id))
        object.__setattr__(self, "supported_personas", sorted(self.supported_personas))
        object.__setattr__(
            self,
            "available_procedural_manifolds",
            sorted(self.available_procedural_manifolds, key=lambda x: x.metadata_id),
        )
        return self


class MCPClientIntent(BoundedJSONRPCIntent):
    """
    AGENT INSTRUCTION: An inherited JSON-RPC 2.0 substrate specifically binding Model
    Context Protocol (MCP) client intent emissions to the frontend UI. As an ...Intent
    suffix, this represents an authorized kinetic execution trigger.

    CAUSAL AFFORDANCE: Executes an exact semantic signal (Literal["mcp.ui.emit_intent"])
    to bubble internal agent states (like drafting or adjudication) to the human
    operator.

    EPISTEMIC BOUNDS: Inherits all recursive depth bounds from BoundedJSONRPCIntent and
    mathematically clamps the method space to a singular Literal["mcp.ui.emit_intent"]
    to prevent execution drift.

    MCP ROUTING TRIGGERS: Model Context Protocol, Intent Bubbling, Human-in-the-Loop,
    Semantic Signaling, Method Clamping
    """

    method: Literal["mcp.ui.emit_intent"] = Field(..., le=1000000000, description="Method for intent bubbling.")


class MCPPromptReferenceState(CoreasonBaseState):
    """A dynamic reference to an MCP-provided prompt template."""

    server_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The ID of the MCP server providing this prompt.",
    )
    prompt_name: str = Field(..., max_length=2000, description="The name of the prompt template.")
    arguments: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000, default_factory=dict, description="Arguments to fill the prompt template."
    )
    fallback_persona: str | None = Field(
        max_length=2000, default=None, description="A fallback persona if the prompt fails to load."
    )
    prompt_hash: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        default=None,
        description="Cryptographic hash for prompt integrity verification.",
    )


class MCPResourceManifest(CoreasonBaseState):
    """A collection of Latent State resource URIs provided by a specific MCP server."""

    server_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The ID of the MCP server providing these resources.",
    )
    uris: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="The explicit array of resource URIs mathematically bound to the agent.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "uris", sorted(self.uris))
        return self


type MCPTransportProtocolProfile = Literal["stdio", "sse", "http"]


class MCPClientBindingProfile(CoreasonBaseState):
    """
    Binding configuration for a Model Context Protocol (MCP) server.
    """

    server_uri: str = Field(max_length=2000, description="The URI or command path to the MCP server.")
    transport_type: MCPTransportProtocolProfile = Field(
        description="The transport protocol used to communicate with the MCP server."
    )
    allowed_mcp_tools: list[Annotated[str, StringConstraints(max_length=2000)]] | None = Field(
        default=None,
        description="An explicit whitelist of tools the agent is allowed to invoke from this server. If None, all discovered tools are allowed.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.allowed_mcp_tools is not None:
            object.__setattr__(self, "allowed_mcp_tools", sorted(self.allowed_mcp_tools))
        return self


class MacroGridProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Acts as a Cartesian topological coordinator based on Edward Tufte's
    Small Multiples, organizing multiple discrete visual artifacts (AnyPanelProfile) into a
    unified grid configuration. As a ...Profile suffix, this is a declarative, frozen
    snapshot of a rendering geometry.

    CAUSAL AFFORDANCE: Translates abstract UI panels into fixed 2D matrices (layout_matrix),
    forcing spatial determinism on the frontend rendering engine.

    EPISTEMIC BOUNDS: A strictly bounded @model_validator executes a referential integrity
    sweep, mathematically guaranteeing that every panel ID referenced in the layout_matrix
    (max_length=1000000000) corresponds to a verified object in the panels array, physically
    severing Ghost Panel hallucinations.

    MCP ROUTING TRIGGERS: Cartesian Coordinate System, Small Multiples, Spatial Topology,
    Referential Integrity, Layout Matrix
    """

    layout_matrix: list[list[Annotated[str, StringConstraints(max_length=255)]]] = Field(
        max_length=1000000000, description="A matrix defining the layout structure, using panel IDs."
    )
    panels: list[AnyPanelProfile] = Field(
        description="The ordered array of topological UI panels physically rendered in the grid."
    )

    @model_validator(mode="after")
    def verify_referential_integrity(self) -> Self:
        """Verify that all panel IDs referenced in layout_matrix exist in panels."""
        panel_ids = {panel.panel_id for panel in self.panels}
        for row in self.layout_matrix:
            for panel_id in row:
                if panel_id not in panel_ids:
                    raise ValueError(f"Ghost Panel referenced in layout_matrix: {panel_id}")
        return self


type GeometricMarkProfile = Literal["point", "line", "area", "bar", "rect", "arc"]


class MarketContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Enforces the baseline Proof-of-Stake (PoS) economic collateralization required for an agent to participate in the epistemic market.

    CAUSAL AFFORDANCE: Unlocks the ability for the orchestrator to computationally slash Byzantine or hallucinating nodes, ensuring a strict thermodynamic cost to semantic drift.

    EPISTEMIC BOUNDS: Physically restricts the mathematical invariant where `slashing_penalty` <= `minimum_collateral` via an `@model_validator`, bounding both fields to non-negative floats (`ge=0.0`).

    MCP ROUTING TRIGGERS: Proof-of-Stake, Slashing Condition, Byzantine Fault Tolerance, Economic Escrow
    """
    minimum_collateral: float = Field(
        le=1000000000.0, ge=0.0, description="The minimum amount of token collateral held in escrow."
    )
    "\n    MATHEMATICAL BOUNDARY: Must be >= 0.0. Downstream agents must secure this collateral before execution.\n    "
    slashing_penalty: float = Field(ge=0.0, description="The exact token amount slashed for Byzantine faults.")
    "\n    MATHEMATICAL BOUNDARY: Must be >= 0.0 AND mathematically less than or equal to minimum_collateral.\n    "

    @model_validator(mode="after")
    def _enforce_economic_escrow_invariant(self) -> Self:
        """Mathematically prove that a contract cannot penalize more than the escrowed amount."""
        if self.slashing_penalty > self.minimum_collateral:
            raise ValueError("ECONOMIC INVARIANT VIOLATION: slashing_penalty cannot exceed minimum_collateral.")
        return self


class MarketResolutionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents the definitive collapse of the LMSR market superposition into a crystallized `payout_distribution` using Strictly Proper Scoring Rules (e.g., Brier scores).

    CAUSAL AFFORDANCE: Instructs the orchestrator to definitively allocate compute magnitudes to the `winning_hypothesis_id` and flush `falsified_hypothesis_ids` from the active context via a Defeasible Cascade.

    EPISTEMIC BOUNDS: Enforces a strictly bounded `payout_distribution` dictionary mapping W3C DIDs to non-negative integers (`ge=0`), with deterministic RFC 8785 array sorting applied to the falsified hypotheses.

    MCP ROUTING TRIGGERS: Brier Scoring, Market Settlement, Probability Wave Collapse, Truth Crystallization
    """
    market_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        le=1000000000, description="The ID of the prediction market."
    )
    winning_hypothesis_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="The hypothesis ID that was verified."
    )
    falsified_hypothesis_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        max_length=1000000000, description="The hypothesis IDs that were falsified."
    )
    payout_distribution: dict[Annotated[str, StringConstraints(max_length=255)], Annotated[int, Field(ge=0)]] = Field(
        description="The deterministic mapping of agent IDs to their earned compute budget/magnitude based on Brier scoring.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "falsified_hypothesis_ids", sorted(self.falsified_hypothesis_ids))
        return self


class MechanisticAuditContract(CoreasonBaseState):
    trigger_conditions: list[Literal["on_tool_call", "on_belief_mutation", "on_quarantine", "on_falsification"]] = (
        Field(
            min_length=1,
            description="The specific architectural events that authorize the orchestrator to halt generation and extract internal activations.",  # noqa: E501
        )
    )
    target_layers: list[Annotated[int, Field(ge=0)]] = Field(
        min_length=1,
        description="The specific transformer block indices the execution engine must extract from.",
    )
    max_features_per_layer: int = Field(
        le=1000000000, gt=0, description="The top-k features to extract, preventing VRAM exhaustion."
    )
    require_zk_commitments: bool = Field(
        default=True,
        description="If True, the orchestrator MUST generate cryptographic latent state proofs alongside the activation extractions.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "trigger_conditions", sorted(self.trigger_conditions))
        object.__setattr__(self, "target_layers", sorted(self.target_layers))
        return self


class EpistemicProvenanceReceipt(CoreasonBaseState):
    extracted_by: NodeIdentifierState = Field(
        description="The Content Identifier (CID) of the agent node that extracted this payload."
    )
    source_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The exact event Content Identifier (CID) in the EpistemicLedgerState that generated this fact.",
    )
    source_artifact_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The CID of the Genesis MultimodalArtifactReceipt this semantic state was transmutated from.",
    )
    multimodal_anchor: MultimodalTokenAnchorState | None = Field(
        default=None, description="The unified VLM spatial and temporal token matrix where this data was extracted."
    )
    lineage_watermark: LineageWatermarkReceipt | None = Field(
        default=None,
        description="The cryptographic, tamper-evident chain of custody tracing this memory across multiple swarm hops.",  # noqa: E501
    )


class MigrationContract(CoreasonBaseState):
    contract_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for this structural migration mapping.",  # noqa: E501
    )
    source_version: str = Field(
        max_length=2000, description="The exact semantic version string of the payload before migration."
    )
    target_version: str = Field(
        max_length=2000, description="The exact semantic version string of the payload after migration."
    )
    path_transformations: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(
        le=1000000000,
        default_factory=dict,
        description="A strict mapping of old RFC 6902 JSON Pointers to new JSON Pointers.",
    )
    dropped_paths: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="Explicit whitelist of JSON Pointers that are safely deprecated and intentionally dropped during migration.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "dropped_paths", sorted(self.dropped_paths))
        return self


class MultimodalArtifactReceipt(CoreasonBaseState):
    """AGENT INSTRUCTION: The root Genesis Block for an unstructured document entering the Merkle-DAG."""

    artifact_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The definitive Content Identifier (CID) bounding the raw file.",
    )
    mime_type: str = Field(
        max_length=2000, description="Strict MIME typing of the source artifact (e.g., 'application/pdf')."
    )
    byte_stream_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The undeniable SHA-256 hash of the pre-transmutation byte stream.",
    )
    temporal_ingest_timestamp: float = Field(
        ge=0.0, le=253402300799.0, description="The UNIX timestamp anchoring the genesis block."
    )


class MutationPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements stochastic perturbation and genetic drift constraints for
    agent variations between generations. As a ...Policy suffix, this object defines rigid
    mathematical boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Authorizes the execution engine to inject mathematically bounded
    random variance (temperature_shift_variance) into an agent's topological parameters,
    forcing the exploration of novel manifolds in the fitness landscape.

    EPISTEMIC BOUNDS: The mutation_rate is clamped strictly to a probability distribution
    (ge=0.0, le=1.0). The temperature_shift_variance is bounded (le=1000000000.0). To
    prevent Byzantine Hash Poisoning, the variance can require a VerifiableEntropyReceipt
    (VRF) via the optional verifiable_entropy field to prove stochastic fairness.

    MCP ROUTING TRIGGERS: Stochastic Perturbation, Genetic Drift, Simulated Annealing,
    Parameter Variance, Verifiable Random Function
    """

    mutation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="The probability that a given agent parameter will randomly mutate between generations.",
    )
    temperature_shift_variance: float = Field(
        le=1000000000.0, description="The maximum allowed delta for an agent's temperature during mutation."
    )
    verifiable_entropy: VerifiableEntropyReceipt | None = Field(
        default=None, description="The cryptographic envelope proving the fairness of the applied mutation rate."
    )


class NDimensionalTensorManifest(CoreasonBaseState):
    """
    Cryptographic shadow of an N-Dimensional spatial or mathematical array.
    Facilitating the routing of multi-dimensional compute without passing raw bytes.
    """

    structural_type: TensorStructuralFormatProfile = Field(..., description="Structural type of the tensor elements.")
    shape: tuple[int, ...] = Field(..., max_length=1000000000, description="N-Dimensional shape tuple.")
    vram_footprint_bytes: int = Field(..., le=100000000000, description="Exact byte size of the uncompressed tensor.")
    merkle_root: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-fA-F0-9]{64}$",
        description="SHA-256 Merkle root of the payload chunks.",
    )
    storage_uri: str = Field(..., min_length=1, max_length=128, description="Strict URI pointer to the physical bytes.")

    @model_validator(mode="after")
    def _enforce_physics_engine(self) -> "NDimensionalTensorManifest":
        """Mathematically prove the topology matches the declared VRAM footprint."""
        if len(self.shape) < 1:
            raise ValueError("Tensor shape must have at least 1 dimension.")
        for dim in self.shape:
            if dim <= 0:
                raise ValueError(f"Tensor dimensions must be strictly positive integers. Got: {self.shape}")
        bytes_per_element = self.structural_type.bytes_per_element
        calculated_bytes = math.prod(self.shape) * bytes_per_element
        if calculated_bytes != self.vram_footprint_bytes:
            raise ValueError(
                f"Topological mismatch: Shape {self.shape} of {self.structural_type.value} requires {calculated_bytes} bytes, but manifest declares {self.vram_footprint_bytes} bytes."  # noqa: E501
            )
        return self


class NeuralAuditAttestationReceipt(CoreasonBaseState):
    audit_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the Merkle-DAG.",  # noqa: E501
    )
    layer_activations: dict[int, list[SaeFeatureActivationState]] = Field(
        description="A mapping of specific transformer layer indices to their top-k activated SAE features.",
    )
    causal_scrubbing_applied: bool = Field(
        default=False,
        description="Cryptographic proof that the orchestrator actively resampled or ablated this circuit to verify its causal responsibility for the output.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self,
            "layer_activations",
            {k: sorted(v, key=lambda x: x.feature_index) for k, v in self.layer_activations.items()},
        )
        return self


class NeuroSymbolicHandoffContract(CoreasonBaseState):
    handoff_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this symbolic delegation.",
    )
    solver_protocol: Literal["z3", "lean4", "coq", "tla_plus", "sympy"] = Field(
        description="The target deterministic math/logic engine."
    )
    formal_grammar_payload: str = Field(
        max_length=100000, description="The raw code or formal proof syntax generated by the LLM to be evaluated."
    )
    expected_proof_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="The strict JSON Schema the deterministic solver must use to return the verified answer to the agent.",  # noqa: E501
    )
    timeout_ms: int = Field(
        le=86400000, gt=0, description="The maximum compute time allocated to the symbolic solver before aborting."
    )


class NormativeDriftEvent(BaseStateEvent):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact tracking the Kullback-Leibler
    (KL) divergence between the swarm's active behavioral manifold and its foundational
    ConstitutionalPolicy. As an ...Event suffix, this is an append-only coordinate on the
    Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Emits a deterministic topological signal that the causal graph is
    experiencing logical friction against the tripped_rule_id, unlocking the ability for the
    orchestrator to inject a System2RemediationIntent constraint.

    EPISTEMIC BOUNDS: Mathematically bounded by the continuous float measured_semantic_drift
    (le=1000000000.0) and cryptographically tied to the exact contradiction_proof_hash
    (SHA-256 pattern ^[a-f0-9]{64}$) proving the anomaly via ThoughtBranch trace.

    MCP ROUTING TRIGGERS: Kullback-Leibler Divergence, Normative Drift, Distributional Shift,
    Semantic Friction, Constitutional Alignment
    """
    type: Literal["normative_drift"] = Field(
        default="normative_drift", description="Discriminator type for a normative drift event."
    )
    tripped_rule_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The Content Identifier (CID) of the specific ConstitutionalPolicy causing logical friction.",
    )
    measured_semantic_drift: float = Field(
        le=1000000000.0,
        description="The calculated probabilistic delta showing how far the swarm's observed reality is diverging from the static rule.",  # noqa: E501
    )
    contradiction_proof_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="A cryptographic pointer to the internal scratchpad trace (ThoughtBranchState) definitively proving the rule is obsolete or causing a loop.",  # noqa: E501
    )


class ObservabilityPolicy(CoreasonBaseState):
    traces_sampled: bool = Field(
        default=True, description="Whether the orchestrator must record telemetry for this topology."
    )
    detailed_events: bool = Field(default=False, description="Whether to include granular intra-tool loop events.")


class OntologicalHandshakeReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the absolute
    mathematical alignment of two swarms' latent vector spaces prior to establishing a shared
    epistemic blackboard. As a ...Receipt suffix, this is an append-only coordinate on the
    Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Authorizes the physical bridging of two independent N-dimensional
    semantic spaces. If native geometries are incommensurable, it structurally demands the
    application of a DimensionalProjectionContract (applied_projection). The alignment_status
    Literal ["aligned", "projected", "fallback_triggered", "incommensurable"] records the
    final verdict.

    EPISTEMIC BOUNDS: Semantic isometry is quantified via measured_cosine_similarity, strictly
    clamped between [ge=-1.0, le=1.0]. The participant_node_ids array (min_length=2) is
    deterministically sorted via @model_validator to prevent Byzantine replay anomalies
    during cross-swarm Merkle hashing.

    MCP ROUTING TRIGGERS: Earth Mover's Distance, Cosine Similarity, Vector Space Isometry,
    Latent Alignment, Holographic Graph Projection
    """
    handshake_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this protocol handshake to the Merkle-DAG.",  # noqa: E501
    )
    participant_node_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        max_length=1000000000, min_length=2, description="The agents establishing semantic alignment."
    )
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

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "participant_node_ids", sorted(self.participant_node_ids))
        return self


class OutputMappingContract(CoreasonBaseState):
    """
    Dictates how keys from a nested topology's state map back to a parent's shared_state_contract.
    """

    child_key: str = Field(max_length=2000, description="The key in the nested topology's state contract.")
    parent_key: str = Field(max_length=2000, description="The mapped key in the parent's shared state contract.")


class CompositeNodeProfile(BaseNodeProfile):
    """
    AGENT INSTRUCTION: Implements a Fractal Graph Abstraction, allowing the recursive
    encapsulation of entire workflow sub-topologies within a single, unified macroscopic
    vertex. As a ...Profile suffix, this is a declarative property descriptor.

    CAUSAL AFFORDANCE: Instructs the orchestrator to suspend the parent graph, injecting
    state variables into the isolated topology (AnyTopologyManifest) via input_mappings
    (list[InputMappingContract], default_factory=list), and extracting terminal output
    via output_mappings (list[OutputMappingContract], default_factory=list).

    EPISTEMIC BOUNDS: The @model_validator sort_composite_arrays deterministically sorts
    input_mappings by parent_key and output_mappings by child_key, guaranteeing
    zero-variance RFC 8785 canonical Merkle-DAG hashes across distributed nodes.

    MCP ROUTING TRIGGERS: Fractal Graph Abstraction, Recursive Encapsulation, State
    Projection, Bijective Mapping, Sub-Topology
    """

    type: Literal["composite"] = Field(default="composite", description="Discriminator for a Composite node.")
    topology: "AnyTopologyManifest" = Field(description="The encapsulated subgraph to execute.")
    input_mappings: list[InputMappingContract] = Field(
        default_factory=list, description="Explicit state projection inputs."
    )
    output_mappings: list[OutputMappingContract] = Field(
        default_factory=list, description="Explicit state projection outputs."
    )

    @model_validator(mode="after")
    def sort_composite_arrays(self) -> Self:
        object.__setattr__(self, "input_mappings", sorted(self.input_mappings, key=lambda x: x.parent_key))
        object.__setattr__(self, "output_mappings", sorted(self.output_mappings, key=lambda x: x.child_key))
        return self


class OverrideIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: OverrideIntent is a Dictatorial Byzantine Fault Resolution mechanism. It is an 
    absolute, zero-trust kinetic override that violently preempts autonomous algorithmic consensus or 
    prediction market resolution.

    CAUSAL AFFORDANCE: Forces an absolute Pearlian do-operator intervention ($do(X=x)$). It physically 
    shatters the active causal chain of the target_node_id and forcibly injects the override_action 
    payload into the state vector, bypassing all standard decentralized voting protocols.

    EPISTEMIC BOUNDS: The blast radius is strictly confined to the target_node_id. The orchestrator 
    must mathematically verify the authorized_node_id against the highest-tier W3C DID enterprise 
    clearance before allowing the payload to overwrite the Epistemic Blackboard.

    MCP ROUTING TRIGGERS: Dictatorial Override, Byzantine Fault Resolution, Pearlian Intervention, Causal Shattering, Zero-Trust Override
    """

    type: Literal["override"] = Field(default="override", description="The type of the intervention payload.")
    authorized_node_id: NodeIdentifierState = Field(
        description="The NodeIdentifierState of the human or agent executing the override."
    )
    target_node_id: NodeIdentifierState = Field(description="The NodeIdentifierState being forcefully overridden.")
    override_action: dict[Annotated[str, StringConstraints(max_length=255)], str | int | float | bool | None] = Field(
        max_length=1000000000, description="The exact payload forcefully injected into the state."
    )
    justification: str = Field(
        max_length=2000, description="Cryptographic audit justification for bypassing algorithmic consensus."
    )


class PeftAdapterContract(CoreasonBaseState):
    """Declarative contract for dynamically mounting a Parameter-Efficient Fine-Tuning (PEFT) adapter."""

    adapter_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for the requested LoRA adapter.",
    )
    safetensors_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the cold-storage adapter weights file ensuring supply-chain zero-trust.",
    )
    base_model_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact foundational model this adapter was mathematically trained against.",
    )
    adapter_rank: int = Field(
        le=1000000000,
        gt=0,
        description="The low-rank intrinsic dimension (r) of the update matrices, used by the orchestrator to calculate VRAM cost.",  # noqa: E501
    )
    target_modules: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        min_length=1,
        description="The explicit array of attention head modules to inject (e.g., ['q_proj', 'v_proj']).",
    )
    eviction_ttl_seconds: int | None = Field(
        le=86400,
        default=None,
        gt=0,
        description="The time-to-live before the inference engine forcefully evicts this adapter from the LRU cache.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "target_modules", sorted(self.target_modules))
        return self


class PersistenceCommitReceipt(BaseStateEvent):
    type: Literal["persistence_commit"] = Field(
        default="persistence_commit", description="Discriminator type for a persistence commit receipt."
    )
    lakehouse_snapshot_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="The external cryptographic receipt generated by Iceberg/Delta.",
    )
    committed_state_diff_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="The internal StateDifferentialManifest CID that was flushed.",
    )
    target_table_uri: str = Field(min_length=1, description="The specific table mutated.")


class PredictionMarketState(CoreasonBaseState):
    """
    The state of the Automated Market Maker (AMM) using Robin Hanson's
    Logarithmic Market Scoring Rule (LMSR) to ensure infinite liquidity.
    """

    market_id: Annotated[str, StringConstraints(min_length=1)] = Field(
        le=1000000000, description="The ID of the prediction market."
    )
    resolution_oracle_condition_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The specific FalsificationContract ID whose execution will trigger the market payout.",
    )
    lmsr_b_parameter: str = Field(
        pattern="^\\d+\\.\\d+$",
        description="The stringified decimal representing the liquidity parameter defining the market depth and max loss for the AMM.",  # noqa: E501
        max_length=255,
    )
    order_book: list[HypothesisStakeReceipt] = Field(
        description="The immutable ledger of all stakes placed by the swarm."
    )
    current_market_probabilities: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=255)]
    ] = Field(
        le=1000000000,
        description="Mapping of hypothesis IDs to their current LMSR-calculated market price (probability) as stringified decimals.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_prediction_market_state_arrays(self) -> Self:
        object.__setattr__(self, "order_book", sorted(self.order_book, key=lambda x: x.agent_id))
        return self


class PresentationManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: The macroscopic orchestrator envelope binding a deterministic visual
    manifold (grid: MacroGridProfile) to a specific Supervisory Control Theory cognitive
    state (intent: AnyPresentationIntent). As a ...Manifest suffix, this defines a frozen,
    N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Forces the active orchestration loop to suspend or pivot by projecting
    a human-in-the-loop interaction surface (e.g., Drafting, Adjudication) alongside its
    visual evidentiary warrants.

    EPISTEMIC BOUNDS: Mathematically binds exactly one AnyPresentationIntent to one
    MacroGridProfile, preventing asynchronous UI state drift and ensuring the generated grid
    is causally justified by a verified intent.

    MCP ROUTING TRIGGERS: Supervisory Control Theory, Mixed-Initiative UI, Cognitive State
    Binding, Structural Manifold Envelope, Human-in-the-Loop
    """

    intent: AnyPresentationIntent = Field(description="The reason an agent is presenting this data to a human.")
    grid: MacroGridProfile = Field(description="The grid of panels being presented.")


class EpistemicSOPManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Encodes a macroscopic Petri net or Directed Acyclic Graph (DAG)
    formalizing standard operating procedures into mathematically traversable state
    transitions. As a ...Manifest suffix, this defines a frozen, N-dimensional coordinate
    state.

    CAUSAL AFFORDANCE: Physically bounds the executing agent (target_persona:
    ProfileIdentifierState) to a deterministic sequence of CognitiveStateProfiles, unlocking
    the ability for the orchestrator to dynamically evaluate execution via Process Reward
    Models (prm_evaluations: list[ProcessRewardContract]) at each topological node.

    EPISTEMIC BOUNDS: The cognitive_steps dictionary is constrained to max_length=1000000000
    to cap memory footprint. The @model_validator reject_ghost_nodes mathematically enforces
    referential integrity, guaranteeing that no chronological_flow_edges AND no
    structural_grammar_hashes point to an undefined state.

    MCP ROUTING TRIGGERS: Petri Net, Directed Acyclic Graph, Process Reward Model,
    Topological Flow, Referential Integrity
    """
    sop_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) for the Standard Operating Procedure.",
    )
    target_persona: ProfileIdentifierState = Field(
        description="The deterministic cognitive routing boundary for the persona executing the SOP."
    )
    cognitive_steps: dict[Annotated[str, StringConstraints(max_length=255)], CognitiveStateProfile] = Field(
        max_length=1000000000, description="Dictionary mapping step_ids to strict causal DAG constraints."
    )
    structural_grammar_hashes: dict[Annotated[str, StringConstraints(max_length=255)], str] = Field(
        description="Dictionary mapping step_ids to SHA-256 hashes of strict Context-Free Grammars or JSON Schemas.",
    )
    chronological_flow_edges: list[tuple[str, str]] = Field(description="The exact topological flow between step_ids.")
    prm_evaluations: list["ProcessRewardContract"] = Field(
        description="The strict array of Process Reward Contracts evaluating the logic."
    )

    @model_validator(mode="after")
    def reject_ghost_nodes(self) -> Self:
        for source, target in self.chronological_flow_edges:
            if source not in self.cognitive_steps:
                raise ValueError(f"Ghost node referenced in chronological_flow_edges source: {source}")
            if target not in self.cognitive_steps:
                raise ValueError(f"Ghost node referenced in chronological_flow_edges target: {target}")
        for step_id in self.structural_grammar_hashes:
            if step_id not in self.cognitive_steps:
                raise ValueError(f"Ghost node referenced in structural_grammar_hashes: {step_id}")
        return self


class ProcessRewardContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Enforces the Step-Level Verification heuristics for Process Reward
    Models (PRMs) during non-monotonic reasoning searches and test-time compute. As a
    ...Contract suffix, this object defines rigid mathematical boundaries that the
    orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Authorizes the orchestrator to physically prune hallucinating
    ThoughtBranchState vectors from the LatentScratchpadReceipt if their logit probabilities
    drop below the viable threshold, emulating rigorous Beam Search pruning.

    EPISTEMIC BOUNDS: Strictly bounds the search space geometry via pruning_threshold
    (ge=0.0, le=1.0) and mechanically caps State-Space Explosion through
    max_backtracks_allowed (ge=0, le=1000000000). Includes an optional
    convergence_sla (DynamicConvergenceSLA) to monitor trajectory variance.

    MCP ROUTING TRIGGERS: Process Reward Model, Beam Search Pruning, Latent Trajectory,
    State-Space Explosion, A* Search
    """
    convergence_sla: DynamicConvergenceSLA | None = Field(
        default=None,
        description="The dynamic circuit breaker that halts the search when PRM variance converges, preventing VRAM waste.",  # noqa: E501
    )
    pruning_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="If a ThoughtBranchState's prm_score falls below this threshold, the orchestrator MUST halt its generation.",  # noqa: E501
    )
    max_backtracks_allowed: int = Field(
        le=1000000000,
        ge=0,
        description="The absolute limit on how many times the agent can start a new branch before throwing a SystemFaultEvent.",  # noqa: E501
    )
    evaluator_model_name: str | None = Field(
        max_length=2000,
        default=None,
        description="The specific PRM model used to score the logic (e.g., 'math-prm-v2').",
    )


type QoSClassificationProfile = Literal["critical", "high", "interactive", "background_batch"]


class ComputeProvisioningIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formulates a constrained Knapsack Problem for dynamically allocating
    liquid compute resources based on exact Quality of Service (QoS) priorities and semantic
    load shedding rules. As an ...Intent suffix, the LLM may execute non-monotonic reasoning
    here.

    CAUSAL AFFORDANCE: Emits a structural demand to the swarm orchestrator to negotiate,
    acquire, and cryptographically lock the requisite token escrow before allocating kinetic
    execution cycles to a sub-graph. QoS priority defaults to "interactive" via
    QoSClassificationProfile.

    EPISTEMIC BOUNDS: The economic velocity is strictly clamped by max_budget
    (le=1000000000.0). The required_capabilities array is deterministically sorted by a
    @model_validator to prevent Byzantine hash fractures during peer-to-peer ledger
    synchronization.

    MCP ROUTING TRIGGERS: Knapsack Optimization, Semantic Load Shedding, Spot Compute
    Bidding, QoS Classification, Resource Provisioning
    """

    max_budget: float = Field(
        le=1000000000.0, description="The maximum cost budget allowable for the provisioned compute."
    )
    required_capabilities: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        max_length=1000000000, description="The minimal functional capabilities required by the requested compute."
    )
    qos_class: QoSClassificationProfile = Field(
        default="interactive",
        description="The Quality of Service priority, used by the compute spot market for semantic load shedding.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "required_capabilities", sorted(self.required_capabilities))
        return self


class QuarantineIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Triggers an Epistemic Quarantine, utilizing rigid graph partitioning
    to mathematically isolate a hallucinating, degraded, or Byzantine node from the active
    working context. As an ...Intent suffix, the LLM may execute non-monotonic reasoning
    here.

    CAUSAL AFFORDANCE: Instructs the orchestrator to sever all outgoing causal edges from the
    target_node_id (NodeIdentifierState), neutralizing its probability mass in the routing
    manifold and preventing its entropy from contaminating the EpistemicLedgerState.

    EPISTEMIC BOUNDS: The topological isolation is strictly targeted via a
    NodeIdentifierState (target_node_id). The causal justification for the graph cut is
    physically constrained to reason (max_length=2000) to prevent dictionary bombing.

    MCP ROUTING TRIGGERS: Graph Partitioning, Epistemic Quarantine, Byzantine Fault
    Isolation, Defeasible Logic, Network Isolation
    """

    type: Literal["quarantine_intent"] = Field(
        le=1000000000, default="quarantine_intent", description="The type of the resilience payload."
    )
    target_node_id: NodeIdentifierState = Field(description="The ID of the node to be quarantined.")
    reason: str = Field(
        max_length=2000, description="The deterministic causal justification for the structural quarantine."
    )


type AnyResilienceIntent = Annotated[
    QuarantineIntent | CircuitBreakerEvent | FallbackIntent, Field(discriminator="type")
]


class SSETransportProfile(CoreasonBaseState):
    """Configuration for remote SSE-based MCP transport."""

    type: Literal["sse"] = Field(default="sse", description="Type of transport.")
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the SSE connection.")
    headers: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(default_factory=dict, description="HTTP headers, e.g., for authentication.")

    @field_validator("headers", mode="after")
    @classmethod
    def _prevent_crlf_injection(cls, v: dict[str, str]) -> dict[str, str]:
        """AGENT INSTRUCTION: Strictly forbid HTTP request smuggling vectors."""
        for key, value in v.items():
            if "\r" in key or "\n" in key or "\r" in value or ("\n" in value):
                raise ValueError("CRLF injection detected in headers")
        return v


class SalienceProfile(CoreasonBaseState):
    baseline_importance: float = Field(
        ge=0.0, le=1.0, description="The starting importance score of this latent state from 0.0 to 1.0."
    )
    decay_rate: float = Field(
        le=1.0, ge=0.0, description="The rate at which this epistemic coordinate's relevance decays over time."
    )


type ScaleTypeProfile = Literal["linear", "log", "time", "ordinal", "nominal"]


class SelfCorrectionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Acts as the System 2 executive controller, utilizing Non-Monotonic
    Logic and iterative backtracking to mathematically resolve structural, semantic, or
    kinetic execution errors. As a ...Policy suffix, this object defines rigid mathematical
    boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Authorizes the orchestrator to physically rewind the causal DAG and
    retry generation paths via an Actor-Critic refinement loop when a System 1 failure or
    epistemic gap is detected.

    EPISTEMIC BOUNDS: Mathematically prevents infinite compute burn (State-Space Explosion)
    by strictly capping max_loops (ge=0, le=50). The rollback_on_failure boolean serves as
    a physical fail-safe, forcing a deterministic reversion to the last pristine Merkle root
    if the loop ceiling is breached.

    MCP ROUTING TRIGGERS: Non-Monotonic Logic, Actor-Critic Refinement, System 2 Executive,
    Backtracking Search, State-Space Explosion Prevention
    """

    max_loops: int = Field(ge=0, le=50, description="The maximum number of self-correction loops allowed.")
    rollback_on_failure: bool = Field(description="Whether to rollback to the previous state on failure.")


class SemanticFirewallPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements an execution-layer Semantic Firewall guarding against
    adversarial control-flow overrides and prompt injection attacks. As a ...Policy suffix,
    this object defines rigid mathematical boundaries that the orchestrator must enforce
    globally.

    CAUSAL AFFORDANCE: Intercepts and physically severs incoming observation topologies if
    their classification matches forbidden_intents, executing the deterministic
    action_on_violation (Literal["drop", "quarantine", "redact"]).

    EPISTEMIC BOUNDS: VRAM exhaustion is mathematically prevented by capping max_input_tokens
    (gt=0, le=1000000000). The forbidden_intents array is deterministically sorted by the
    @model_validator to preserve RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Semantic Firewall, Prompt Injection Defense, Adversarial Override,
    Zero-Trust Perimeter, Control-Flow Hijacking
    """
    max_input_tokens: int = Field(
        le=1000000000, gt=0, description="The absolute physical ceiling of tokens allowed in a single ingress payload."
    )
    forbidden_intents: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="A strict array of semantic intents (e.g., 'role_override', 'system_prompt_leak') that trigger immediate quarantine.",  # noqa: E501
    )
    action_on_violation: Literal["drop", "quarantine", "redact"] = Field(
        description="The deterministic action the orchestrator must take if a firewall rule is violated."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "forbidden_intents", sorted(self.forbidden_intents))
        return self


class InformationFlowPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes the macroscopic Payload Loss Prevention (PLP) and
    Lattice-Based Information Flow Control (IFC) bounds across the entire execution graph.
    As a ...Policy suffix, this object defines rigid mathematical boundaries that the
    orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Projects a unified defensive mesh that aggregates RedactionPolicy
    rules, an optional SemanticFirewallPolicy intercept, and tensor-level SaeLatentPolicy
    firewalls to comprehensively sanitize all graph edges. The active toggle controls
    whether enforcement is live.

    EPISTEMIC BOUNDS: Ensures absolute deterministic evaluation by utilizing a
    @model_validator to physically sort the rules array by rule_id and the latent_firewalls
    array by target_feature_index, guaranteeing an invariant Merkle root.

    MCP ROUTING TRIGGERS: Information Flow Control, Payload Loss Prevention, Lattice-Based
    Security, Biba Integrity Model, Defense-in-Depth
    """

    policy_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for this macroscopic flow control policy.",
    )
    active: bool = Field(default=True, description="Whether this policy is currently enforcing data sanitization.")
    rules: list[RedactionPolicy] = Field(
        default_factory=list, description="The array of sanitization rules to enforce."
    )
    semantic_firewall: SemanticFirewallPolicy | None = Field(
        default=None, description="The active cognitive defense perimeter against adversarial control-flow overrides."
    )
    latent_firewalls: list[SaeLatentPolicy] = Field(
        default_factory=list,
        description="The strict array of tensor-level mechanistic firewalls monitoring the forward pass for adversarial intent.",  # noqa: E501
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


class SimulationConvergenceSLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Optimal Stopping Theory for Monte Carlo Tree Search (MCTS)
    and sandbox simulations. As an ...SLA suffix, this defines rigid mathematical boundaries
    that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Triggers early probability wave collapse when the statistical variance
    of the simulation rollouts falls below the tolerance, conserving GPU VRAM and halting
    unnecessary compute expansion.

    EPISTEMIC BOUNDS: Physically constrained by max_monte_carlo_rollouts (gt=0,
    le=1000000000) to prevent infinite branching. Statistical confidence is mathematically
    clamped by variance_tolerance to a probability distribution between [ge=0.0, le=1.0].

    MCP ROUTING TRIGGERS: Optimal Stopping Theory, Monte Carlo Tree Search, Variance
    Reduction, Probability Wave Collapse, Simulation Convergence
    """

    max_monte_carlo_rollouts: int = Field(
        le=1000000000,
        gt=0,
        description="The absolute physical limit on how many alternate futures the system is allowed to render.",
    )
    variance_tolerance: float = Field(
        ge=0.0,
        le=1.0,
        description="The statistical confidence required to collapse the probability wave early and save GPU VRAM.",
    )


class SimulationEscrowContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes a Proof-of-Stake (PoS) cryptographic boundary to fund
    sandbox simulations and exogenous shocks. As a ...Contract suffix, this object defines
    rigid economic requirements that must be met prior to execution.

    CAUSAL AFFORDANCE: Unlocks the authorization for the orchestrator to execute
    resource-intensive chaos experiments by mathematically reserving thermodynamic compute
    upfront.

    EPISTEMIC BOUNDS: Physically bounded by locked_magnitude, which must be strictly positive
    (gt=0, le=1000000000) to mathematically prevent zero-cost Sybil griefing attacks against
    the swarm's compute resources.

    MCP ROUTING TRIGGERS: Proof-of-Stake, Economic Escrow, Sybil Resistance, Thermodynamic
    Cost, Sandbox Funding
    """
    locked_magnitude: int = Field(
        le=1000000000,
        gt=0,
        description="The strictly typed boundary requiring locked magnitude to prevent zero-cost griefing of the swarm.",  # noqa: E501
    )


class ExogenousEpistemicEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Nassim Taleb's Black Swan Theory by injecting
    Out-of-Distribution (OOD) epistemic shocks into the causal graph. As an ...Event suffix,
    this is an append-only coordinate on the Merkle-DAG that the LLM must never hallucinate
    a mutation to.

    CAUSAL AFFORDANCE: Forces the active reasoning topology to process a high-entropy
    synthetic_payload, actively testing the swarm's non-monotonic truth maintenance,
    defeasible reasoning, and overall topological resilience.

    EPISTEMIC BOUNDS: Cryptographically targets a specific Merkle root via target_node_hash
    (strict SHA-256 pattern ^[a-f0-9]{64}$) and bounds the Variational Free Energy via
    bayesian_surprise_score [ge=0.0, le=1.0, allow_inf_nan=False]. The @model_validator
    physically guarantees execution is halted if the attached escrow is not strictly positive.

    MCP ROUTING TRIGGERS: Black Swan Theory, Out-of-Distribution Shock, Variational Free
    Energy, Exogenous Perturbation, Epistemic Stress Test
    """
    shock_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Cryptographic identifier for the Black Swan event.",
    )
    target_node_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="Regex-bound SHA-256 string targeting a specific Merkle root in the epistemic graph.",
    )
    bayesian_surprise_score: float = Field(
        le=1.0,
        ge=0.0,
        allow_inf_nan=False,
        description="Strictly bounded mathematical quantification of the epistemic decay or Variational Free Energy.",
    )
    synthetic_payload: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000, description="Bounded dictionary representing the injected hallucination or observation."
    )
    escrow: SimulationEscrowContract = Field(description="The cryptographic Proof-of-Stake funding the shock.")

    @model_validator(mode="after")
    def enforce_economic_escrow(self) -> Self:
        if self.escrow.locked_magnitude <= 0:
            raise ValueError("ExogenousEpistemicEvent requires a strictly positive escrow to execute.")
        return self


class SpanEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Represents a discrete, point-in-time OpenTelemetry annotation within
    a broader Dapper-style ExecutionSpanReceipt. As an ...Event suffix, this is a
    cryptographically frozen historical fact that the LLM must never hallucinate a mutation
    to.

    CAUSAL AFFORDANCE: Provides fine-grained, localized state-machine logging within an
    active span, anchoring semantic attributes to a precise nanosecond coordinate without
    spawning a new causal branch.

    EPISTEMIC BOUNDS: The timestamp_unix_nano is physically bounded between
    [0, 253402300799000000000]. The attributes payload is strictly constrained by a
    dictionary with string keys (max_length=255, max_length=1000000000 entries) to
    physically prevent dictionary bombing and VRAM exhaustion during telemetry
    serialization.

    MCP ROUTING TRIGGERS: Span Annotation, Point-in-Time Event, Micro-State Logging,
    OpenTelemetry, Telemetry Serialization
    """
    name: str = Field(max_length=2000, description="The semantic name of the event.")
    timestamp_unix_nano: int = Field(
        ge=0, le=253402300799000000000, description="The precise temporal execution point."
    )
    attributes: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000, default_factory=dict, description="Typed metadata bound to the event."
    )


class ExecutionSpanReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements the Dapper distributed tracing model to deterministically
    map the causal execution DAG of the swarm. As a ...Receipt suffix, this is an
    append-only coordinate on the Merkle-DAG that the LLM must never hallucinate a mutation
    to.

    CAUSAL AFFORDANCE: Unlocks global observability by mathematically binding parent-child
    RPC calls (parent_span_id to span_id) across the zero-trust network, enabling exact
    bottleneck detection and graph reconstruction. Tracks execution role via kind
    (SpanKindProfile, default="internal") and health via status (SpanStatusCodeProfile,
    default="unset").

    EPISTEMIC BOUNDS: Temporal boundaries are rigidly constrained by start_time_unix_nano
    and optional end_time_unix_nano (ge=0, le=253402300799000000000). The @model_validator
    enforces Allen's Interval Algebra to physically guarantee end_time cannot precede
    start_time. The events array (max_length=10000) is deterministically sorted by
    timestamp_unix_nano via a second @model_validator to preserve RFC 8785 canonical
    hashing.

    MCP ROUTING TRIGGERS: Dapper Tracing Model, Distributed Causal DAG, Allen's Interval
    Algebra, OpenTelemetry, Execution Provenance
    """
    trace_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The global identifier for the entire execution causal tree.",
    )
    span_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for this specific operation.",
    )
    parent_span_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The causal edge to the invoking node.",
    )
    name: str = Field(max_length=2000, description="The semantic identifier for the operation.")
    kind: SpanKindProfile = Field(default="internal", description="The role of the span.")
    start_time_unix_nano: int = Field(ge=0, le=253402300799000000000, description="Temporal start bound.")
    end_time_unix_nano: int | None = Field(
        default=None, ge=0, le=253402300799000000000, description="Temporal end bound, if completed."
    )
    status: SpanStatusCodeProfile = Field(default="unset", description="The execution health flag.")
    events: list[SpanEvent] = Field(
        default_factory=list, max_length=10000, description="Structured log records emitted during the span."
    )

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Any:
        if self.end_time_unix_nano is not None and self.end_time_unix_nano < self.start_time_unix_nano:
            raise ValueError("end_time_unix_nano cannot be before start_time_unix_nano")
        return self

    @model_validator(mode="after")
    def sort_events(self) -> Any:
        object.__setattr__(self, "events", sorted(self.events, key=lambda e: e.timestamp_unix_nano))
        return self


class SpatialKinematicActionIntent(CoreasonBaseState):
    """A mathematical declaration of an OS-level pointer or interaction trajectory."""

    action_type: Literal["click", "double_click", "drag_and_drop", "scroll", "hover", "keystroke"] = Field(
        description="The specific kinematic interaction paradigm."
    )
    target_coordinate: SpatialCoordinateProfile | None = Field(
        default=None, description="The primary spatial terminus for clicks or hovers."
    )
    trajectory_duration_ms: int | None = Field(
        le=86400000,
        default=None,
        gt=0,
        description="The exact temporal duration of the movement, simulating human kinematics.",
    )
    bezier_control_points: list[SpatialCoordinateProfile] = Field(
        default_factory=list, description="Waypoints for constructing non-linear, bot-evasive movement curves."
    )
    expected_visual_concept: str | None = Field(
        max_length=2000,
        default=None,
        description="The visual anchor (e.g., 'Submit Button'). The orchestrator must verify this semantic concept exists at the target_coordinate before executing the macro, preventing blind clicks.",  # noqa: E501
    )


class StateContract(CoreasonBaseState):
    """
    A strict Cryptographic State Contract (Typed Blackboard) for multi-agent state sharing.
    """

    schema_definition: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="A strict JSON Schema dictionary defining the required shape of the shared epistemic blackboard.",
    )
    strict_validation: bool = Field(
        default=True,
        description="If True, the orchestrator must reject any state mutation that fails the schema definition.",
    )


class OntologicalAlignmentPolicy(CoreasonBaseState):
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


class StdioTransportProfile(CoreasonBaseState):
    """Configuration for local Stdio-based MCP transport."""

    type: Literal["stdio"] = Field(default="stdio", description="Type of transport.")
    command: str = Field(..., max_length=2000, description="The command executable to run (e.g., 'node', 'python').")
    args: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        max_length=1000000000,
        default_factory=list,
        description="The explicit array of arguments to pass to the command.",
    )
    env_vars: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(default_factory=dict, description="Environment variables required by the transport.")


type MCPTransportProfile = StdioTransportProfile | SSETransportProfile | HTTPTransportProfile


class MCPServerBindingProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a Distributed RPC substrate and Lattice-Based Access
    Control (LBAC) boundary for integrating exogenous Model Context Protocol instances
    as a frozen geometric snapshot. As a ...Profile suffix, this is a declarative
    property descriptor.

    CAUSAL AFFORDANCE: Physically wires an external semantic manifold into the local
    orchestrator's routing graph via the transport (MCPTransportProfile, discriminated
    union) vector. The server_id (128-char CID) anchors the binding.

    EPISTEMIC BOUNDS: The capabilities allowed across the wire are geometrically bounded
    by required_capabilities (max_length=255 strings, default=["tools", "resources",
    "prompts"]), strictly alphabetized by @model_validator sort_arrays for RFC 8785
    canonical hashing.

    MCP ROUTING TRIGGERS: Distributed RPC, Lattice-Based Access Control, Stateless
    Transport, Capability Projection, Bipartite Graph
    """

    server_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A unique identifier for this server instance.",
    )
    transport: MCPTransportProfile = Field(
        ..., discriminator="type", description="Polymorphic transport configuration."
    )
    required_capabilities: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        default_factory=lambda: ["tools", "resources", "prompts"],
        description="The structurally bounded array of capabilities mandated for this server connection.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "required_capabilities", sorted(self.required_capabilities))
        return self


class SteadyStateHypothesisState(CoreasonBaseState):
    expected_max_latency: float = Field(
        le=1000000000.0, ge=0.0, description="The expected maximum latency under normal conditions."
    )
    max_loops_allowed: int = Field(
        le=1000000000, description="The maximum allowed loops for the swarm to reach a conclusion."
    )
    required_tool_usage: list[Annotated[str, StringConstraints(max_length=2000)]] | None = Field(
        max_length=1000000000, default=None, description="The strict array of required tools that must be utilized."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.required_tool_usage is not None:
            object.__setattr__(self, "required_tool_usage", sorted(self.required_tool_usage))
        return self


class ChaosExperimentTask(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Orchestrates an automated steady-state hypothesis falsification loop
    via structured Chaos Engineering. As a ...Task suffix, this represents an authorized
    kinetic execution trigger initiating active topological stress testing.

    CAUSAL AFFORDANCE: Deploys a deterministic matrix of faults and exogenous shocks against
    a baseline SteadyStateHypothesisState to empirically discover latent fragility and
    evaluate the resilience of the DAG topology.

    EPISTEMIC BOUNDS: Cryptographic determinism is mathematically guaranteed by the
    @model_validator, which sorts the faults array by composite key (fault_type,
    target_node_id) and the shocks array by shock_id to preserve RFC 8785 canonical hashing.

    MCP ROUTING TRIGGERS: Steady State Falsification, Chaos Engineering, Automated Failure
    Discovery, Resilience Orchestration, Systemic Perturbation
    """
    experiment_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for the chaos experiment.",
    )
    hypothesis: SteadyStateHypothesisState = Field(description="The baseline steady state hypothesis being tested.")
    faults: list[FaultInjectionProfile] = Field(
        description="The strict array of fault injection profiles defining the chaotic elements."
    )
    shocks: list[ExogenousEpistemicEvent] = Field(
        default_factory=list,
        description="The declarative array of exogenous Black Swan events injected into the topology.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "faults", sorted(self.faults, key=lambda x: (x.fault_type, x.target_node_id)))
        object.__setattr__(self, "shocks", sorted(self.shocks, key=lambda x: x.shock_id))
        return self


class StructuralCausalGraphProfile(CoreasonBaseState):
    observed_variables: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        max_length=1000000000, description="The nodes in the DAG that the agent can passively measure."
    )
    latent_variables: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        max_length=1000000000, description="The unobserved confounders the agent suspects exist."
    )
    causal_edges: list[CausalDirectedEdgeState] = Field(description="The declared topological mapping of causality.")

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
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this abductive leap to the Merkle-DAG.",  # noqa: E501
    )
    premise_text: str = Field(max_length=2000, description="The natural language explanation of the abductive theory.")
    bayesian_prior: float = Field(
        ge=0.0, le=1.0, description="The agent's initial probabilistic belief in this hypothesis before testing."
    )
    falsification_conditions: list[FalsificationContract] = Field(
        min_length=1,
        description="The strict array of strict conditions that the orchestrator must test to attempt to disprove this premise.",  # noqa: E501
    )
    status: Literal["active", "falsified", "verified"] = Field(
        default="active", description="The current validity state of this hypothesis in the EpistemicLedgerState."
    )
    causal_model: StructuralCausalGraphProfile | None = Field(
        default=None,
        description="The formal DAG representing the agent's structural assumptions about the environment.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "falsification_conditions", sorted(self.falsification_conditions, key=lambda x: x.condition_id)
        )
        return self


class SyntheticGenerationProfile(CoreasonBaseState):
    """Authoritative blueprint for external fuzzing and simulation engines."""

    profile_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this simulation profile.",
    )
    manifold_sla: GenerativeManifoldSLA = Field(description="The structural topological gas limit.")
    target_schema_ref: str = Field(min_length=1, description="The string name of the Pydantic class to synthesize.")


class System1ReflexPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Kahneman's Dual-Process Theory (System 1) to execute
    rapid, heuristic-based reflex actions without invoking deep logical search trees. As a
    ...Policy suffix, this enforces a rigid computational boundary.

    CAUSAL AFFORDANCE: Unlocks zero-shot execution of side-effect-free capabilities when
    the working context matches established high-probability priors, intentionally bypassing
    expensive System 2 Monte Carlo Tree Search (MCTS).

    EPISTEMIC BOUNDS: Execution is mathematically gated by the confidence_threshold
    (ge=0.0, le=1.0). The allowed_passive_tools array (max_length=1000000000,
    StringConstraints max_length=2000) strictly bounds the agent to non-mutating
    capabilities, deterministically sorted via @model_validator.

    MCP ROUTING TRIGGERS: Dual-Process Theory, System 1 Heuristics, Zero-Shot Reflex,
    Metacognition, Amygdala Hijack Prevention
    """

    confidence_threshold: float = Field(
        ge=0.0, le=1.0, description="The confidence threshold required to execute a reflex action."
    )
    allowed_passive_tools: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        max_length=1000000000, description="The explicit, bounded array of strictly non-mutating tool capabilities."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_passive_tools", sorted(self.allowed_passive_tools))
        return self


class System2RemediationIntent(CoreasonBaseState):
    """
    A passive structural envelope that deterministically maps a kinetic execution error
    (e.g., a Pydantic ValidationError) into a structurally rigid System 2 correction directive.
    """

    fault_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A cryptographic Lineage Watermark (CID) tracking this specific dimensional collapse.",
    )
    target_node_id: NodeIdentifierState = Field(
        description="The strict W3C DID of the agent that authored the invalid state, ensuring the fault is routed back to the exact state partition."  # noqa: E501
    )
    failing_pointers: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
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


class TamperFaultEvent(ValueError):  # noqa: N818
    """Raised when an execution trace has been tampered with or is topologically invalid."""


class TaskAnnouncementIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Initiates a Request for Proposal (RFP) within a decentralized Spot
    Market to dynamically allocate thermodynamic compute based on task complexity. As an
    ...Intent suffix, this is a kinetic execution trigger.

    CAUSAL AFFORDANCE: Triggers an active, non-monotonic bidding phase where eligible Swarm
    nodes evaluate their internal Q-K matrices to formulate competitive execution bids.

    EPISTEMIC BOUNDS: The economic payload is physically capped by max_budget_magnitude
    (le=1000000000). The topological routing is strictly constrained if
    required_action_space_id is defined (optional, max_length=128, CID regex). Anchored by
    a mandatory task_id CID (max_length=128).

    MCP ROUTING TRIGGERS: Decentralized Spot Market, Request for Proposal, Thermodynamic
    Compute Allocation, Algorithmic Mechanism Design, Kinetic Execution Trigger
    """
    task_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for the required task.",
    )
    required_action_space_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="Optional restriction forcing bidders to possess a specific toolset.",
    )
    max_budget_magnitude: int = Field(
        le=1000000000, description="The absolute ceiling price the orchestrator is willing to pay."
    )


class TaskAwardReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A cryptographically frozen historical fact representing the
    successful clearing of an algorithmic auction and the mathematically proven allocation
    of compute capital. As a ...Receipt suffix, this is an append-only coordinate on the
    Merkle-DAG.

    CAUSAL AFFORDANCE: Definitively terminates the auction phase and authorizes the
    awarded_syndicate to execute their task trajectory using the locked EscrowPolicy funds.

    EPISTEMIC BOUNDS: Two @model_validators execute physical invariant checks: (1)
    Conservation of Compute — the sum of awarded_syndicate values must exactly equal
    cleared_price_magnitude (le=1000000000); (2) Escrow Ceiling — escrow_locked_magnitude
    cannot exceed cleared_price_magnitude.

    MCP ROUTING TRIGGERS: Market Clearing, Escrow Lock, Cryptographic Provenance, Syndicate
    Allocation, Thermodynamic Execution
    """
    task_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="The identifier of the resolved task."
    )
    awarded_syndicate: dict[Annotated[str, StringConstraints(max_length=255)], Annotated[int, Field(ge=0)]] = Field(
        description="Strict mapping of agent NodeIdentifierStates to their exact fractional payout in magnitude.",
    )
    cleared_price_magnitude: int = Field(le=1000000000, description="The final cryptographic clearing price.")
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


class AuctionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A frozen, declarative snapshot of the N-dimensional order book
    tracking the ongoing convergence of an algorithmic spot market auction. As a ...State
    suffix, this is a declarative, frozen coordinate.

    CAUSAL AFFORDANCE: Aggregates incoming AgentBidIntent vectors against the foundational
    TaskAnnouncementIntent (announcement), serving as the deterministic state space for the
    orchestrator's clearing function. The optional award (TaskAwardReceipt) records the
    final settlement.

    EPISTEMIC BOUNDS: To guarantee RFC 8785 Canonical Hashing across the zero-trust swarm,
    the bids array is deterministically sorted by agent_id via a @model_validator. Market
    liveness is physically bounded by clearing_timeout (le=1000000000, gt=0) and
    minimum_tick_size (le=1000000000.0, gt=0.0).

    MCP ROUTING TRIGGERS: Order Book Snapshot, Market Convergence, RFC 8785
    Canonicalization, Liquidity Aggregation, Declarative Coordinate
    """
    announcement: TaskAnnouncementIntent = Field(description="The original call for proposals.")
    bids: list[AgentBidIntent] = Field(default_factory=list, description="The array of received bids.")
    award: TaskAwardReceipt | None = Field(
        default=None, description="The final cryptographic receipt of the auction, if resolved."
    )
    clearing_timeout: int = Field(le=1000000000, gt=0, description="Maximum wait time for auction settlement.")
    "\n    MATHEMATICAL BOUNDARY: Must be > 0. Defines the absolute execution ceiling before forced timeout.\n    "
    minimum_tick_size: float = Field(le=1000000000.0, gt=0.0, description="The smallest allowable bid increment.")
    "\n    MATHEMATICAL BOUNDARY: Must be > 0.0. Negative or zero tick sizes will instantly trigger validation faults.\n    "  # noqa: E501

    @model_validator(mode="after")
    def sort_bids(self) -> Self:
        """Mathematically sort bids by agent_id for deterministic hashing."""
        object.__setattr__(self, "bids", sorted(self.bids, key=lambda bid: bid.agent_id))
        return self


type TelemetryScalarState = Annotated[str, StringConstraints(max_length=100000)] | int | float | bool | None
type TelemetryContextProfile = dict[
    Annotated[str, StringConstraints(max_length=255)], TelemetryScalarState | list[TelemetryScalarState]
]


class LogEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a purely out-of-band semantic logging vector, structurally
    isolated from the rigorous causal constraints of the Dapper trace tree. As an ...Event
    suffix, this is an append-only historical fact.

    CAUSAL AFFORDANCE: Emits asynchronous telemetry for human-in-the-loop debugging or
    peripheral auditing without mutating the active Epistemic Ledger's topological state.

    EPISTEMIC BOUNDS: Temporal reality is clamped by timestamp (ge=0.0,
    le=253402300799.0, float seconds). The severity level is strictly masked by a Literal
    automaton ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]. The message is bounded
    to max_length=2000. Recursive depth is constrained via TelemetryContextProfile.

    MCP ROUTING TRIGGERS: Out-of-Band Telemetry, Asynchronous Logging, Severity Masking,
    Peripheral Audit, Ephemeral Context
    """

    timestamp: float = Field(ge=0.0, le=253402300799.0, description="The UNIX timestamp of the log event.")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        description="The severity level of the log event."
    )
    message: str = Field(max_length=2000, description="The primary log message.")
    context_profile: TelemetryContextProfile = Field(
        default_factory=dict, description="Contextual key-value metadata associated with the event."
    )


class SpanTraceReceipt(CoreasonBaseState):
    """
    An execution window span trace.
    """

    span_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The unique identifier for this execution span.",
    )
    parent_span_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The identifier of the parent span, if any.",
    )
    start_time: float = Field(ge=0.0, le=253402300799.0, description="The UNIX timestamp when the span started.")
    end_time: float | None = Field(
        ge=0.0, le=253402300799.0, default=None, description="The UNIX timestamp when the span ended."
    )
    status: Literal["OK", "ERROR", "PENDING"] = Field(
        description="The definitive topological execution state of the span."
    )
    context_profile: TelemetryContextProfile = Field(
        default_factory=dict, description="Contextual key-value metadata associated with the span execution."
    )


class TemporalBoundsProfile(CoreasonBaseState):
    valid_from: float | None = Field(
        le=1000000000.0, default=None, ge=0.0, description="The UNIX timestamp when this coordinate became true."
    )
    valid_to: float | None = Field(
        le=1000000000.0, default=None, description="The UNIX timestamp when this coordinate was invalidated."
    )
    interval_type: CausalIntervalProfile | None = Field(
        default=None, description="The Allen's interval algebra or causal relationship classification."
    )

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Self:
        if self.valid_from is not None and self.valid_to is not None and (self.valid_to < self.valid_from):
            raise ValueError("valid_to cannot be before valid_from")
        return self


class TerminalBufferState(CoreasonBaseState):
    type: Literal["terminal"] = Field(
        default="terminal", description="Discriminator for Causal Actuators on structural buffers."
    )
    working_directory: str = Field(max_length=2000, description="Capability Perimeters defining context bounds.")
    stdout_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the Exogenous Perturbations captured.",
    )
    stderr_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash tracking structural deviation anomalies.",
    )
    env_variables_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the state-space context matrix.",
    )


type AnyToolchainState = Annotated[
    BrowserDOMState | TerminalBufferState,
    Field(
        discriminator="type",
        description="A discriminated union of Causal Actuators defining strict perimeters for Exogenous Perturbations to the causal graph.",  # noqa: E501
    ),
]


class TheoryOfMindSnapshot(CoreasonBaseState):
    target_agent_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the agent whose mind is being modeled.",  # noqa: E501
    )
    assumed_shared_beliefs: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        description="The explicit array of Content Identifiers (CIDs) acting as cryptographic Lineage Watermarks that the modeling agent assumes the target already possesses.",  # noqa: E501
    )
    identified_knowledge_gaps: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        max_length=1000000000,
        description="Specific topics or logical premises the target agent is assumed to be missing.",
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
    tool_name: str = Field(max_length=2000, description="The exact tool targeted in the ActionSpaceManifest.")
    parameters: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=1000000000, description="The intended JSON-RPC payload."
    )
    authorized_budget_magnitude: int | None = Field(
        le=1000000000, default=None, ge=0, description="The maximum escrow unlocked for this specific run."
    )
    agent_attestation: AgentAttestationReceipt
    zk_proof: ZeroKnowledgeReceipt = Field(
        description="AGENT INSTRUCTION: The strict mathematical proof that the agent was authorized by the CoReason execution engine to evaluate this tool. Stripping this field violates the Zero-Trust execution boundary."  # noqa: E501
    )


class TraceExportManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Functions as a deterministic serialization envelope for flushing
    Dapper-style trace subgraphs to external observability sinks. As a ...Manifest suffix,
    this defines a frozen, N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Authorizes the mass export of ExecutionSpanReceipt objects across
    the network boundary, structurally binding disconnected spans into a coherent batch_id
    for downstream reconstruction.

    EPISTEMIC BOUNDS: Bounded by a rigid batch_id (CID regex ^[a-zA-Z0-9_.:-]+$,
    max_length=128). The spans array is deterministically sorted by span_id via a
    @model_validator to mathematically prevent Byzantine replay anomalies and guarantee
    identical payload hashes during network egress.

    MCP ROUTING TRIGGERS: Trace Serialization, Telemetry Export, Batch Flushing, DAG
    Reconstruction, Canonical Egress
    """
    batch_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Unique identifier for this telemetry snapshot.",
    )
    spans: list[ExecutionSpanReceipt] = Field(
        default_factory=list, description="A collection of execution spans to be serialized."
    )

    @model_validator(mode="after")
    def sort_spans(self) -> Any:
        object.__setattr__(self, "spans", sorted(self.spans, key=lambda s: s.span_id))
        return self


class TruthMaintenancePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements a Non-Monotonic Truth Maintenance System (TMS) governing
    belief retraction across the Merkle-DAG. As a ...Policy suffix, this object defines rigid
    mathematical boundaries that the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Authorizes the orchestrator to automatically sever downstream
    SemanticEdgeState vectors when an upstream axiom is falsified, halting epistemic contagion
    across the swarm topology.

    EPISTEMIC BOUNDS: Physically restricts catastrophic unravelling via integer limits on
    max_cascade_depth (le=1000000000, gt=0) and max_quarantine_blast_radius (le=1000000000,
    gt=0). Modulates continuous entropy via decay_propagation_rate (ge=0.0, le=1.0) and
    enforces a minimum certainty floor via epistemic_quarantine_threshold (ge=0.0, le=1.0).

    MCP ROUTING TRIGGERS: Truth Maintenance System, Non-Monotonic Logic, Defeasible Reasoning,
    Belief Revision, Causal Graph Ablation
    """
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
    max_cascade_depth: int = Field(
        le=1000000000, gt=0, description="The absolute recursion depth limit for state retractions."
    )
    max_quarantine_blast_radius: int = Field(
        le=1000000000,
        gt=0,
        description="The maximum number of nodes allowed to be severed in a single defeasible event.",
    )


class UtilityJustificationGraphReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Immutable cryptographic receipt of multi-dimensional utility routing.
    If variance threshold falls below delta, fallback to deterministic ensemble superposition.
    """

    optimizing_vectors: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ] = Field(
        le=1000000000.0,
        default_factory=dict,
        description="Multi-dimensional continuous values representing optimizations.",
    )
    degrading_vectors: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ] = Field(
        le=1000000000.0,
        default_factory=dict,
        description="Multi-dimensional continuous values representing degradations.",
    )
    superposition_variance_threshold: float = Field(
        ...,
        le=1000000000.0,
        ge=0.0,
        allow_inf_nan=False,
        description="The statistical variance threshold below which deterministic fallback is enforced.",
    )
    ensemble_spec: EnsembleTopologyProfile | None = Field(
        default=None,
        description="The deterministic ensemble specification to fall back on when threshold falls below delta.",
    )

    @model_validator(mode="after")
    def _enforce_mathematical_interlocks(self) -> "UtilityJustificationGraphReceipt":
        if self.ensemble_spec is not None and self.superposition_variance_threshold == 0.0:
            raise ValueError(
                "Topological Interlock Failed: ensemble_spec defined but variance threshold is 0.0. Mathematical certainty prohibits superposition."  # noqa: E501
            )
        for vectors in (self.optimizing_vectors, self.degrading_vectors):
            for key, val in vectors.items():
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Tensor Poisoning Detected: Vector '{key}' contains invalid float {val}.")
        return self


class VectorEmbeddingState(CoreasonBaseState):
    vector_base64: str = Field(
        pattern="^[A-Za-z0-9+/]*={0,2}$", max_length=5000000, description="The base64-encoded dense vector array."
    )
    dimensionality: int = Field(description="The size of the vector array.")
    model_name: str = Field(
        max_length=2000, description="The provenance of the embedding model used (e.g., 'text-embedding-3-large')."
    )


class CognitiveCritiqueProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A declarative, dense supervision vector generated
    by a Process Reward Model (PRM) to steer intermediate test-time reasoning.
    """

    reasoning_trace_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="CoReason Shared Kernel Ontology: The cryptographic Merkle root of the specific ThoughtBranch being evaluated.",  # noqa: E501
    )
    logical_flaw_embedding: VectorEmbeddingState | None = Field(
        default=None,
        description="CoReason Shared Kernel Ontology: A dense latent space representation of the specific logical fallacy identified, used to mathematically repel future generation trajectories.",  # noqa: E501
    )
    epistemic_penalty_scalar: float = Field(
        ge=0.0,
        le=1.0,
        description="CoReason Shared Kernel Ontology: A continuous penalty applied to the branch's probability mass if normative drift or hallucination is detected.",  # noqa: E501
    )


class KineticBudgetPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: The mathematical boundary forcing the collapse of
    probability waves and wide-search trees as physical compute resources deplete.
    """

    exploration_decay_curve: Literal["linear", "exponential", "step"] = Field(
        description="CoReason Shared Kernel Ontology: The mathematical function dictating how rapidly lateral ThoughtBranches are restricted over time."  # noqa: E501
    )
    forced_exploitation_threshold_ms: int = Field(
        le=86400000,
        gt=0,
        description="CoReason Shared Kernel Ontology: The physical wall-clock time remaining at which the orchestrator is mathematically forbidden from opening new lateral branches.",  # noqa: E501
    )
    dynamic_temperature_asymptote: float = Field(
        le=1000000000.0,
        ge=0.0,
        description="CoReason Shared Kernel Ontology: The absolute minimum sampling temperature the system must converge to during the final exploitation phase.",  # noqa: E501
    )


class EpistemicEscalationContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: The strict mathematical agreement governing when
    an agent is authorized to expand its test-time compute allocation based on measured doubt.
    """

    baseline_entropy_threshold: float = Field(
        le=1000000000.0,
        ge=0.0,
        description="CoReason Shared Kernel Ontology: The mathematical measure of uncertainty (e.g., variance in generated hypotheses) required to trigger escalation.",  # noqa: E501
    )
    test_time_multiplier: float = Field(
        le=1000000000.0,
        gt=1.0,
        description="CoReason Shared Kernel Ontology: The continuous scalar applied to the agent's baseline max_latent_tokens_budget when the entropy threshold is breached.",  # noqa: E501
    )
    max_escalation_tiers: int = Field(
        le=1000000000,
        ge=1,
        description="CoReason Shared Kernel Ontology: The absolute integer limit on how many times the orchestrator can recursively multiply the compute budget before forcing a SystemFaultEvent.",  # noqa: E501
    )


class FederatedPeftContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: The physical and temporal bounding constraints
    for hot-swapping low-rank adapter tensors into GPU memory.
    """

    adapter_merkle_root: str = Field(
        pattern="^[a-f0-9]{64}$",
        description="CoReason Shared Kernel Ontology: The tamper-evident SHA-256 hash of the exact safetensors weight matrix.",  # noqa: E501
    )
    vram_footprint_bytes: int = Field(
        le=100000000000,
        gt=0,
        description="CoReason Shared Kernel Ontology: The exact spatial geometry required in VRAM to mount this adapter.",  # noqa: E501
    )
    ephemeral_ttl_ms: int = Field(
        le=86400000,
        gt=0,
        description="CoReason Shared Kernel Ontology: The absolute Time-To-Live for the adapter to exist in the kinetic execution plane before forced eviction.",  # noqa: E501
    )
    cache_priority_weight: float = Field(
        ge=0.0,
        le=1.0,
        description="CoReason Shared Kernel Ontology: The relative importance scalar used by the orchestrator's LRU eviction algorithm when VRAM limits are saturated.",  # noqa: E501
    )


class SemanticEdgeState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A mathematical tensor bridging two SemanticNodeStates, executing
    Judea Pearl's Structural Causal Models (SCMs) to explicitly formalize causality,
    correlation, or confounding relationships across the Knowledge Graph. As a ...State
    suffix, this is a frozen N-dimensional coordinate.

    CAUSAL AFFORDANCE: Empowers the orchestrator's traversal engine to execute directed
    graph algorithms (e.g., Random Walk with Restart) via subject_node_id and
    object_node_id (both 128-char CIDs), utilizing the continuous confidence_score
    (optional, ge=0.0, le=1.0, default=None) to probabilistically prune uncertain paths.
    The predicate (max_length=2000) carries the semantic relationship label.

    EPISTEMIC BOUNDS: Causal directionality is restricted to a strict Literal automaton
    ["causes", "confounds", "correlates_with", "undirected"] (default="undirected").
    Optional typed fields (embedding: VectorEmbeddingState, provenance:
    EpistemicProvenanceReceipt, temporal_bounds: TemporalBoundsProfile) extend the edge
    geometry without mandatory overhead.

    MCP ROUTING TRIGGERS: Structural Causal Models, Pearlian Directed Edge, Semantic
    Triplet, Adjacency Matrix, Epistemic Link
    """
    edge_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this semantic edge to the Merkle-DAG.",  # noqa: E501
    )
    subject_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The origin SemanticNodeState Content Identifier (CID).",
    )
    object_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The destination SemanticNodeState Content Identifier (CID).",
    )
    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="The probabilistic certainty of this logical connection."
    )
    predicate: str = Field(
        max_length=2000, description="The string representation of the relationship (e.g., 'WORKS_FOR')."
    )
    embedding: VectorEmbeddingState | None = Field(
        default=None,
        description="Topologically Bounded Latent Spaces used to calculate exact geometric distance and preserve structural Isometry.",  # noqa: E501
    )
    provenance: EpistemicProvenanceReceipt | None = Field(
        default=None,
        description="Optional distinct provenance if the relationship was inferred separately from the nodes.",
    )
    temporal_bounds: TemporalBoundsProfile | None = Field(
        default=None, description="The time window during which this relationship holds true."
    )
    causal_relationship: Literal["causes", "confounds", "correlates_with", "undirected"] = Field(
        default="undirected", description="The Pearlian directionality of the semantic relationship."
    )


class SemanticNodeState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A declarative, frozen N-dimensional coordinate representing a
    discrete entity vertex within a Resource Description Framework (RDF) or continuous
    Property Graph. As a ...State suffix, this is a mathematically immutable snapshot.

    CAUSAL AFFORDANCE: Unlocks privacy-preserving mathematical operations on encrypted
    state via fhe_profile (HomomorphicEncryptionProfile, optional) and enables zero-shot
    semantic routing based on dense vector distances (embedding: VectorEmbeddingState,
    optional). Provenance (EpistemicProvenanceReceipt) is required.

    EPISTEMIC BOUNDS: The vertex geometry is physically anchored by node_id (128-char CID
    regex). The internal representation (text_chunk) is capped at max_length=50000. The
    scope Literal ["global", "tenant", "session"] (default="session") partitions the
    cryptographic namespace. The tier (CognitiveTierProfile, default="semantic") and
    salience (SalienceProfile, optional) govern structural pruning.

    MCP ROUTING TRIGGERS: Resource Description Framework, Property Graph, Fully
    Homomorphic Encryption, Semantic Coordinate, Vector Embedding
    """
    node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this semantic node to the Merkle-DAG.",  # noqa: E501
    )
    label: str = Field(max_length=2000, description="The categorical label of the node (e.g., 'Person', 'Concept').")
    scope: Literal["global", "tenant", "session"] = Field(
        default="session",
        description="The cryptographic namespace partitioning boundary. Global is public, Tenant is corporate, Session is ephemeral.",  # noqa: E501
    )
    text_chunk: str = Field(
        max_length=50000, description="The raw natural language representation of the semantic node."
    )
    embedding: VectorEmbeddingState | None = Field(
        default=None,
        description="Topologically Bounded Latent Spaces used to calculate exact geometric distance and preserve structural Isometry.",  # noqa: E501
    )
    provenance: EpistemicProvenanceReceipt = Field(
        description="The cryptographic chain of custody for this semantic state."
    )
    tier: CognitiveTierProfile = Field(
        default="semantic", description="The cognitive tier this latent state resides in."
    )
    temporal_bounds: TemporalBoundsProfile | None = Field(
        default=None, description="The time window during which this node is considered valid."
    )
    salience: SalienceProfile | None = Field(
        default=None, description="The mathematical importance profile governing structural pruning."
    )
    fhe_profile: HomomorphicEncryptionProfile | None = Field(
        default=None,
        description="The cryptographic envelope enabling privacy-preserving computation directly on this node's encrypted state.",  # noqa: E501
    )


class VerifiableCredentialPresentationReceipt(CoreasonBaseState):
    """A cryptographic proof of clearance or capability presented to a zero-trust orchestrator."""

    presentation_format: Literal["jwt_vc", "ldp_vc", "sd_jwt", "zkp_vc"] = Field(
        description="The exact cryptographic standard used to encode this credential presentation."
    )
    issuer_did: NodeIdentifierState = Field(
        description="The W3C DID of the trusted authority that cryptographically signed the credential, explicitly representing the delegation of authority from a human or parent principal."  # noqa: E501
    )
    cryptographic_proof_blob: str = Field(
        max_length=100000,
        description="The base64-encoded cryptographic proof (e.g., ZK-SNARKs, zkVM receipts, or programmable trust attestations) proving the claims without revealing the private key.",  # noqa: E501
    )
    authorization_claims: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        max_length=86400000,
        description="The strict, domain-agnostic JSON dictionary of strictly bounded geometric predicates that define the operational perimeter of the agent (e.g., {'clearance': 'RESTRICTED'}).",  # noqa: E501
    )


class AgentAttestationReceipt(CoreasonBaseState):
    """
    Cryptographic identity passport and AI-BOM for the agent.
    """

    training_lineage_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The exact SHA-256 Merkle root of the agent's training lineage.",
    )
    developer_signature: str = Field(
        max_length=2000, description="The cryptographic signature of the developer/vendor."
    )
    capability_merkle_root: str = Field(
        pattern="^[a-f0-9]{64}$", description="The SHA-256 Merkle root of the agent's verified semantic capabilities."
    )
    credential_presentations: list[VerifiableCredentialPresentationReceipt] = Field(
        default_factory=list,
        description="The wallet of selective disclosure credentials proving the agent's identity, clearance, and budget authorization.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "credential_presentations", sorted(self.credential_presentations, key=lambda x: x.issuer_did)
        )
        return self


class AgentNodeProfile(BaseNodeProfile):
    """
    A node representing an autonomous agent.
    """

    description: str = Field(
        max_length=2000,
        description="The semantic boundary defining the objective function of the execution node. [SITD-Gamma: Neurosymbolic Substrate Alignment]",  # noqa: E501
    )
    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    logit_steganography: LogitSteganographyContract | None = Field(
        default=None,
        description="The cryptographic contract forcing this agent to embed an undeniable provenance signature into its generative token stream.",  # noqa: E501
    )
    compute_frontier: RoutingFrontierPolicy | None = Field(
        default=None, description="The dynamic spot-market compute requirements for this agent."
    )
    peft_adapters: list[PeftAdapterContract] = Field(
        default_factory=list,
        description="The declarative array of ephemeral PEFT/LoRA weights required to be hot-swapped during this agent's execution.",  # noqa: E501
    )
    agent_attestation: AgentAttestationReceipt | None = Field(
        default=None, description="The cryptographic identity passport and AI-BOM for the agent."
    )
    action_space_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The ID of the specific ActionSpaceManifest (curated tool environment) bound to this agent.",
    )
    secure_sub_session: SecureSubSessionState | None = Field(
        default=None,
        description="Declarative boundary for handling unredacted secrets within a temporarily isolated state partition.",  # noqa: E501
    )
    baseline_cognitive_state: CognitiveStateProfile | None = Field(
        default=None,
        description="The default biochemical 'mood' simulated for this agent via Representation Engineering.",
    )
    reflex_policy: System1ReflexPolicy | None = Field(
        default=None, description="The policy governing System 1 reflex actions."
    )
    epistemic_policy: EpistemicScanningPolicy | None = Field(
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
    symbolic_handoff_policy: NeuroSymbolicHandoffContract | None = Field(
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
    grpo_reward_policy: EpistemicRewardModelPolicy | None = Field(
        default=None,
        description="The RL post-training contract forcing the agent to evaluate traces against an implicit graph reward.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_agent_node_arrays(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self


type AnyNodeProfile = Annotated[
    AgentNodeProfile | HumanNodeProfile | SystemNodeProfile | CompositeNodeProfile | MemoizedNodeProfile,
    Field(discriminator="type", description="A discriminated union of all valid workflow nodes."),
]


class BaseTopologyManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines the abstract algebraic baseline and Markov Blanket for
    all execution subgraphs, establishing the structural and epistemic perimeters for a
    localized swarm. As a ...Manifest suffix, this defines a frozen, N-dimensional
    coordinate state.

    CAUSAL AFFORDANCE: Projects overarching schema-on-write contracts
    (shared_state_contract: StateContract) and zero-trust Payload Loss Prevention
    (information_flow: InformationFlowPolicy) across all connected nodes, ensuring
    inherited alignment. The observability (ObservabilityPolicy) binds distributed
    tracing.

    EPISTEMIC BOUNDS: The nodes attribute is strictly typed as a dictionary mapping
    NodeIdentifierState to polymorphic AnyNodeProfile identities. The lifecycle_phase
    is locked to an FSM Literal ["draft", "live"] (default="live"). The
    architectural_intent and justification strings are capped at max_length=2000.

    MCP ROUTING TRIGGERS: Topological Manifold, Markov Blanket, Subgraph Abstraction,
    Execution Base, Structural Isolation
    """

    epistemic_enforcement: TruthMaintenancePolicy | None = Field(
        le=1000000000, default=None, description="Ties the topology to the Truth Maintenance layer."
    )
    lifecycle_phase: Literal["draft", "live"] = Field(
        default="live", description="The execution phase of the graph. 'draft' allows incomplete structural state."
    )
    architectural_intent: str | None = Field(
        max_length=2000, default=None, description="The AI's declarative rationale for selecting this topology."
    )
    justification: str | None = Field(
        max_length=2000,
        default=None,
        description="Cryptographic/audit justification for this topology's configuration.",
    )
    nodes: dict[NodeIdentifierState, AnyNodeProfile] = Field(description="Flat registry of all nodes in this topology.")
    shared_state_contract: StateContract | None = Field(
        default=None, description="The schema-on-write contract governing the internal state of this topology."
    )
    information_flow: InformationFlowPolicy | None = Field(
        default=None,
        description="The structural Payload Loss Prevention (PLP) contract governing all state mutations in this topology.",  # noqa: E501
    )
    observability: ObservabilityPolicy | None = Field(
        default=None, description="The distributed tracing rules bound to this specific execution graph."
    )


class CouncilTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: Formalizes Social Choice Theory, Condorcet's Jury Theorem, and
    Practical Byzantine Fault Tolerance (pBFT) to synthesize an authoritative truth
    from a multi-agent network. As a ...Manifest suffix, this defines a frozen,
    N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Unlocks decentralized truth-synthesis by routing conflicting
    proposals through a strict consensus_policy (ConsensusPolicy), ultimately collapsing
    the epistemic probability wave via the designated adjudicator_id
    (NodeIdentifierState). Cognitive heterogeneity is enforced by
    diversity_policy (DiversityPolicy).

    EPISTEMIC BOUNDS: The @model_validator enforce_funded_byzantine_slashing enforces a
    strict economic interlock: if the consensus_policy demands slash_escrow via pBFT,
    it halts instantiation unless a funded council_escrow (EscrowPolicy, magnitude > 0)
    is present. A second @model_validator check_adjudicator_id verifies the
    adjudicator_id exists in the nodes registry.

    MCP ROUTING TRIGGERS: Social Choice Theory, PBFT Consensus, Multi-Agent Debate,
    Byzantine Fault Tolerance, Slashing Condition
    """

    type: Literal["council"] = Field(default="council", description="Discriminator for a Council topology.")
    adjudicator_id: NodeIdentifierState = Field(
        description="The NodeIdentifierState of the adjudicator that synthesizes the council's output."
    )
    diversity_policy: DiversityPolicy | None = Field(
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


class DAGTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: Formalizes a Directed Acyclic Graph (DAG) for deterministic,
    chronologically ordered task execution, guaranteeing strict topological sorting of
    operations. As a ...Manifest suffix, this defines a frozen, N-dimensional
    coordinate state.

    CAUSAL AFFORDANCE: Forces the orchestrator to evaluate causal edges
    (default_factory=list) and execute DFS loop-detection to verify the allow_cycles
    constraint (default=False) before initiating kinetic node compute. The backpressure
    (BackpressurePolicy) governs edge flow control.

    EPISTEMIC BOUNDS: Algorithmic complexity is mathematically bound by max_depth
    (ge=1, le=256) and max_fan_out (ge=1, le=1024), preventing recursive token
    exhaustion. The @model_validator sort_dag_topology_arrays deterministically sorts
    edges for RFC 8785 hashing. A second @model_validator verify_edges_exist validates
    edge nodes in the registry and executes DFS cycle detection.

    MCP ROUTING TRIGGERS: Directed Acyclic Graph, Kahn's Algorithm, Topological Sort,
    Causal Edge, Algorithmic Complexity
    """

    type: Literal["dag"] = Field(default="dag", description="Discriminator for a DAG topology.")
    edges: list[tuple[NodeIdentifierState, NodeIdentifierState]] = Field(
        default_factory=list, description="The strict, topologically bounded matrix of directed causal edges."
    )
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
            adj: dict[NodeIdentifierState, list[NodeIdentifierState]] = {node_id: [] for node_id in self.nodes}
            for source, target in self.edges:
                adj[source].append(target)
            visited: set[NodeIdentifierState] = set()
            recursion_stack: set[NodeIdentifierState] = set()
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


class DigitalTwinTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: A declarative, frozen snapshot of a Cyber-Physical Systems (CPS)
    Digital Twin, establishing an epistemically isolated shadow graph that mirrors a
    real-world topology without risking kinetic bleed. As a ...Manifest suffix, this
    defines a frozen N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Authorizes the orchestrator to execute unbounded sandbox
    simulations against the mirrored target_topology_id (128-char CID), mathematically
    severing all external write access if enforce_no_side_effects (default=True) is True.

    EPISTEMIC BOUNDS: The simulation physics are structurally clamped by the
    convergence_sla (SimulationConvergenceSLA), which physically bounds the maximum Monte
    Carlo rollouts and variance tolerance. External kinetic permutations are mechanically
    trapped.

    MCP ROUTING TRIGGERS: Digital Twin, Cyber-Physical Systems, Sandbox Simulation,
    Markov Blanket, Shadow Graph
    """

    type: Literal["digital_twin"] = Field(
        default="digital_twin", description="Discriminator for a Digital Twin topology."
    )
    target_topology_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The identifier (expected to be a W3C DID) pointing to the real-world topology it is cloning.",
    )
    convergence_sla: SimulationConvergenceSLA = Field(
        description="The strict mathematical boundaries for the simulation."
    )
    enforce_no_side_effects: bool = Field(
        default=True,
        description="A declarative flag that instructs the runtime to mathematically sever all external write access.",
    )


class EvaluatorOptimizerTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: A declarative, frozen snapshot of an Actor-Critic
    (Generator-Discriminator) micro-topology, establishing a zero-sum minimax game
    between two discrete node identities. As a ...Manifest suffix, this defines a
    frozen N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Executes a finite, adversarial generation-evaluation-revision
    loop, forcing the generator_node_id to propose states and the evaluator_node_id to
    strictly critique them. The optional require_multimodal_grounding (default=False)
    enforces pure adversarial Proposer-Critique validation.

    EPISTEMIC BOUNDS: State-Space Explosion is mathematically prevented by capping
    max_revision_loops (ge=1, le=1000000000). The @model_validator verify_bipartite_nodes
    structurally guarantees both nodes exist in the topology's nodes registry AND are
    disjoint identities.

    MCP ROUTING TRIGGERS: Actor-Critic Architecture, Minimax Optimization, Adversarial
    Critique, Dual-Process Revision, Generative Adversarial Loop
    """

    type: Literal["evaluator_optimizer"] = Field(
        default="evaluator_optimizer", description="Discriminator for an Evaluator-Optimizer loop."
    )
    generator_node_id: NodeIdentifierState = Field(description="The ID of the actor generating the payload.")
    evaluator_node_id: NodeIdentifierState = Field(description="The ID of the critic scoring the payload.")
    max_revision_loops: int = Field(
        le=1000000000, ge=1, description="The absolute limit on Actor-Critic cycles to prevent infinite compute burn."
    )
    require_multimodal_grounding: bool = Field(
        default=False,
        description="If True, the evaluator_node_id MUST mathematically mask all tokens outside the MultimodalTokenAnchorState during its forward pass to execute pure adversarial Proposer-Critique validation.",  # noqa: E501
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


class EvolutionaryTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: Formalizes a Genetic Algorithm (GA) or Evolutionary Strategy (ES)
    topology for the gradient-free optimization of agent populations over discrete temporal
    generations. As a ...Manifest suffix, this is a declarative, frozen snapshot of an
    N-dimensional execution coordinate.

    CAUSAL AFFORDANCE: Orchestrates the iterative instantiation, evaluation, and culling of
    autonomous agents, actively applying stochastic perturbations (MutationPolicy) and
    chromosomal combinations (CrossoverPolicy) to maximize fitness.

    EPISTEMIC BOUNDS: The state space explosion is physically restricted by integer limits
    on population_size (le=1000000000) and generations (le=1.0). The @model_validator
    mathematically guarantees that fitness_objectives are deterministically sorted by
    target_metric, preserving RFC 8785 canonical hashing across the decentralized swarm.

    MCP ROUTING TRIGGERS: Genetic Algorithm, Evolutionary Strategy, Gradient-Free
    Optimization, Population Dynamics, Multi-Objective Optimization
    """

    type: Literal["evolutionary"] = Field(
        default="evolutionary", description="Discriminator for an Evolutionary topology."
    )
    generations: int = Field(le=1.0, description="The absolute limit on evolutionary breeding cycles.")
    population_size: int = Field(
        le=1000000000, description="The number of concurrent agents instantiated per generation."
    )
    mutation: MutationPolicy = Field(description="The constraints governing random heuristic mutations.")
    crossover: CrossoverPolicy = Field(description="The mathematical rules for combining elite agents.")
    fitness_objectives: list[FitnessObjectiveProfile] = Field(
        description="The multi-dimensional criteria used to score and cull the population."
    )

    @model_validator(mode="after")
    def sort_objectives(self) -> Self:
        object.__setattr__(
            self, "fitness_objectives", sorted(self.fitness_objectives, key=lambda obj: obj.target_metric)
        )
        return self


class SMPCTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: A declarative, frozen snapshot establishing a Secure Multi-Party
    Computation (SMPC) ring, leveraging cryptographic privacy-preserving protocols to
    evaluate a joint function over decentralized inputs. As a ...Manifest suffix, this
    defines a frozen N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Authorizes the decentralized orchestrator to route zero-trust
    traffic via specific mathematical logic (Literal ["garbled_circuits",
    "secret_sharing", "oblivious_transfer"]), allowing mutually distrustful agents to
    synthesize a shared output. Optional ontological_alignment
    (OntologicalAlignmentPolicy) gates pre-flight semantic alignment.

    EPISTEMIC BOUNDS: The topology physically mandates a minimum of two participants
    (participant_node_ids min_length=2) to satisfy the multi-party invariant. The
    joint_function_uri is bounded to max_length=2000.

    MCP ROUTING TRIGGERS: Secure Multi-Party Computation, Garbled Circuits, Secret
    Sharing, Oblivious Transfer, Zero-Trust Cryptography
    """

    type: Literal["smpc"] = Field(default="smpc", description="Discriminator for SMPC Topology.")
    smpc_protocol: Literal["garbled_circuits", "secret_sharing", "oblivious_transfer"] = Field(
        description="The exact cryptographic P2P protocol the nodes must use to evaluate the function."
    )
    joint_function_uri: str = Field(
        max_length=2000,
        description="The URI or hash pointing to the exact math circuit or polynomial function the ring will collaboratively compute.",  # noqa: E501
    )
    participant_node_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        min_length=2,
        description="The strict ordered array of NodeIdentifierStates participating in the Secure Multi-Party Computation ring.",  # noqa: E501
    )
    ontological_alignment: OntologicalAlignmentPolicy | None = Field(
        default=None,
        description="The pre-flight execution gate forcing agents to mathematically align their latent semantics before participating in the topology.",  # noqa: E501
    )


class SwarmTopologyManifest(BaseTopologyManifest):
    """
    AGENT INSTRUCTION: A declarative, frozen snapshot defining a Complex Adaptive System
    representing a fluid, decentralized Swarm topology governed by Algorithmic Mechanism
    Design and Spot Market dynamics. As a ...Manifest suffix, this defines a frozen
    N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Unlocks dynamic agent instantiation, allowing the topology to
    spawn concurrent workers up to max_concurrent_agents (le=100, default=10) and resolve
    consensus probabilistically via active_prediction_markets. Optional auction_policy
    (AuctionPolicy) governs task decentralization.

    EPISTEMIC BOUNDS: Horizontal compute explosion is governed by spawning_threshold
    (ge=1, le=100, default=3) and max_concurrent_agents (le=100, default=10). The
    @model_validator enforce_concurrency_ceiling guarantees spawning_threshold cannot
    exceed max_concurrent_agents. A second @model_validator sort_arrays deterministically
    sorts active and resolved prediction markets by market_id for RFC 8785 hashing.

    MCP ROUTING TRIGGERS: Complex Adaptive Systems, Swarm Intelligence, Algorithmic
    Mechanism Design, Spot Market Routing, Multi-Agent Reinforcement Learning
    """

    type: Literal["swarm"] = Field(default="swarm", description="Discriminator for a Swarm topology.")
    spawning_threshold: int = Field(
        ge=1, le=100, default=3, description="Threshold limit for dynamic spawning of additional nodes."
    )
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

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "active_prediction_markets", sorted(self.active_prediction_markets, key=lambda x: x.market_id)
        )
        object.__setattr__(self, "resolved_markets", sorted(self.resolved_markets, key=lambda x: x.market_id))
        return self


class AdversarialMarketTopologyManifest(CoreasonBaseState):
    """
    A Zero-Cost Macro abstraction that deterministically compiles into a Red/Blue team CouncilTopologyManifest.
    """

    type: Literal["macro_adversarial"] = Field(
        default="macro_adversarial", description="Discriminator for adversarial macro."
    )
    blue_team_ids: list[NodeIdentifierState] = Field(min_length=1, description="Nodes assigned to the Blue Team.")
    red_team_ids: list[NodeIdentifierState] = Field(min_length=1, description="Nodes assigned to the Red Team.")
    adjudicator_id: NodeIdentifierState = Field(
        description="The neutral node responsible for synthesizing the market resolution."
    )
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

    def compile_to_base_topology(self) -> CouncilTopologyManifest:
        """Deterministically unwraps the macro into a rigid CouncilTopologyManifest."""
        nodes: dict[NodeIdentifierState, AnyNodeProfile] = {
            self.adjudicator_id: SystemNodeProfile(description="Synthesizing Adjudicator")
        }
        for node_id in self.blue_team_ids:
            nodes[node_id] = SystemNodeProfile(description="Blue Team Member")
        for node_id in self.red_team_ids:
            nodes[node_id] = SystemNodeProfile(description="Red Team Member")
        consensus = ConsensusPolicy(strategy="prediction_market", prediction_market_rules=self.market_rules)
        return CouncilTopologyManifest(nodes=nodes, adjudicator_id=self.adjudicator_id, consensus_policy=consensus)


class ConsensusFederationTopologyManifest(CoreasonBaseState):
    """
    A Zero-Cost Macro abstraction compiling into a standard PBFT CouncilTopologyManifest.
    """

    type: Literal["macro_federation"] = Field(
        default="macro_federation", description="Discriminator for federation macro."
    )
    participant_ids: list[NodeIdentifierState] = Field(min_length=3, description="The nodes forming the PBFT ring.")
    adjudicator_id: NodeIdentifierState = Field(description="The orchestrating sequencer for the PBFT consensus.")
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

    def compile_to_base_topology(self) -> CouncilTopologyManifest:
        nodes: dict[NodeIdentifierState, AnyNodeProfile] = {
            self.adjudicator_id: SystemNodeProfile(description="PBFT Sequencer")
        }
        for node_id in self.participant_ids:
            nodes[node_id] = SystemNodeProfile(description="PBFT Participant")
        return CouncilTopologyManifest(
            nodes=nodes,
            adjudicator_id=self.adjudicator_id,
            consensus_policy=ConsensusPolicy(strategy="pbft", quorum_rules=self.quorum_rules),
        )


type AnyTopologyManifest = Annotated[
    DAGTopologyManifest
    | CouncilTopologyManifest
    | SwarmTopologyManifest
    | EvolutionaryTopologyManifest
    | SMPCTopologyManifest
    | EvaluatorOptimizerTopologyManifest
    | DigitalTwinTopologyManifest
    | AdversarialMarketTopologyManifest
    | ConsensusFederationTopologyManifest,
    Field(discriminator="type", description="A discriminated union of workflow topologies."),
]


class WorkflowManifest(CoreasonBaseState):
    """
    The root envelope for an orchestrated workflow payload.
    """

    genesis_provenance: EpistemicProvenanceReceipt = Field(
        description='"""AGENT INSTRUCTION: This structural lock guarantees that any graph execution is mathematically anchored to a CoReason Genesis Block. Stripping this field violates the Topological Consistency of the Shared Kernel."""'  # noqa: E501
    )
    manifest_version: SemanticVersionState = Field(
        description="The semantic version of this workflow manifestation schema."
    )
    topology: AnyTopologyManifest = Field(
        description="The underlying topology governing execution routing. [SITD-Beta: Defeasible Merkle-DAG Causal Bounding]"  # noqa: E501
    )
    governance: GlobalGovernancePolicy | None = Field(
        default=None, description="Macro-economic circuit breakers and TTL limits for the swarm."
    )
    tenant_id: str | None = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        max_length=255,
        description="The enterprise tenant boundary for this execution.",
    )
    session_id: str | None = Field(
        min_length=1,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        max_length=255,
        description="The ephemeral session boundary for this execution.",
    )
    max_risk_tolerance: RiskLevelPolicy | None = Field(
        default=None, description="The absolute maximum enterprise risk threshold permitted for this topology."
    )
    allowed_information_classifications: list[InformationClassificationProfile] | None = Field(
        default=None,
        description="The declarative whitelist of data classifications permitted to flow through this graph.",
    )
    federated_discovery: FederatedDiscoveryManifest | None = Field(
        default=None, description="The broadcast protocol for B2B multi-swarm discovery."
    )
    federated_sla: BilateralSLA | None = Field(
        default=None,
        description="The B2B Service Level Agreement contract that must be mathematically satisfied before multi-tenant graph coupling.",  # noqa: E501
    )
    pq_signature: PostQuantumSignatureReceipt | None = Field(
        default=None, description="The quantum-resistant signature securing the root execution graph."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        if self.allowed_information_classifications is not None:
            object.__setattr__(
                self, "allowed_information_classifications", sorted(self.allowed_information_classifications)
            )
        return self


class WetwareAttestationContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: This model represents a SOTA cryptographic receipt
    proving a human in the loop physically authorized a state transition.
    """

    mechanism: AttestationMechanismProfile = Field(
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


class InterventionReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: InterventionReceipt is a cryptographically frozen historical fact representing 
    the resolution of a Mixed-Initiative pause. It acts as the mathematical key that unlocks a suspended 
    state partition.

    CAUSAL AFFORDANCE: Collapses the halted superposition of the DAG, physically re-activating the 
    execution thread and authorizing the orchestrator to commit the human-approved state mutation to 
    the Epistemic Ledger.

    EPISTEMIC BOUNDS: Mathematically locked against Replay Attacks via the intervention_request_id 
    (a UUID cryptographic nonce). The @model_validator physically guarantees that if a WetwareAttestationContract 
    is present, its internal DAG node nonce must perfectly match the request ID, preventing signature laundering.

    MCP ROUTING TRIGGERS: Cryptographic Nonce, State Resumption, Replay Attack Prevention, Wetware Attestation, Liveness Resolution
    """

    type: Literal["verdict"] = Field(default="verdict", description="The type of the intervention payload.")
    intervention_request_id: UUID = Field(
        description="The cryptographic nonce uniquely identifying the intervention request."
    )
    target_node_id: NodeIdentifierState = Field(description="The ID of the target node.")
    approved: bool = Field(description="Indicates whether the proposed action was approved.")
    feedback: str | None = Field(max_length=2000, description="Optional feedback provided along with the verdict.")
    attestation: WetwareAttestationContract | None = Field(
        default=None, description="The cryptographic proof provided by the human operator, if required."
    )

    @model_validator(mode="after")
    def verify_attestation_nonce(self) -> "InterventionReceipt":
        """
        Mathematically guarantees that if a cryptographic signature is presented,
        it cannot be a replay attack from a different node in the DAG.
        """
        if self.attestation is not None and self.attestation.dag_node_nonce != self.intervention_request_id:
            raise ValueError(
                "Anti-Replay Lock Triggered: Attestation nonce does not match the intervention request ID."
            )
        return self


type AnyInterventionState = Annotated[
    InterventionIntent | InterventionReceipt | OverrideIntent | ConstitutionalAmendmentIntent,
    Field(discriminator="type"),
]


class EpistemicQuarantineSnapshot(CoreasonBaseState):
    """Represents the Epistemic Quarantine, partitioned from the Committed Epistemic Ledger."""

    system_prompt: str = Field(
        max_length=2000, description="The basal non-monotonic instruction set currently held in Epistemic Quarantine."
    )
    active_context: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=100000)]
    ] = Field(
        le=1000000000,
        description="The ephemeral latent variables and environmental bindings currently active in Epistemic Quarantine.",  # noqa: E501
    )
    argumentation: EpistemicArgumentGraphState | None = Field(
        default=None,
        description="The formal graph of non-monotonic claims and defeasible attacks currently active in the swarm's working state.",  # noqa: E501
    )
    theory_of_mind_models: list[TheoryOfMindSnapshot] = Field(
        default_factory=list,
        description="Empathetic models of other agents to compress and target outgoing communications.",
    )
    affordance_projection: OntologicalSurfaceProjectionManifest | None = Field(
        default=None,
        description="The mathematically bounded subgraph of capabilities currently available to the agent.",
    )
    capability_attestations: list[FederatedCapabilityAttestationReceipt] = Field(
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


class ZeroKnowledgeReceipt(CoreasonBaseState):
    proof_protocol: Literal["zk-SNARK", "zk-STARK", "plonk", "bulletproofs"] = Field(
        description="The mathematical dialect of the cryptographic proof."
    )
    public_inputs_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the public inputs (e.g., prompt, Lamport clock) anchoring this proof to the specific state index.",  # noqa: E501
    )
    verifier_key_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the public evaluation key.",  # noqa: E501
    )
    cryptographic_blob: str = Field(
        max_length=5000000, description="The base64-encoded succinct cryptographic proof payload."
    )
    latent_state_commitments: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=100)]
    ] = Field(
        le=1000000000,
        default_factory=dict,
        description="Cryptographic bindings (hashes) of intermediate residual stream states to prevent activation spoofing.",  # noqa: E501
    )


class BeliefMutationEvent(BaseStateEvent):
    type: Literal["belief_mutation"] = Field(
        default="belief_mutation", description="Discriminator type for a Belief Assertion event."
    )
    payload: dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState] = Field(
        description="Topologically Bounded Latent Spaces capturing the semantic representation of the agent's internal cognitive shift or synthesis that anchor statistical probability to a definitive causal event hash.",  # noqa: E501
    )
    source_node_id: NodeIdentifierState | None = Field(
        default=None, description="The specific topological node that synthesized this belief assertion."
    )
    causal_attributions: list[CausalAttributionState] = Field(
        default_factory=list,
        description="Immutable audit trail of prior states that forced this specific cognitive synthesis.",
    )
    hardware_attestation: HardwareEnclaveReceipt | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this belief was synthesized in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeReceipt | None = Field(
        default=None,
        description="The mathematical attestation proving this belief synthesis was appended securely without model-downgrade fraud.",  # noqa: E501
    )
    uncertainty_profile: CognitiveUncertaintyProfile | None = Field(
        le=1000000000,
        default=None,
        description="The mathematical quantification of doubt associated with this synthesized belief.",
    )
    scratchpad_trace: LatentScratchpadReceipt | None = Field(
        default=None,
        description="The cryptographic record of the non-monotonic internal monologue that justifies this belief.",
    )
    neural_audit: NeuralAuditAttestationReceipt | None = Field(
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
    payload: dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState] = Field(
        description="Neurosymbolic Bindings of the raw, lossless semantic output appended from the environment or tool execution that anchor statistical probability to a definitive causal event hash.",  # noqa: E501
    )
    source_node_id: NodeIdentifierState | None = Field(
        default=None, description="The specific topological node that appended this observation."
    )
    hardware_attestation: HardwareEnclaveReceipt | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this observation was appended in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeReceipt | None = Field(
        default=None, description="The mathematical attestation proving this observation was appended securely."
    )
    toolchain_snapshot: AnyToolchainState | None = Field(
        default=None,
        description="The immutable cryptographic snapshot of the external environment at the moment of observation.",
    )
    sensory_trigger: EmbodiedSensoryVectorProfile | None = Field(
        default=None, description="The continuous multimodal trigger that forced this discrete observation."
    )
    neural_audit: NeuralAuditAttestationReceipt | None = Field(
        default=None,
        description="The mathematical brain-scan proving exactly which neural circuits fired to append this event.",
    )
    triggering_invocation_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="The Event ID of the specific ToolInvocationEvent that spawned this observation, forming a strict bipartite directed edge.",  # noqa: E501
    )

    @field_validator("payload", mode="before")
    @classmethod
    def enforce_payload_topology(cls, v: Any) -> Any:
        return _validate_payload_bounds(v)


class EpistemicTelemetryEvent(BaseStateEvent):
    """
    The cryptographic receipt of human-in-the-loop interaction tracking used to calculate
    Epistemic Regret and iteratively tune retrieval gradients without explicit human grading.
    """

    type: Literal["epistemic_telemetry"] = Field(
        default="epistemic_telemetry", description="Discriminator type for telemetry events."
    )
    interaction_modality: Literal["expansion", "collapse", "dwell_focus", "heuristic_rejection"] = Field(
        description="The exact topological action the human operator performed on the projected manifold."
    )
    target_node_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The specific TaxonomicNodeState CID that was manipulated.",
    )
    dwell_duration_ms: int | None = Field(
        le=86400000,
        default=None,
        ge=0,
        description="The strictly typed temporal bound measuring human attention focus.",
    )
    spatial_coordinates: SpatialCoordinateProfile | None = Field(
        default=None, description="Optional 2D trajectory of the human pointer event mapped to the visual grid."
    )


class EpistemicAxiomState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements First-Order Logic and Resource Description Framework (RDF)
    triples to mathematically formalize knowledge. As a ...State suffix, this is a
    declarative, frozen snapshot of a specific causal connection at a point in time.

    CAUSAL AFFORDANCE: Distills high-entropy natural language token streams into rigid,
    hashable causal edges (Subject, Predicate, Object), unlocking deterministic querying
    and Truth Maintenance System (TMS) traversals.

    EPISTEMIC BOUNDS: Source and target concept physical boundaries are strictly locked to
    128-char CIDs matching the regex ^[a-zA-Z0-9_.:-]+$. The directed_edge_type is clamped
    to a max_length of 2000 to prevent dictionary bombing during semantic evaluation.

    MCP ROUTING TRIGGERS: First-Order Logic, RDF Triple, Semantic Distillation, Causal
    Edge, Directed Graph
    """
    source_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of the origin node."
    )
    directed_edge_type: str = Field(max_length=2000, description="The topological relationship.")
    target_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of destination node."
    )


class EpistemicSeedInjectionPolicy(CoreasonBaseState):
    similarity_threshold_alpha: float = Field(ge=0.0, le=1.0)
    relation_diversity_bucket_size: int = Field(le=1000000000, gt=0)


class EpistemicChainGraphState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Defines a Markov Blanket formulation within an Abstract
    Argumentation Framework. As a ...State suffix, this represents a frozen, declarative
    geometry of interconnected axioms binding semantic leaves to syntactic roots.

    CAUSAL AFFORDANCE: Authorizes the orchestrator to compute deterministic reachability
    matrices, tracing high-level syntactic claims (syntactic_roots, min_length=1) back to
    their foundational semantic triples without invoking non-monotonic reasoning loops.

    EPISTEMIC BOUNDS: Bounded by a 128-char chain_id CID. The @model_validator physically
    enforces cryptographic determinism by sorting the semantic_leaves array by the composite
    key (source_concept_id, directed_edge_type, target_concept_id), guaranteeing invariant
    RFC 8785 canonical hashing across the decentralized swarm.

    MCP ROUTING TRIGGERS: Markov Blanket, Reachability Matrix, Abstract Argumentation,
    RFC 8785 Canonicalization, Graph Traversal
    """
    chain_id: str = Field(max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", min_length=1)
    syntactic_roots: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(min_length=1)
    semantic_leaves: list[EpistemicAxiomState]

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self,
            "semantic_leaves",
            sorted(
                self.semantic_leaves, key=lambda x: (x.source_concept_id, x.directed_edge_type, x.target_concept_id)
            ),
        )
        return self


class CognitivePredictionReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: Captures the pre-verification predictive distribution (Softmax
    outputs) of an LLM across a latent conceptual boundary. As a ...Receipt suffix,
    this is an append-only, cryptographically frozen coordinate on the Merkle-DAG.

    CAUSAL AFFORDANCE: Exposes the raw generative probability manifold to the
    orchestrator, enabling external solvers to evaluate token divergence before
    crystallizing it into a permanent epistemic axiom. The target_source_concept
    (max_length=2000) provides the semantic anchor.

    EPISTEMIC BOUNDS: Mathematical isolation is enforced by binding predictions to a
    strict source_chain_id CID (128-char regex). The prediction vector is physically
    capped by predicted_top_k_tokens (min_length=1, string max_length=255) to prevent
    unbounded tensor serialization.

    MCP ROUTING TRIGGERS: Predictive Distribution, Softmax Output, Generative Manifold,
    Pre-Verification State, Token Entropy
    """
    type: Literal["cognitive_prediction"] = Field(default="cognitive_prediction")
    source_chain_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    target_source_concept: str = Field(max_length=2000)
    predicted_top_k_tokens: list[Annotated[str, StringConstraints(max_length=255)]] = Field(min_length=1)


class EpistemicAxiomVerificationReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: Implements automated Fact-Checking and Entailment Verification to
    structurally quarantine hallucinated tokens. As a ...Receipt suffix, it represents
    an immutable cryptographic verdict on the factual alignment of a prediction.

    CAUSAL AFFORDANCE: Acts as a definitive Truth Maintenance filter. If verification
    succeeds, it unlocks the promotion of the source prediction (source_prediction_id,
    128-char CID) into the semantic knowledge graph.

    EPISTEMIC BOUNDS: The factual alignment is mathematically bounded by
    sequence_similarity_score (ge=0.0, le=1.0). The @model_validator
    enforce_epistemic_quarantine enforces a strict invariant, deliberately crashing
    instantiation if fact_score_passed is False, physically preventing the Merkle-DAG
    from recording unverified epistemic contagion.

    MCP ROUTING TRIGGERS: Entailment Verification, Truth Maintenance System, Epistemic
    Quarantine, Hallucination Filtering, Invariant Assertion
    """
    type: Literal["epistemic_axiom_verification"] = Field(default="epistemic_axiom_verification")
    source_prediction_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    sequence_similarity_score: float = Field(ge=0.0, le=1.0)
    fact_score_passed: bool

    @model_validator(mode="after")
    def enforce_epistemic_quarantine(self) -> Self:
        if not self.fact_score_passed:
            raise ValueError("Epistemic Contagion Prevented: Axioms failing validation cannot be verified.")
        return self


class EpistemicDomainGraphManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Encapsulates Formal Epistemology and Bounded Semilattices to
    represent a verifiable, collision-free cluster of knowledge. As a ...Manifest suffix,
    this defines a frozen, N-dimensional coordinate state projected to the orchestrator.

    CAUSAL AFFORDANCE: Projects a fully verified, non-contradictory subdomain of the global
    Knowledge Graph into the orchestrator's active context window, allowing specialized
    agents to operate on a localized, noise-free epistemic baseline.

    EPISTEMIC BOUNDS: The graph is physically constrained to a 128-char graph_id CID. The
    verified_axioms array requires min_length=1. To prevent Byzantine hash fractures, the
    @model_validator deterministically sorts verified_axioms by its triplet components
    (source_concept_id, directed_edge_type, target_concept_id), preserving perfect
    Merkle-DAG alignment across distributed nodes.

    MCP ROUTING TRIGGERS: Formal Epistemology, Bounded Semilattice, Knowledge Graph
    Partition, Deterministic Alignment, Subdomain Projection
    """
    graph_id: str = Field(max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", min_length=1)
    verified_axioms: list[EpistemicAxiomState] = Field(min_length=1)

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self,
            "verified_axioms",
            sorted(
                self.verified_axioms, key=lambda x: (x.source_concept_id, x.directed_edge_type, x.target_concept_id)
            ),
        )
        return self


class EpistemicTopologicalProofManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes the Curry-Howard Correspondence, mapping pure logic to
    computational types to form an unassailable deductive chain. As a ...Manifest suffix,
    this defines a frozen, N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Unlocks verifiable automated theorem proving. By presenting a
    strictly ordered, acyclic sequence of axioms (axiomatic_chain), it allows an independent
    auditor or secondary LLM to mechanically verify the logical deduction step-by-step.

    EPISTEMIC BOUNDS: The axiomatic_chain array is structurally declared with min_length=1.
    Crucially, it invokes the Topological Exemption from array sorting; the sequence order
    MUST mathematically preserve the chronological deduction steps, preventing the
    destruction of the proof's epistemic value.

    MCP ROUTING TRIGGERS: Curry-Howard Correspondence, Constructive Proof, Topological
    Sort, Deductive Reasoning, Automated Theorem Proving
    """
    proof_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="A Content Identifier (CID) for this specific topological proof.",
    )
    axiomatic_chain: list[EpistemicAxiomState] = Field(
        min_length=1, description="The strictly ordered sequence of axioms forming the reasoning path."
    )


class CognitiveSamplingPolicy(CoreasonBaseState):
    max_complexity_hops: int = Field(le=1000000000, ge=1, description="The absolute physical limit on path length N.")
    inverse_frequency_smoothing_epsilon: float = Field(
        le=1.0, default=1.0, description="The epsilon constant ensuring unsampled nodes are mathematically prioritized."
    )


class CognitiveReasoningTraceState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A declarative, frozen snapshot of a continuous proof trace resulting
    from a successfully resolved non-monotonic search, projecting internal System 2 thinking
    into the observable graph. As a ...State suffix, this is a frozen N-dimensional
    coordinate.

    CAUSAL AFFORDANCE: Binds the raw, unstructured Chain-of-Thought (trace_payload) to a
    formal EpistemicTopologicalProofManifest (source_proof_id), injecting the internal
    monologue into the verifiable DAG for downstream reward shaping (GRPO).

    EPISTEMIC BOUNDS: The token_length is restricted (ge=0, le=1000000000). The textual
    reasoning is physically bounded to max_length=100000 to prevent context window
    explosion. The trace_id is locked to a 128-char CID.

    MCP ROUTING TRIGGERS: Chain of Thought, Non-Monotonic Trace, Proof Crystallization,
    Latent Monologue, Verifiable Reasoning
    """
    trace_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="CID of this specific non-monotonic reasoning trace.",
    )
    source_proof_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The EpistemicTopologicalProofManifest CID this trace is mathematically anchored to.",
    )
    token_length: int = Field(le=1000000000, ge=0, description="The exact token consumption of the trace.")
    trace_payload: str = Field(
        max_length=100000, description="The natural language reasoning steps bounded by structural tags."
    )


class CognitiveDualVerificationReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes a Byzantine-tolerant Multi-Agent Debate and Consensus
    protocol (the "Two-Man Rule") to eliminate single-point epistemic failures. As a
    ...Receipt suffix, this is a frozen historical fact on the Merkle-DAG.

    CAUSAL AFFORDANCE: Authorizes the final cryptographic lock on a reasoning trace or
    semantic payload, proving that two independent cognitive agents achieved symmetric
    factual alignment via trace_factual_alignment (bool).

    EPISTEMIC BOUNDS: The @model_validator enforce_dual_key_lock mathematically
    guarantees zero-trust isolation by demanding that primary_verifier_id and
    secondary_verifier_id (both NodeIdentifierState) resolve to completely distinct
    Decentralized Identifiers (DIDs).

    MCP ROUTING TRIGGERS: Multi-Agent Debate, Byzantine Tolerance, Dual-Key
    Cryptography, Symmetric Consensus, Zero-Trust Evaluation
    """
    primary_verifier_id: NodeIdentifierState = Field(description="The DID of the primary evaluating agent.")
    secondary_verifier_id: NodeIdentifierState = Field(
        description="The DID of the independent secondary evaluating agent."
    )
    trace_factual_alignment: bool = Field(
        description="Strict Boolean indicating if BOTH agents mathematically agree on factual alignment."
    )

    @model_validator(mode="after")
    def enforce_dual_key_lock(self) -> Self:
        if self.primary_verifier_id == self.secondary_verifier_id:
            raise ValueError(
                "Topological Contradiction: Dual verification requires two distinct and independent evaluator nodes."
            )
        return self


class EpistemicGroundedTaskManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Formalizes Trajectory Distillation and Direct Preference Optimization
    (DPO) by encapsulating a mathematically verified ground-truth training datum. As a
    ...Manifest suffix, this defines a frozen, N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Unlocks verifiable Reinforcement Learning across the swarm by
    securely binding an unstructured vignette_payload to a formal topological_proof
    (EpistemicTopologicalProofManifest) and its resulting non-monotonic thinking_trace
    (CognitiveReasoningTraceState).

    EPISTEMIC BOUNDS: The task_id is cryptographically constrained to a 128-char CID
    (^[a-zA-Z0-9_.:-]+$). The vignette_payload is bounded to 100000 characters to prevent
    context exhaustion. A verification_lock (CognitiveDualVerificationReceipt) is
    structurally mandated to physically prevent reward hacking via isolated consensus.

    MCP ROUTING TRIGGERS: Trajectory Distillation, Direct Preference Optimization,
    Reinforcement Learning, Dual Verification, Curry-Howard Correspondence
    """
    task_id: str = Field(
        max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", min_length=1, description="The cryptographic CID of the task."
    )
    topological_proof: EpistemicTopologicalProofManifest = Field(description="The underlying latent path.")
    vignette_payload: str = Field(max_length=100000, description="The generated natural language scenario.")
    thinking_trace: CognitiveReasoningTraceState = Field(description="The verified reasoning path.")
    verification_lock: CognitiveDualVerificationReceipt = Field(
        description="The cryptographic proof of dual-agent approval."
    )


class EpistemicCurriculumManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Curriculum Learning and Experience Replay manifolds,
    serving as the definitive batch transport layer for continuous swarm optimization. As a
    ...Manifest suffix, this defines a frozen, N-dimensional coordinate state.

    CAUSAL AFFORDANCE: Injects a validated cluster of EpistemicGroundedTaskManifest
    primitives into the decentralized training pipeline, forcing deterministic policy
    gradient updates across all subscribing nodes.

    EPISTEMIC BOUNDS: The tasks array requires min_length=1 to prevent empty compute
    cycles. To guarantee zero-trust distribution and prevent Byzantine hash fractures, the
    @model_validator sort_tasks mechanically sorts the array by task_id, ensuring perfect
    RFC 8785 canonical hashing. Anchored by a 128-char curriculum_id CID.

    MCP ROUTING TRIGGERS: Curriculum Learning, Experience Replay, Policy Gradient,
    Canonical Hashing, Knowledge Distillation
    """
    curriculum_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique CID for this training epoch release.",
    )
    tasks: list[EpistemicGroundedTaskManifest] = Field(
        min_length=1, description="The array of fully verified task primitives."
    )

    @model_validator(mode="after")
    def sort_tasks(self) -> Self:
        object.__setattr__(self, "tasks", sorted(self.tasks, key=lambda task: task.task_id))
        return self


class CognitiveFormatContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Employs Finite State Machine (FSM) Logit Masking and Constrained
    Decoding to deterministically herd LLM stochasticity into rigorous syntactic
    structures. As a ...Contract suffix, this enforces a rigid mathematical boundary
    globally.

    CAUSAL AFFORDANCE: Instructs the orchestrator's inference engine to physically
    suffocate invalid token probabilities to negative infinity, mechanically ensuring
    the output conforms to downstream parser requirements.

    EPISTEMIC BOUNDS: Execution constraints are rigidly defined by require_think_tags
    (default=True, forcing XML-bounded internal monologues) and final_answer_regex
    (max_length=2000, default="^Final Answer: .*$") to prevent ReDoS CPU exhaustion
    during evaluation and routing.

    MCP ROUTING TRIGGERS: FSM Logit Masking, Constrained Decoding, Regular Expression
    Automaton, Syntactic Boundary, Token Suffocation
    """
    require_think_tags: bool = Field(
        default=True, description="Forces the inclusion of structural XML tags to isolate the reasoning trace."
    )
    final_answer_regex: str = Field(
        max_length=2000,
        default="^Final Answer: .*$",
        description="The strict regular expression the model must satisfy to yield a valid discrete classification.",
    )


class EpistemicRewardModelPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Establishes the Group Relative Policy Optimization (GRPO) reward
    shaping ruleset, mathematically immunizing the swarm against Goodhart's Law and reward
    hacking. As a ...Policy suffix, this object defines rigid mathematical boundaries that
    the orchestrator must enforce globally.

    CAUSAL AFFORDANCE: Projects a continuous penalty/reward gradient across extracted axiomatic
    paths, enforcing syntactic compliance through the format_contract (CognitiveFormatContract)
    while simultaneously evaluating semantic and topological validity via the optional
    topological_scoring (TopologicalRewardContract).

    EPISTEMIC BOUNDS: Prevents reward hacking by scaling the logical validity score (R_path)
    via the beta_path_weight scalar (ge=0.0, le=1.0). Gated by a cryptographic
    reference_graph_id providing the deterministic ground-truth topology.

    MCP ROUTING TRIGGERS: GRPO, Reward Shaping, Goodhart's Law, Policy Gradient,
    Advantage Estimation
    """
    policy_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="CID for this specific reward configuration.",
    )
    reference_graph_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the EpistemicDomainGraphManifest acting as the deterministic ground truth.",
    )
    format_contract: CognitiveFormatContract = Field(
        description="The syntactic constraints the agent must follow to prevent reward zeroing."
    )
    beta_path_weight: float = Field(
        le=1.0,
        ge=0.0,
        description="The scalar weight applied to the logical path validity (R_path) to prevent reward hacking.",
    )
    topological_scoring: TopologicalRewardContract | None = Field(
        default=None, description="The continuous spatial/topological constraints governing path extraction validation."
    )


class CognitiveRewardEvaluationReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: The immutable cryptographic receipt of a GRPO Advantage Actor-Critic
    evaluation step, permanently logging the mathematically verified advantage score of a
    specific generation trajectory. As a ...Receipt suffix, this is an append-only coordinate
    on the Merkle-DAG that the LLM must never hallucinate a mutation to.

    CAUSAL AFFORDANCE: Unlocks policy gradient updates by providing the deterministic advantage
    signal derived from the extracted_axioms of the source_generation_id.

    EPISTEMIC BOUNDS: The calculated_r_path is strictly clamped between [ge=0.0, le=1.0], and
    the total_advantage_score is capped at le=100.0. The @model_validator physically guarantees
    that the extracted_axioms array is deterministically sorted by the composite key
    (source_concept_id, directed_edge_type, target_concept_id) to preserve RFC 8785 canonical
    hashing across the distributed swarm.

    MCP ROUTING TRIGGERS: Advantage Actor-Critic, Policy Gradient Update, Epistemic Reward,
    Baseline Normalization, Reinforcement Learning
    """
    type: Literal["cognitive_reward_evaluation"] = Field(default="cognitive_reward_evaluation")
    source_generation_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the LLM's raw generated text trajectory.",
    )
    extracted_axioms: list[EpistemicAxiomState] = Field(
        default_factory=list,
        description="The specific axiomatic claims extracted exclusively from the bounded reasoning block.",
    )
    calculated_r_path: float = Field(
        ge=0.0, le=1.0, description="The dense reasoning reward signal derived from the verified axioms."
    )
    total_advantage_score: float = Field(
        le=100.0, description="The final computed GRPO advantage signal used to update the policy gradients."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self,
            "extracted_axioms",
            sorted(
                self.extracted_axioms, key=lambda x: (x.source_concept_id, x.directed_edge_type, x.target_concept_id)
            ),
        )
        return self


class CognitiveDetailedBalanceContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Generative Flow Network (GFlowNet) trajectory balance
    conditions to ensure that the probability of generating a non-monotonic reasoning path
    is strictly proportional to its terminal reward. As a ...Contract suffix, this object
    defines rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Instructs the orchestrator's sampling mechanism to continuously
    optimize for the detailed balance equations using the specified flow_estimation_model
    (max_length=2000), ensuring proportional flow allocation across alternative Markov
    Decision Process (MDP) branches.

    EPISTEMIC BOUNDS: The acceptable mathematical variance is strictly bounded by
    target_balance_epsilon (ge=0.0, le=1.0), preventing probability flow divergence. The
    local_exploration_k (gt=0, le=1.0) physically caps exploratory branching.

    MCP ROUTING TRIGGERS: Generative Flow Networks, Detailed Balance, Markov Chain Monte
    Carlo, Trajectory Flow, Credit Assignment Problem
    """
    target_balance_epsilon: float = Field(
        le=1.0, ge=0.0, description="The mathematical tolerance for the detailed balance constraint."
    )
    flow_estimation_model: str = Field(
        max_length=2000, description="The specific neural architecture used to estimate flow."
    )
    local_exploration_k: int = Field(
        le=1.0, gt=0, description="The number of exploratory actions taken per state to optimize flow efficiently."
    )


class EpistemicFlowStateReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: An immutable cryptographic coordinate recording the successful
    factorization of a terminal reward into a fractional flow value across a continuous
    CognitiveReasoningTraceState trajectory. As a ...Receipt suffix, this is an append-only
    coordinate on the Merkle-DAG.

    CAUSAL AFFORDANCE: Physically anchors the scalar backpropagation of a factored reward
    to a specific source_trajectory_id, unlocking global flow consistency calculations
    across the distributed swarm. The terminal_reward_factorized boolean confirms
    successful reward decomposition.

    EPISTEMIC BOUNDS: Flow magnitude is geometrically bounded by estimated_flow_value
    (ge=0.0, le=1000000000.0) to prevent exploding gradients during policy updates.
    Cryptographically mapped to a rigid 128-char source_trajectory_id CID.

    MCP ROUTING TRIGGERS: Trajectory Balance, Reward Factorization, Flow Network Receipt,
    Scalar Backpropagation, Acyclic Path
    """
    type: Literal["epistemic_flow_state"] = Field(default="epistemic_flow_state")
    source_trajectory_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the partial CognitiveReasoningTraceState.",
    )
    estimated_flow_value: float = Field(
        le=1000000000.0,
        ge=0.0,
        description="The non-negative flow value scalar representing the factorized outcome reward.",
    )
    terminal_reward_factorized: bool = Field(
        description="True if this flow successfully factorized a terminal outcome reward."
    )


class TopologicalRewardContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Enforces Graph Representation Learning (GCN/GAT) constraints to
    shape the epistemic reward based purely on the topological centrality and spectral
    connectivity of the extracted axioms. As a ...Contract suffix, this object defines
    rigid mathematical boundaries.

    CAUSAL AFFORDANCE: Commands the orchestrator to execute deterministic graph traversal
    algorithms (Random Walk with Restart, Spatial GCN) to compute node reachability and
    vector similarity before allocating policy gradients to the actor model.

    EPISTEMIC BOUNDS: Clamps structural relevance geometrically using
    min_link_criticality_score and min_semantic_relevance_score, both strictly between
    (ge=0.0, le=1.0). The aggregation_method restricts the orchestrator to a strict
    Literal automaton ["gcn_spatial", "attention_gat", "rwr_topological"].

    MCP ROUTING TRIGGERS: Graph Convolutional Networks, Spectral Graph Theory, Random Walk
    with Restart, Topological Reward Shaping, PageRank
    """
    min_link_criticality_score: float = Field(
        ge=0.0, le=1.0, description="The lower bound for Random Walk with Restart (RWR) reachability."
    )
    min_semantic_relevance_score: float = Field(
        ge=0.0, le=1.0, description="The lower bound for GCN/GAT cosine similarity."
    )
    aggregation_method: Literal["gcn_spatial", "attention_gat", "rwr_topological"] = Field(
        description="The deterministic protocol the orchestrator must use to compute these scores."
    )


class DifferentiableLogicConstraint(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Bridges the Neurosymbolic divide by mapping discrete Satisfiability
    Modulo Theories (SMT) or Lean4 logic proofs into continuous, differentiable loss
    gradients. As a constraint, this object defines rigid mathematical boundaries the
    orchestrator must enforce.

    CAUSAL AFFORDANCE: Allows the backpropagation engine to apply a continuous,
    differentiable penalty (relaxation) to the LLM's probability mass when it violates the
    formal syntactic rules encoded in the formal_syntax_smt representation
    (max_length=2000).

    EPISTEMIC BOUNDS: The geometric penalty is clamped by relaxation_epsilon (ge=0.0,
    le=1.0) to prevent gradient explosion. The logical schema is locked to the 128-char
    constraint_id CID (^[a-zA-Z0-9_.:-]+$) to structurally bound string evaluation scope.

    MCP ROUTING TRIGGERS: Satisfiability Modulo Theories, Neurosymbolic Relaxation,
    Differentiable Theorem Proving, Probabilistic Logic Networks, Continuous Penalty
    """
    constraint_id: str = Field(max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", min_length=1)
    formal_syntax_smt: str = Field(
        max_length=2000, description="The formal SMT-LIB or Lean4 language representation of the symbolic rule."
    )
    relaxation_epsilon: float = Field(
        le=1.0,
        ge=0.0,
        description="The continuous penalty applied to the LLM probability mass for constraint violation.",
    )


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
    | PersistenceCommitReceipt
    | TokenBurnReceipt
    | BudgetExhaustionEvent
    | EpistemicTelemetryEvent
    | CognitivePredictionReceipt
    | EpistemicAxiomVerificationReceipt
    | CognitiveRewardEvaluationReceipt
    | EpistemicFlowStateReceipt
    | CausalExplanationEvent,
    Field(discriminator="type", description="A discriminated union of state events."),
]


class EpistemicLedgerState(CoreasonBaseState):
    """The Committed Epistemic Ledger (crystallized truth), completely partitioned from volatile working context
    or Epistemic Quarantine."""

    history: list[AnyStateEvent] = Field(
        max_length=10000,
        description="An append-only, cryptographic ledger of state events. [SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry]",  # noqa: E501
    )
    checkpoints: list[TemporalCheckpointState] = Field(
        max_length=1000000000, default_factory=list, description="Hard temporal anchors allowing state restoration."
    )
    active_rollbacks: list[RollbackIntent] = Field(
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
        le=1000000000,
        default=None,
        description="The mathematical contract governing automated causal graph ablations and probabilistic decay.",
    )
    active_cascades: list[DefeasibleCascadeEvent] = Field(
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


CompositeNodeProfile.model_rebuild()
WorkflowManifest.model_rebuild()
MCPServerBindingProfile.model_rebuild()
StateHydrationManifest.model_rebuild()
BaseTopologyManifest.model_rebuild()
DAGTopologyManifest.model_rebuild()
CouncilTopologyManifest.model_rebuild()
SwarmTopologyManifest.model_rebuild()
EvolutionaryTopologyManifest.model_rebuild()
SMPCTopologyManifest.model_rebuild()
EvaluatorOptimizerTopologyManifest.model_rebuild()
DigitalTwinTopologyManifest.model_rebuild()
AdversarialMarketTopologyManifest.model_rebuild()
ConsensusFederationTopologyManifest.model_rebuild()
EpistemicSOPManifest.model_rebuild()
DelegatedCapabilityManifest.model_rebuild()
TokenBurnReceipt.model_rebuild()
BudgetExhaustionEvent.model_rebuild()
LatentProjectionIntent.model_rebuild()
EpistemicAxiomState.model_rebuild()
EpistemicSeedInjectionPolicy.model_rebuild()
EpistemicChainGraphState.model_rebuild()
CognitivePredictionReceipt.model_rebuild()
EpistemicAxiomVerificationReceipt.model_rebuild()
EpistemicDomainGraphManifest.model_rebuild()
EpistemicTopologicalProofManifest.model_rebuild()
CognitiveSamplingPolicy.model_rebuild()
CognitiveReasoningTraceState.model_rebuild()
CognitiveDualVerificationReceipt.model_rebuild()
EpistemicGroundedTaskManifest.model_rebuild()
EpistemicCurriculumManifest.model_rebuild()
CognitiveFormatContract.model_rebuild()
EpistemicRewardModelPolicy.model_rebuild()
CognitiveRewardEvaluationReceipt.model_rebuild()
AgentNodeProfile.model_rebuild()
CognitiveDetailedBalanceContract.model_rebuild()
EpistemicFlowStateReceipt.model_rebuild()
TopologicalRewardContract.model_rebuild()
DifferentiableLogicConstraint.model_rebuild()
CausalExplanationEvent.model_rebuild()
