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

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

# The Extension Namespace Boundary
type DomainExtensionString = Annotated[str, StringConstraints(pattern="^ext:[a-zA-Z0-9_.-]+$", max_length=128)]


type CoreRoutingIntent = Literal[
    "informational_inform", "directive_instruct", "semantic_discovery", "taxonomic_restructure"
]
CORE_ROUTING_SEMANTICS = {
    "informational_inform": "ISO 24617-2: Standard data projection to the user. No state mutation.",
    "directive_instruct": "ISO 24617-2: Agent commanding a sub-system to execute a kinetic action.",
    "semantic_discovery": "Schema.org DiscoverAction: Triggering RAG or Tool discovery.",
    "taxonomic_restructure": "Dynamic UI regrouping across the Hollow Data Plane.",
}

type CoreEBNFConstruct = Literal["terminal", "non_terminal", "production_rule", "quantifier"]
CORE_EBNF_SEMANTICS = {
    "terminal": "W3C EBNF: A leaf node character or string that cannot be broken down further.",
    "non_terminal": "W3C EBNF: A named reference to another structural grammar rule.",
    "production_rule": "W3C EBNF: The declaration mapping a non-terminal to its expansion sequence.",
    "quantifier": "W3C EBNF: An operator (+, *, ?) defining the repetition variance of a token.",
}

type CoreTokenMergeMetric = Literal["cosine_similarity", "euclidean_distance", "manhattan_distance"]
CORE_TOKEN_MERGE_SEMANTICS = {
    "cosine_similarity": "Information-theoretic compression comparing the geometric angle between embedding vectors.",
    "euclidean_distance": "Spatial distance calculation measuring direct point-to-point magnitude.",
    "manhattan_distance": "L1 norm calculating grid-based traversal distance.",
}

type CoreTokenMatchingAlgorithm = Literal["bipartite_soft_matching", "size_distinctive_matching"]
CORE_TOKEN_MATCHING_SEMANTICS = {
    "bipartite_soft_matching": "Algorithm partitioning tokens into two sets and merging the most similar edges.",
    "size_distinctive_matching": "Algorithm prioritizing the merging of small token clusters into larger structural anchors.",  # noqa: E501
}

type CoreXAIExplanationType = Literal["feature_attribution", "counterfactual", "contrastive"]
CORE_XAI_EXPLANATION_SEMANTICS = {
    "feature_attribution": "XAI: Assigning specific causal weight to a recognized monosemantic concept.",
    "counterfactual": "XAI: Proving the routing decision mathematically changes if a specific concept is toggled False.",  # noqa: E501
    "contrastive": "XAI: Comparing why Route A was chosen over Route B based on strict concept activations.",
}

type CoreEntropyMetric = Literal["shannon_entropy", "semantic_entropy", "predictive_variance"]
CORE_ENTROPY_METRIC_SEMANTICS = {
    "shannon_entropy": "Information Theory: The strict mathematical baseline measure of unpredictability.",
    "semantic_entropy": "Uncertainty Quantification: Entropy calculated over equivalence classes of meaning rather than raw tokens.",  # noqa: E501
    "predictive_variance": "Statistical bounds of token probability distributions during sequence generation.",
}

type CoreComputeStrategyTier = Literal["speed_single_pass", "precision_token_class", "reasoning_ensemble"]
CORE_COMPUTE_STRATEGY_SEMANTICS = {
    "speed_single_pass": (
        "Hardware execution utilizing lightweight bidirectional encoders (e.g., GLiNER) for high-throughput."
    ),
    "precision_token_class": "Hardware execution utilizing strict token-by-token classification models (e.g., NuNER).",
    "reasoning_ensemble": (
        "Test-time compute executing an Actor-Critic loop using an LLM to propose and prune subgraphs."
    ),
}

type CoreClinicalAssertion = Literal["present", "absent", "possible", "history", "family"]
CORE_CLINICAL_ASSERTION_SEMANTICS = {
    "present": "Non-monotonic boundary indicating a baseline factual or actively observed state.",
    "absent": (
        "Non-monotonic boundary indicating a negation. Mathematically triggers an "
        "'undercutter' edge in argumentation graphs."
    ),
    "possible": "Non-monotonic boundary indicating epistemic speculation or high uncertainty.",
    "history": "Episodic boundary referencing past resolved states.",
    "family": "Genetic or external attribution boundary.",
}

type CoreOBORelationEdge = Literal["is_a", "part_of", "has_part"]
CORE_OBO_RELATION_SEMANTICS = {
    "is_a": "OBO Foundry RO: A taxonomic subsumption relationship between classes.",
    "part_of": "OBO Foundry RO: A structural mereological relationship indicating component inclusion.",
    "has_part": "OBO Foundry RO: The inverse mereological relationship of part_of.",
}

type CoreExtractionOntologyTarget = Literal["obo_foundry", "rxnorm", "snomed_ct", "mesh"]
CORE_EXTRACTION_ONTOLOGY_SEMANTICS = {
    "obo_foundry": "Open Biological and Biomedical Ontology standard.",
    "rxnorm": "Normalized naming system for generic and branded drugs.",
    "snomed_ct": "Systematized Nomenclature of Medicine - Clinical Terms.",
    "mesh": "Medical Subject Headings controlled vocabulary.",
}

type CoreCognitiveMemoryDomain = Literal["working", "episodic", "semantic"]
CORE_COGNITIVE_MEMORY_SEMANTICS = {
    "working": "ACT-R/SOAR Architecture: Ephemeral context, active session state, and scratchpads.",
    "episodic": "ACT-R/SOAR Architecture: Historical logs, telemetry, and time-series events.",
    "semantic": "ACT-R/SOAR Architecture: Factual axioms, ontology ledgers, and generalized knowledge.",
}

type CoreDisfluencyRole = Literal["reparandum", "interregnum", "repair"]
CORE_DISFLUENCY_SEMANTICS = {
    "reparandum": "Switchboard Corpus Standard: The aborted thought or string of error tokens to be dropped.",
    "interregnum": "Switchboard Corpus Standard: The phonetic edit or pause signal (e.g., 'uh', 'wait').",
    "repair": "Switchboard Corpus Standard: The newly injected, corrected context.",
}

type CoreCacheEviction = Literal["lru", "lfu", "fifo"]
CORE_CACHE_EVICTION_SEMANTICS = {
    "lru": "Hardware memory algorithm discarding the Least Recently Used discrete pages.",
    "lfu": "Hardware memory algorithm discarding the Least Frequently Used discrete pages.",
    "fifo": "Hardware memory algorithm operating a strict chronological queue.",
}

type CoreDefeasibleEdgeType = Literal["rebuttal", "undercut", "undermine"]
CORE_DEFEASIBLE_EDGE_SEMANTICS = {
    "rebuttal": (
        "Dung's Argumentation: A symmetric attack where a new node claims the exact opposite of an existing node."
    ),
    "undercut": (
        "Dung's Argumentation: An attack on the reasoning/inference rule connecting two nodes, "
        "rather than the nodes themselves."
    ),
    "undermine": "Dung's Argumentation: A direct attack on the core premise or foundational warrant of a claim.",
}

type CoreIEEEAnomalyClass = Literal["logic_flaw", "data_fault", "interface_defect", "computation_error"]
CORE_IEEE_ANOMALY_SEMANTICS = {
    "logic_flaw": "IEEE 1044-2009: A semantic reasoning failure or workflow DAG violation.",
    "data_fault": "IEEE 1044-2009: An invalid data type, hallucinated key, or schema structure violation.",
    "interface_defect": "IEEE 1044-2009: A broken schema projection, routing failure, or API contract mismatch.",
    "computation_error": "IEEE 1044-2009: A mathematical limit breach, division by zero, or execution timeout.",
}

type CoreSMTSolverOutcome = Literal["sat", "unsat", "unknown"]
CORE_SMT_SOLVER_SEMANTICS = {
    "sat": "SMT-LIB Standard: The theorem prover mathematically satisfied the constraint.",
    "unsat": "SMT-LIB Standard: The theorem prover proved the constraint is actively violated.",
    "unknown": "SMT-LIB Standard: The solver timed out or lacked sufficient compute to prove satisfiability.",
}

type ValidRoutingIntent = CoreRoutingIntent | DomainExtensionString
type EBNFConstruct = CoreEBNFConstruct | DomainExtensionString
type TokenMergeMetric = CoreTokenMergeMetric | DomainExtensionString
type TokenMatchingAlgorithm = CoreTokenMatchingAlgorithm | DomainExtensionString
type XAIExplanationType = CoreXAIExplanationType | DomainExtensionString
type EntropyMetric = CoreEntropyMetric | DomainExtensionString
type ComputeStrategyTier = CoreComputeStrategyTier | DomainExtensionString
type ClinicalAssertionState = CoreClinicalAssertion | DomainExtensionString
type OBORelationEdge = CoreOBORelationEdge | DomainExtensionString
type ExtractionOntologyTarget = CoreExtractionOntologyTarget | DomainExtensionString
type CognitiveMemoryDomain = CoreCognitiveMemoryDomain | DomainExtensionString
type DisfluencyRole = CoreDisfluencyRole | DomainExtensionString
type CacheEviction = CoreCacheEviction | DomainExtensionString
type DefeasibleEdgeType = CoreDefeasibleEdgeType | DomainExtensionString
type IEEEAnomalyClass = CoreIEEEAnomalyClass | DomainExtensionString
type SMTSolverOutcome = CoreSMTSolverOutcome | DomainExtensionString

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
    Base class for all domain models in the Coreason Manifest.

    This model guarantees deterministic serialization for Tamper-Evident Hash Chains and
    Merkle-Tree Attestations, preventing epistemic contamination.

    Enforces:
    1. Immutability (frozen=True) - Essential for distributed state consistency.
    2. Strict validation (strict=True) - No silent coercion.
    3. Forbidden extra fields (extra='forbid') - Schema strictness.
    4. Deterministic serialization - Keys are sorted for hash consistency.
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

    @model_validator(mode="after")
    def validate_global_domain_extensions(self, info: ValidationInfo) -> Self:
        """
        Global mathematical boundary: Recursively prove any 'ext:' string exists
        in the active client's dynamically loaded vocabulary.
        """
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())

        def _walk_and_validate(obj: Any) -> None:
            if isinstance(obj, str):
                if obj.startswith("ext:") and obj not in allowed_exts:
                    raise ValueError(f"Unauthorized domain extension string detected: '{obj}'")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    _walk_and_validate(k)
                    _walk_and_validate(v)
            elif isinstance(obj, (list, tuple, set)):
                for item in obj:
                    _walk_and_validate(item)

        _walk_and_validate(self.__dict__)
        return self


class SpatialBoundingBoxProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SpatialBoundingBoxProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on x_min
    (ge=0.0, le=1.0), y_min (ge=0.0, le=1.0), x_max (ge=0.0, le=1.0), y_max (ge=0.0, le=1.0); constrained by
    @model_validator hooks (validate_geometry) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: DynamicLayoutManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    layout_tstring (max_length=2000); enforced via @field_validator structural bounds (validate_tstring). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: ExecutionSLA is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_execution_time_ms (le=86400000, gt=0), max_compute_footprint_mb (le=1000000000, gt=0). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: FacetMatrixProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on row_field
    (max_length=2000), column_field (max_length=2000). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    row_field: str | None = Field(
        max_length=2000, default=None, description="The dataset field used to split the chart into rows."
    )
    column_field: str | None = Field(
        max_length=2000, default=None, description="The dataset field used to split the chart into columns."
    )


class SpatialCoordinateProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SpatialCoordinateProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on x (ge=0.0,
    le=1.0), y (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    x: float = Field(ge=0.0, le=1.0, description="The normalized X-axis coordinate (0.0 = left, 1.0 = right).")
    y: float = Field(ge=0.0, le=1.0, description="The normalized Y-axis coordinate (0.0 = top, 1.0 = bottom).")


class ComputeRateContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ComputeRateContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    cost_per_million_input_tokens (le=1000000000.0), cost_per_million_output_tokens (le=1000000000.0),
    magnitude_unit (max_length=2000). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    cost_per_million_input_tokens: float = Field(
        le=1000000000.0, description="The cost per 1 million input tokens provided to the model."
    )
    cost_per_million_output_tokens: float = Field(
        le=1000000000.0, description="The cost per 1 million output tokens generated by the model."
    )
    magnitude_unit: str = Field(max_length=2000, description="The magnitude unit of the associated costs.")


class ConceptBottleneckPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ConceptBottleneckPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    required_concept_vector (min_length=1), bottleneck_temperature (ge=0.0, le=0.0); constrained by
    @model_validator hooks (sort_concept_vector) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    required_concept_vector: dict[Annotated[str, StringConstraints(max_length=255)], bool] = Field(
        min_length=1,
        description="A strictly defined dictionary of boolean dimensions representing required monosemantic concepts.",
    )
    bottleneck_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=0.0,
        description="Mathematically forced to 0.0 to ensure deterministic, zero-variance classification.",
    )
    explanation_modality: XAIExplanationType = Field(
        description="The formal XAI methodology used to justify the resulting spatial route."
    )

    @model_validator(mode="after")
    def sort_concept_vector(self) -> Self:
        object.__setattr__(
            self,
            "required_concept_vector",
            {k: self.required_concept_vector[k] for k in sorted(self.required_concept_vector.keys())},
        )
        return self


class ScalePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ScalePolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on domain_min (le=1000000000.0), domain_max (le=1000000000.0). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: VisualEncodingProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: channel; intrinsic Pydantic limits on field (max_length=2000). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    channel: Literal["x", "y", "color", "size", "opacity", "shape", "text"] = Field(
        description="The visual channel the metric is mapped to."
    )
    field: str = Field(max_length=2000, description="The exact column or field name from the semantic series.")
    scale: ScalePolicy | None = Field(default=None, description="Optional scale override for this specific channel.")


class SideEffectProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SideEffectProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    is_idempotent: bool = Field(
        description="True if the tool can be safely retried multiple times without altering state beyond the first call."  # noqa: E501
    )
    mutates_state: bool = Field(description="True if the tool performs write operations or side-effects.")


class VerifiableEntropyReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: VerifiableEntropyReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on vrf_proof
    (min_length=10), public_key (min_length=10), seed_hash (max_length=128, pattern='^[a-f0-9]{64}$',
    min_length=10). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: HardwareEnclaveReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: enclave_type; intrinsic Pydantic limits on enclave_type (le=1000000000), platform_measurement_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), hardware_signature_blob (max_length=8192). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: LatentSmoothingProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: decay_function; intrinsic Pydantic limits on transition_window_tokens (le=1000000000, gt=0),
    decay_rate_param (le=1.0). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: LogitSteganographyContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    verification_public_key_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), prf_seed_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), watermark_strength_delta (le=1.0, gt=0.0),
    target_bits_per_token (le=1000000000.0, gt=0.0), context_history_window (le=1000000000, ge=0). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: ComputeEngineProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on model_name
    (max_length=2000), provider (max_length=2000), context_window_size (le=1000000000), capabilities
    (max_length=1000000000); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: PermissionBoundaryPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: PostQuantumSignatureReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: pq_algorithm; intrinsic Pydantic limits on public_key_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), pq_signature_blob (max_length=100000). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: RoutingFrontierPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: tradeoff_preference; intrinsic Pydantic limits on max_latency_ms (le=86400000, gt=0),
    max_cost_magnitude_per_token (le=1000000000, gt=0), min_capability_score (ge=0.0, le=1.0),
    max_carbon_intensity_gco2eq_kwh (le=10000.0, ge=0.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: SaeFeatureActivationState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on feature_index
    (le=1000000000, ge=0), activation_magnitude (le=1000000000), interpretability_label (max_length=2000). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: ActivationSteeringContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: vector_modality; intrinsic Pydantic limits on steering_vector_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'), injection_layers (min_length=1), scaling_factor (le=100.0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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


class DeterministicExtractionContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: The strict symbolic boundary forcing the probabilistic VLM output into a deterministic string
    or schema via hard execution of Regex, XPath, or CSS Selectors.
    """

    contract_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    extraction_type: Literal["regex", "xpath", "css_selector", "json_pointer"] = Field(
        description="The exact deterministic engine to use."
    )
    query_string: str = Field(max_length=2000, description="The actual Regex pattern or DOM selector.")
    strict_type_coercion: Literal["string", "integer", "float", "boolean", "date"] = Field(
        description="The required final primitive type post-extraction."
    )
    fallback_value: JsonPrimitiveState | None = Field(
        default=None, description="Optional default if the query yields a null set."
    )

    @field_validator("fallback_value", mode="before")
    @classmethod
    def validate_payload(cls, v: Any) -> Any:
        if v is None:
            return None
        return _validate_payload_bounds(v)


class SemanticSlicingPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SemanticSlicingPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    permitted_classification_tiers (min_length=1), context_window_token_ceiling (le=2000000, gt=0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    spatial_crop_boundary: SpatialBoundingBoxProfile | None = Field(
        default=None,
        description="The strict Euclidean geometric coordinate bounds. The orchestrator must physically crop the visual tensor to this exact region before VLM evaluation to prevent attention dilution.",  # noqa: E501
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
    AGENT INSTRUCTION: CognitiveRoutingContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on dynamic_top_k
    (le=1000000000, ge=1), routing_temperature (le=1000000000.0, ge=0.0), expert_logit_biases (le=1000000000.0).
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: CognitiveStateProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on urgency_index
    (ge=0.0, le=1.0), caution_index (ge=0.0, le=1.0), divergence_tolerance (ge=0.0, le=1.0). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CognitiveUncertaintyProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    decomposition_entropy_threshold (ge=0.0, le=1000000000.0), aleatoric_entropy (ge=0.0, le=1000000000.0),
    epistemic_uncertainty (ge=0.0, le=1000000000.0), semantic_consistency_score (ge=0.0, le=1.0),
    theory_of_mind_divergence (ge=0.0, le=1000000000.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    decomposition_entropy_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1000000000.0,
        description=(
            "The exact epistemic entropy boundary (in bits/nats) that, when breached, mathematically "
            "mandates the orchestrator to splinter the monolithic prompt into a QueryDecompositionManifest."
        ),
    )
    aleatoric_entropy: float = Field(
        ge=0.0,
        le=1000000000.0,
        description="Irreducible ambiguity detected in the observational fields (P(y|x)), measured in bits/nats.",
    )
    epistemic_uncertainty: float = Field(
        ge=0.0,
        le=1000000000.0,
        description="The causal gap demanding Do-Calculus Interventions (P(y|do(x))), measured in bits/nats.",
    )
    semantic_consistency_score: float = Field(
        ge=0.0, le=1.0, description="Counterfactual Geometries representing alternative timeline vectors."
    )
    requires_abductive_escalation: bool = Field(
        description="True if epistemic_uncertainty breaches the safety threshold, requiring structural mandate escalation."  # noqa: E501
    )
    theory_of_mind_divergence: float | None = Field(
        default=None,
        ge=0.0,
        le=1000000000.0,
        description="The mathematical KL divergence between the agent's internal belief distribution and the explicitly modeled TheoryOfMindSnapshot.",  # noqa: E501
    )


class ConstitutionalPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ConstitutionalPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: severity; intrinsic Pydantic limits on rule_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), description (max_length=2000), forbidden_intents (max_length=1000000000);
    constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: GradingCriterionProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on criterion_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), description (max_length=2000), weight (le=100.0,
    ge=0.0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: AdjudicationRubricProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on rubric_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), passing_threshold (ge=0.0, le=100.0);
    constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: PredictionMarketPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: staking_function; intrinsic Pydantic limits on min_liquidity_magnitude (le=1000000000, ge=0),
    convergence_delta_threshold (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: QuorumPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: state_validation_metric, byzantine_action; intrinsic Pydantic limits on max_tolerable_faults
    (le=1000000000, ge=0), min_quorum_size (le=1000000000, gt=0); constrained by @model_validator hooks
    (enforce_bft_math) for exact graph determinism. All field limits must be strictly validated at instantiation
    to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: ConsensusPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: strategy; intrinsic Pydantic limits on max_debate_rounds (le=1000000000); constrained by
    @model_validator hooks (validate_pbft_requirements) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: RedactionPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on rule_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), target_pattern (max_length=2000),
    target_regex_pattern (max_length=200), context_exclusion_zones (max_length=100), replacement_token
    (max_length=2000); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: SaeLatentPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: violation_action; intrinsic Pydantic limits on target_feature_index (le=1000000000, ge=0),
    monitored_layers (min_length=1), max_activation_threshold (le=1000000000.0, ge=0.0), clamp_value
    (le=1000000000.0), sae_dictionary_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'); constrained
    by @model_validator hooks (sort_arrays, validate_smooth_decay) for exact graph determinism. All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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


class BrowserFingerprintManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: BrowserFingerprintManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    user_agent_string (max_length=2000), ja3_tls_fingerprint (min_length=32, max_length=128,
    pattern='^[a-f0-9A-F]+$'), webgl_vendor_renderer (max_length=2000), canvas_noise_hash (min_length=1,
    max_length=128, pattern='^[a-f0-9]{64}$'). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    user_agent_string: str = Field(
        max_length=2000,
        description="The exact `navigator.userAgent`.",
    )
    ja3_tls_fingerprint: str = Field(
        min_length=32,
        max_length=128,
        pattern="^[a-f0-9A-F]+$",
        description="The MD5/SHA hash of the strict TLS Client Hello signature.",
    )
    webgl_vendor_renderer: str = Field(
        max_length=2000,
        description="The spoofed GPU renderer string.",
    )
    canvas_noise_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 seed used to deterministically poison Canvas rendering readouts.",
    )
    viewport_geometry: tuple[int, int] = Field(
        description="The $W \\times H$ bound for `window.innerWidth`/`innerHeight`."
    )
    has_touch_capability: bool = Field(
        description="Signals if `ontouchstart` should be mathematically present in the DOM."
    )


class SecureSubSessionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SecureSubSessionState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on session_id
    (min_length=1, pattern='^[a-zA-Z0-9_.:-]+$', max_length=255), allowed_vault_keys (max_length=100),
    max_ttl_seconds (ge=1, le=3600), description (max_length=2000); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    device_fingerprint: BrowserFingerprintManifest | None = Field(
        default=None,
        description="The cryptographic hardware and network stack identity bound to this authenticated session partition.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "allowed_vault_keys", sorted(self.allowed_vault_keys))
        return self


class DefeasibleCascadeEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: DefeasibleCascadeEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on cascade_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), root_falsified_event_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), propagated_decay_factor (ge=0.0, le=1.0), quarantined_event_ids
    (min_length=1); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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


class DefeasibleRebuttalContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: DefeasibleRebuttalContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    permitted_attack_edges (min_length=1), required_evidence_density (ge=0.0, le=1.0), max_quarantine_blast_radius
    (gt=0, le=1000000000); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    permitted_attack_edges: list[DefeasibleEdgeType] = Field(
        min_length=1, description="The formal argumentation edge types allowed to sever a prior operational intent."
    )
    required_evidence_density: float = Field(
        ge=0.0,
        le=1.0,
        description="The minimum confidence weight the new claim needs to successfully defeat the older node.",
    )
    max_quarantine_blast_radius: int = Field(
        gt=0,
        le=1000000000,
        description="Limits how many downstream API calls or semantic dependencies can be automatically severed by the logical cascade.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "permitted_attack_edges", sorted(self.permitted_attack_edges))
        return self


class MultimodalTokenAnchorState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: MultimodalTokenAnchorState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: block_type; intrinsic Pydantic limits on token_span_start (le=1000000000, ge=0), token_span_end
    (le=1000000000, ge=0); constrained by @model_validator hooks (validate_token_spans, sort_arrays) for exact
    graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    bounding_box: SpatialBoundingBoxProfile | None = Field(
        default=None,
        description="The strictly typed SpatialBoundingBoxProfile.",
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
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "visual_patch_hashes", sorted(self.visual_patch_hashes))
        return self


class RollbackIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: RollbackIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on request_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), target_event_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks (sort_invalidated_nodes) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: StateMutationIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on path
    (max_length=2000), from_path (max_length=2000). All field limits must be strictly validated at instantiation
    to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: StateDifferentialManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on diff_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), author_node_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), lamport_timestamp (le=1000000000, ge=0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: StateHydrationManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    epistemic_coordinate (max_length=2000), max_retained_tokens (le=1000000000, gt=0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism; enforced via @field_validator structural
    bounds (enforce_payload_topology). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: TemporalCheckpointState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on checkpoint_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), ledger_index (le=1000000000), state_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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


class MonteCarloTreeSearchPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: MonteCarloTreeSearchPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    exploration_constant_c (ge=0.0), max_rollout_depth (ge=1, le=1000000000), num_simulations (ge=1,
    le=1000000000), discount_factor_gamma (ge=0.0, le=1.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    exploration_constant_c: float = Field(
        ge=0.0, description="The UCB1 exploration weight bounding curiosity vs. exploitation."
    )
    max_rollout_depth: int = Field(
        ge=1, le=1000000000, description="The physical recursion limit for hallucinating future UI states."
    )
    num_simulations: int = Field(
        ge=1,
        le=1000000000,
        description="The number of search iterations required before collapsing the probability wave into a physical action.",  # noqa: E501
    )
    discount_factor_gamma: float = Field(
        ge=0.0, le=1.0, description="The mathematical discount applied to future expected rewards."
    )


class ThoughtBranchState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ThoughtBranchState is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on branch_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), parent_branch_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), latent_content_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'),
    prm_score (ge=0.0, le=1.0), simulated_action_hash (pattern='^[a-f0-9]{64}$'), expected_next_state_hash
    (pattern='^[a-f0-9]{64}$'), visit_count (ge=1). All field limits must be strictly validated at instantiation
    to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    simulated_action_hash: str | None = Field(
        default=None,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the proposed tool or kinematic action intent ($A_t$).",
    )
    expected_next_state_hash: str | None = Field(
        default=None,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 hash of the hallucinated/expected UI state ($S_{t+1}$) resulting from the simulated action.",  # noqa: E501
    )
    q_value_estimate: float | None = Field(
        default=None, description="The expected cumulative reward $Q(s,a)$ for this branch."
    )
    visit_count: int = Field(
        default=1,
        ge=1,
        description="The mathematical visit count $N(s,a)$ used for UCT exploration/exploitation balancing.",
    )


class LatentScratchpadReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: LatentScratchpadReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    root_state_hash (pattern='^[a-f0-9]{64}$'), trace_id (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$',
    min_length=1), resolution_branch_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    total_latent_tokens (le=1000000000, ge=0); constrained by @model_validator hooks
    (verify_referential_integrity, sort_arrays) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    root_state_hash: str | None = Field(
        default=None,
        pattern="^[a-f0-9]{64}$",
        description="The exact SHA-256 hash of the initial environment state (e.g., ViewportRasterState) from which the MCTS rollout originated.",  # noqa: E501
    )
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
    AGENT INSTRUCTION: EphemeralNamespacePartitionState is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: execution_runtime; intrinsic Pydantic limits on partition_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), authorized_bytecode_hashes (min_length=1), max_ttl_seconds
    (le=86400, gt=0), max_vram_mb (le=1000000000, gt=0); constrained by @model_validator hooks
    (validate_cryptographic_hashes, sort_arrays) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: ToolManifest is a declarative and frozen snapshot representing N-dimensional geometry at a
    specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on tool_name
    (max_length=2000), description (max_length=2000), input_schema (max_length=1000000000). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: BilateralSLA is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    receiving_tenant_id (min_length=1, pattern='^[a-zA-Z0-9_.:-]+$', max_length=255), liability_limit_magnitude
    (le=1000000000, ge=0), max_permitted_grid_carbon_intensity (le=10000.0, ge=0.0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: FederatedDiscoveryManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    broadcast_endpoints (max_length=1000000000), supported_ontologies (max_length=1000000000); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: ActiveInferenceContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on task_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), target_hypothesis_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), target_condition_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), selected_tool_name (max_length=2000), expected_information_gain (ge=0.0,
    le=1.0), execution_cost_budget_magnitude (le=1000000000, ge=0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: AdjudicationIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, timeout_action; intrinsic Pydantic limits on deadlocked_claims (max_length=86400000,
    min_length=2); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: AdjudicationReceipt is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on rubric_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), score (ge=0, le=100), reasoning
    (max_length=2000). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: AdversarialSimulationProfile is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: attack_vector; intrinsic Pydantic limits on simulation_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), target_node_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    synthetic_payload (max_length=100000), expected_firewall_trip (max_length=2000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: AgentBidIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on agent_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), estimated_cost_magnitude (le=1000000000),
    estimated_latency_ms (le=86400000, ge=0), estimated_carbon_gco2eq (le=10000.0, ge=0.0), confidence_score
    (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: AmbientState is a declarative and frozen snapshot representing N-dimensional geometry at a
    specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    status_message (max_length=2000), progress (le=1000000000.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    status_message: str = Field(
        max_length=2000,
        description="The semantic 1D string projection representing the active kinetic execution state.",
    )
    progress: float | None = Field(
        le=1000000000.0, default=None, description="The progress ratio from 0.0 to 1.0, or None if indeterminate."
    )


class AnalogicalMappingTask(CoreasonBaseState):
    """
    AGENT INSTRUCTION: AnalogicalMappingTask is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on task_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), source_domain (max_length=2000), target_domain
    (max_length=2000), required_isomorphisms (le=86400000, ge=1), divergence_temperature_override (le=10.0,
    ge=0.0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

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
    AGENT INSTRUCTION: AnchoringPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    anchor_prompt_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), max_semantic_drift (ge=0.0,
    le=1.0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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


type AttestationMechanismProfile = Literal["fido2_webauthn", "zk_snark_groth16", "pqc_ml_dsa"]


class AuctionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: AuctionPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_bidding_window_ms (le=86400000). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    auction_type: AuctionMechanismProfile = Field(description="The market mechanism governing the auction.")
    tie_breaker: TieBreakerPolicy = Field(description="The deterministic rule for resolving tied bids.")
    max_bidding_window_ms: int = Field(
        le=86400000, description="The absolute timeout in milliseconds for nodes to submit proposals."
    )


class BackpressurePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: BackpressurePolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_queue_depth (le=1000000000), token_budget_per_branch (le=1000000000), max_tokens_per_minute
    (le=1000000000, gt=0), max_requests_per_minute (le=1000000000, gt=0), max_uninterruptible_span_ms
    (le=86400000, gt=0), max_concurrent_tool_invocations (le=1000000000, gt=0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: BaseIntent is a non-monotonic kinetic trigger bounding a formal capability request. Serves
    as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """


class BasePanelProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: BasePanelProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on panel_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    panel_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="Unique identifier for the panel."
    )


class BaseStateEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: BaseStateEvent is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on event_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), timestamp (ge=0.0, le=253402300799.0). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    """
    AGENT INSTRUCTION: SystemFaultEvent is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    type: Literal["system_fault"] = Field(
        default="system_fault", description="Discriminator type for a system fault event."
    )


class BoundedInterventionScopePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: BoundedInterventionScopePolicy is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    allowed_fields (max_length=1000000000); constrained by @model_validator hooks (sort_arrays) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: BoundedJSONRPCIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: jsonrpc; intrinsic Pydantic limits on method (max_length=1000), params (max_length=86400000), id
    (le=1000000000); enforced via @field_validator structural bounds (validate_params_depth_and_size). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    """
    AGENT INSTRUCTION: BrowserDOMState is a declarative and frozen snapshot representing N-dimensional geometry at
    a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on current_url (max_length=2000), viewport_size
    (max_length=1000000000), dom_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'),
    accessibility_tree_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), screenshot_cid
    (max_length=2000); enforced via @field_validator structural bounds (_enforce_spatial_safety). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
            except (ValueError, OverflowError, IndexError):
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
    """
    AGENT INSTRUCTION: BypassReceipt is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: justification; intrinsic Pydantic limits on artifact_event_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), cryptographic_null_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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


class CanonicalGroundingReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: CanonicalGroundingReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on canonical_id
    (min_length=1, max_length=2000), cosine_similarity (ge=-1.0, le=1.0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    target_database: ExtractionOntologyTarget = Field(
        description="The authoritative vector database or nomenclature system."
    )
    canonical_id: str = Field(
        min_length=1, max_length=2000, description="The exact canonical identifier (e.g., a SNOMED code)."
    )
    cosine_similarity: float = Field(
        ge=-1.0,
        le=1.0,
        description="The mathematical proof of geometric distance matching the extracted concept to the canonical database.",  # noqa: E501
    )


class CausalAttributionState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: CausalAttributionState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    source_event_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), influence_weight (ge=0.0,
    le=1.0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CollectiveIntelligenceProfile is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on synergy_index
    (le=1000000000.0), coordination_score (le=1.0), information_integration (le=1.0). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: ShapleyAttributionReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    causal_attribution_score (le=1.0), normalized_contribution_percentage (ge=0.0, le=1.0),
    confidence_interval_lower (le=1000000000.0), confidence_interval_upper (le=1000000000.0). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: CausalExplanationEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on target_outcome_event_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks (sort_agent_attributions) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: CausalDirectedEdgeState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: edge_type; intrinsic Pydantic limits on source_variable (min_length=1), target_variable
    (min_length=1). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    source_variable: str = Field(min_length=1, description="The independent variable $X$.")
    target_variable: str = Field(min_length=1, description="The dependent variable $Y$.")
    edge_type: Literal["direct_cause", "confounder", "collider", "mediator"] = Field(
        description="The specific Pearlian topological relationship between the two variables."
    )


class CircuitBreakerEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: CircuitBreakerEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on error_signature (max_length=2000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: ConstitutionalAmendmentIntent is a non-monotonic kinetic trigger bounding a formal
    capability request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on drift_event_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), justification (max_length=2000). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    """
    AGENT INSTRUCTION: ContinuousMutationPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: mutation_paradigm; intrinsic Pydantic limits on max_uncommitted_edges (le=1000000000, gt=0),
    micro_batch_interval_ms (le=86400000, gt=0); constrained by @model_validator hooks
    (enforce_append_only_vram_bound) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    """
    AGENT INSTRUCTION: CounterfactualRegretEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on historical_event_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), counterfactual_intervention (max_length=2000), expected_utility_actual
    (le=1000000000.0), expected_utility_simulated (le=1000000000.0), epistemic_regret (le=1000000000.0),
    policy_mutation_gradients (le=1000000000.0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    AGENT INSTRUCTION: CrossSwarmHandshakeState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: status; intrinsic Pydantic limits on handshake_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), initiating_tenant_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), receiving_tenant_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CrossoverPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    blending_factor (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: CrystallizationPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: target_cognitive_tier; intrinsic Pydantic limits on min_observations_required (le=1000000000, ge=10),
    aleatoric_entropy_threshold (le=0.1). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: CustodyReceipt is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on record_id
    (min_length=1, pattern='^[a-zA-Z0-9_.:-]+$', max_length=255), source_node_id (min_length=1,
    pattern='^[a-zA-Z0-9_.:-]+$', max_length=255), applied_policy_id (min_length=1, pattern='^[a-zA-Z0-9_.:-]+$',
    max_length=255), pre_redaction_hash (min_length=1, pattern='^[a-f0-9]{64}$', max_length=255),
    post_redaction_hash (min_length=1, pattern='^[a-f0-9]{64}$', max_length=255), redaction_timestamp_unix_nano
    (ge=0, le=253402300799000000000). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: DefeasibleAttackEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on attack_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), source_claim_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), target_claim_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$').
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    attack_vector: DefeasibleEdgeType = Field(description="Geometric matrices of undercutting defeaters.")


class DimensionalProjectionContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: DimensionalProjectionContract is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    source_model_name (max_length=2000), target_model_name (max_length=2000), projection_matrix_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), isometry_preservation_score (ge=0.0, le=1.0). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    """
    AGENT INSTRUCTION: DistributionProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on mean
    (le=1000000000.0), variance (le=1000000000.0), confidence_interval_95 (max_length=1000000000); constrained by
    @model_validator hooks (validate_confidence_interval) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: DiversityPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    min_adversaries (le=1000000000), temperature_variance (le=1000000000.0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: DocumentLayoutRegionState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: block_type; intrinsic Pydantic limits on block_id (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$',
    min_length=1). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    """
    AGENT INSTRUCTION: DocumentLayoutManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on blocks
    (max_length=1000000000); constrained by @model_validator hooks (verify_dag_and_integrity) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: ContextExpansionPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: expansion_paradigm; intrinsic Pydantic limits on max_token_budget (le=1000000000, gt=0),
    surrounding_sentences_k (le=1000000000, ge=1), parent_merge_threshold (ge=0.0, le=1.0). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: TopologicalRetrievalContract is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: allowed_causal_relationships; intrinsic Pydantic limits on max_hop_depth (le=1000000000, ge=1),
    allowed_causal_relationships (min_length=1); constrained by @model_validator hooks (sort_arrays) for exact
    graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: LatentProjectionIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on top_k_candidates (gt=0), min_isometry_score (ge=-1.0, le=1.0). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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


class DecomposedSubQueryState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: DecomposedSubQueryState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on sub_query_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), expected_information_gain (ge=0.0, le=1.0);
    constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    sub_query_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    latent_target_vector: VectorEmbeddingState = Field(
        description="The dense embedding of what this specific sub-query is hunting for."
    )
    expected_information_gain: float = Field(
        ge=0.0, le=1.0, description="The Bayesian EIG expected from resolving this specific branch."
    )
    required_surface_capabilities: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        description="The explicit array of capability strings expected to resolve this."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "required_surface_capabilities", sorted(self.required_surface_capabilities))
        return self


class SemanticDiscoveryIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SemanticDiscoveryIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on parent_decomposition_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), min_isometry_score (ge=-1.0, le=1.0), required_structural_types
    (max_length=1000000000); constrained by @model_validator hooks (sort_required_structural_types) for exact
    graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

    type: Literal["semantic_discovery"] = Field(
        default="semantic_discovery", description="Discriminator for geometric boundary of latent tool discovery."
    )
    parent_decomposition_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description=(
            "The cryptographic pointer linking this specific retrieval hop back to the "
            "governing QueryDecompositionManifest DAG."
        ),
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


class QueryDecompositionManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: QueryDecompositionManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on manifest_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), root_intent_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'),
    surface_projection_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by
    @model_validator hooks (sort_execution_dag_edges, verify_dag_integrity) for exact graph determinism. All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    type: Literal["query_decomposition"] = Field(default="query_decomposition")
    manifest_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    root_intent_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The cryptographic SHA-256 hash of the high-entropy, monolithic user prompt prior to algorithmic Query Reformulation.",  # noqa: E501
    )
    surface_projection_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The pointer to the OntologicalSurfaceProjectionManifest",
    )
    sub_queries: dict[Annotated[str, StringConstraints(max_length=255)], DecomposedSubQueryState] = Field(
        description="Matrix of decomposed semantic intents"
    )
    execution_dag_edges: list[tuple[str, str]] = Field(
        description="Directed edges (source_sub_query_id, target_sub_query_id)"
    )

    @model_validator(mode="after")
    def sort_execution_dag_edges(self) -> Self:
        object.__setattr__(self, "execution_dag_edges", sorted(self.execution_dag_edges))
        return self

    @model_validator(mode="after")
    def verify_dag_integrity(self) -> Self:
        adj: dict[str, list[str]] = {node_id: [] for node_id in self.sub_queries}
        for source, target in self.execution_dag_edges:
            if source not in self.sub_queries:
                raise ValueError(f"Ghost node referenced in execution_dag_edges source: {source}")
            if target not in self.sub_queries:
                raise ValueError(f"Ghost node referenced in execution_dag_edges target: {target}")
            adj[source].append(target)
        visited: set[str] = set()
        recursion_stack: set[str] = set()
        for start_node in self.sub_queries:
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
                        raise ValueError("Execution DAG contains cycles")
                except StopIteration:
                    recursion_stack.remove(curr)
                    stack.pop()
        return self


class DraftingIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: DraftingIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, timeout_action; intrinsic Pydantic limits on context_prompt (max_length=2000), resolution_schema
    (max_length=1000000000). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: DynamicConvergenceSLA is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    convergence_delta_epsilon (le=1.0, ge=0.0), lookback_window_steps (le=1000000000, gt=0),
    minimum_reasoning_steps (le=1000000000, gt=0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: EmbodiedSensoryVectorProfile is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: sensory_modality; intrinsic Pydantic limits on bayesian_surprise_score (le=1.0, ge=0.0),
    temporal_duration_ms (gt=0, le=86400000). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    """
    AGENT INSTRUCTION: BargeInInterruptEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, epistemic_disposition; intrinsic Pydantic limits on target_event_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), retained_partial_payload (max_length=100000). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    disfluency_type: DisfluencyRole
    evicted_token_count: int = Field(default=0)


type EncodingChannelProfile = Literal["x", "y", "color", "size", "opacity", "shape", "text"]


class EnsembleTopologyProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EnsembleTopologyProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: fusion_function; intrinsic Pydantic limits on concurrent_branch_ids (min_length=2); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: EpistemicCompressionSLA is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: required_grounding_density; intrinsic Pydantic limits on max_allowed_entropy_loss (ge=0.0, le=1.0).
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    AGENT INSTRUCTION: EpistemicPromotionEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on crystallized_semantic_node_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), compression_ratio (le=1.0); constrained by @model_validator hooks (sort_arrays)
    for exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: EpistemicScanningPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: action_on_gap; intrinsic Pydantic limits on dissonance_threshold (ge=0.0, le=1.0). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    active: bool = Field(description="Whether the epistemic scanner is active.")
    dissonance_threshold: float = Field(
        ge=0.0, le=1.0, description="The threshold for cognitive dissonance before triggering an action."
    )
    action_on_gap: Literal["fail", "probe", "clarify"] = Field(
        description="The action to take when an epistemic gap is detected."
    )


class EpistemicTransmutationTask(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicTransmutationTask is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: target_modalities; intrinsic Pydantic limits on task_id (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$',
    min_length=1), artifact_event_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    target_modalities (min_length=1), execution_cost_budget_magnitude (le=1000000000, ge=0); constrained by
    @model_validator hooks (validate_grounding_density_for_visuals, sort_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

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
    target_layout_region_ids: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] | None = Field(
        default=None,
        description="The explicit array of DocumentLayoutRegionState block_ids the VLM must constrain its extraction to.",  # noqa: E501
    )
    extraction_contracts: list[DeterministicExtractionContract] = Field(
        default_factory=list,
        description="The strict array of deterministic Regex/Selector rules applied to the VLM output to sanitize the final payload.",  # noqa: E501
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
        if self.target_layout_region_ids is not None:
            object.__setattr__(self, "target_layout_region_ids", sorted(self.target_layout_region_ids))
        object.__setattr__(self, "extraction_contracts", sorted(self.extraction_contracts, key=lambda x: x.contract_id))
        return self


class EscalationContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EscalationContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    uncertainty_escalation_threshold (ge=0.0, le=1.0), max_latent_tokens_budget (le=1000000000, gt=0),
    max_test_time_compute_ms (le=86400000, gt=0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    predictive_entropy_sla: PredictiveEntropySLA | None = Field(default=None)


class EscalationIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EscalationIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, timeout_action; intrinsic Pydantic limits on tripped_rule_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

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
    """
    AGENT INSTRUCTION: EscrowPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    escrow_locked_magnitude (le=1000000000, ge=0), release_condition_metric (max_length=2000),
    refund_target_node_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    AGENT INSTRUCTION: EvictionPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: strategy; intrinsic Pydantic limits on max_retained_tokens (le=1000000000, gt=0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: EvidentiaryWarrantState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    source_event_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), source_semantic_node_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), justification (max_length=2000). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: EpistemicArgumentClaimState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on claim_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), proponent_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), text_chunk (max_length=50000); constrained by @model_validator hooks
    (sort_argument_claim_arrays) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: EpistemicArgumentGraphState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on claims
    (max_length=10000), attacks (max_length=10000). All field limits must be strictly validated at instantiation
    to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: ExecutionNodeReceipt is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on request_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), parent_request_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), root_request_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    node_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'); constrained by @model_validator hooks
    (validate_lineage, populate_hash) for exact graph determinism; enforced via @field_validator structural bounds
    (enforce_payload_topology). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: FYIIntent is a non-monotonic kinetic trigger bounding a formal capability request. Serves
    as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

    type: Literal["fyi"] = Field(default="fyi", description="Discriminator for an FYI intent.")


class FallbackSLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: FallbackSLA is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: timeout_action; intrinsic Pydantic limits on timeout_seconds (le=86400, gt=0). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: FallbackIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on type (le=1000000000). All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

    type: Literal["fallback_intent"] = Field(
        le=1000000000, default="fallback_intent", description="The type of the resilience payload."
    )
    target_node_id: NodeIdentifierState = Field(description="The ID of the failing node.")
    fallback_node_id: NodeIdentifierState = Field(description="The ID of the node to use as a fallback.")


class FalsificationContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: FalsificationContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on condition_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), description (max_length=2000),
    required_tool_name (max_length=2000), falsifying_observation_signature (max_length=2000). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: FaultInjectionProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    target_node_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), intensity (le=1000000000.0). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: FederatedCapabilityAttestationReceipt is a mathematically defined coordinate on the Merkle-
    DAG representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    attestation_id (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1); constrained by @model_validator
    hooks (enforce_restricted_vault_locks) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: FederatedStateSnapshot is an exact topological boundary enforcing strict capability
    parameters and physical execution state.

    CAUSAL AFFORDANCE: Resolves graph constraints and unlocks specific spatial operations or API boundaries.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on topology_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: DAG Routing, Topographical Component, Capability Definition, Semantic Anchor
    """

    topology_id: str | None = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the federated topology, if applicable.",  # noqa: E501
    )


class FitnessObjectiveProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: FitnessObjectiveProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on target_metric
    (max_length=2000), weight (le=1.0). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: FormalVerificationContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: proof_system; intrinsic Pydantic limits on invariant_theorem (max_length=2000), compiled_proof_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: DelegatedCapabilityManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on capability_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), expiration_timestamp (ge=0.0,
    le=253402300799.0), cryptographic_signature (max_length=10000); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: BudgetExhaustionEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on exhausted_escrow_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), final_burn_receipt_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: TokenBurnReceipt is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on tool_invocation_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), input_tokens (le=1000000000, ge=0), output_tokens (le=1000000000, ge=0),
    burn_magnitude (le=1000000000, ge=0). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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


class TokenMergingPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: TokenMergingPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    target_compression_ratio (ge=0.0, le=1.0), layer_whitelist (min_length=1, max_length=1000000000); constrained
    by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    metric: TokenMergeMetric = Field(description="The mathematical metric used to evaluate attention entropy.")
    matching_algorithm: TokenMatchingAlgorithm = Field(
        description="The algorithm used to physically fuse redundant tokens."
    )
    target_compression_ratio: float = Field(
        ge=0.0, le=1.0, description="The strictly typed percentage of the active context window to safely compress."
    )
    layer_whitelist: list[Annotated[int, Field(ge=0)]] = Field(
        min_length=1, max_length=1000000000, description="The specific transformer blocks authorized to fuse tokens."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "layer_whitelist", sorted(self.layer_whitelist))
        return self


class GlobalGovernancePolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: GlobalGovernancePolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_budget_magnitude (le=1000000000), max_global_tokens (le=1000000000), max_carbon_budget_gco2eq (le=10000.0,
    ge=0.0), global_timeout_seconds (le=86400, ge=0); constrained by @model_validator hooks
    (enforce_prosperity_license) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: GenerativeManifoldSLA is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_topological_depth (le=1000000000, ge=1), max_node_fanout (le=1000000000, ge=1), max_synthetic_tokens
    (le=1000000000, ge=1); constrained by @model_validator hooks (enforce_geometric_bounds) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    """
    AGENT INSTRUCTION: GlobalSemanticProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: detected_modalities; intrinsic Pydantic limits on artifact_event_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), token_density (le=1000000000, ge=0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    """
    AGENT INSTRUCTION: DynamicRoutingManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on manifest_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), branch_budgets_magnitude
    (max_length=1000000000); constrained by @model_validator hooks (sort_arrays, sort_bypassed_steps,
    validate_modality_alignment, validate_conservation_of_custody) for exact graph determinism. All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: GovernancePolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on policy_name
    (max_length=2000); constrained by @model_validator hooks (sort_rules) for exact graph determinism. All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: GrammarPanelProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, mark; intrinsic Pydantic limits on panel_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), title (max_length=2000), ledger_source_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), mark (le=1000000000); constrained by @model_validator hooks (sort_encodings)
    for exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: GraphFlatteningPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: node_projection_mode, edge_projection_mode. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: HTTPTransportProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on headers (max_length=1000000000); enforced via @field_validator
    structural bounds (_prevent_crlf_injection). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    type: Literal["http"] = Field(default="http", description="Type of transport.")
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the stateless connection.")
    headers: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(
        max_length=1000000000,
        default_factory=dict,
        description="HTTP headers, strictly bounded for zero-trust credentials.",
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
    """
    AGENT INSTRUCTION: HomomorphicEncryptionProfile is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: fhe_scheme; intrinsic Pydantic limits on public_key_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), ciphertext_blob (max_length=5000000). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: HypothesisStakeReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on agent_id
    (le=1000000000), target_hypothesis_id (le=1000000000), staked_magnitude (le=1000000000, gt=0),
    implied_probability (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: InformationalIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, timeout_action; intrinsic Pydantic limits on message (max_length=2000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

    type: Literal["informational"] = Field(
        default="informational", description="Discriminator for read-only informational handoffs."
    )
    message: str = Field(max_length=2000, description="The context or summary to display to the human operator.")
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The orchestrator's automatic fallback if the human does not acknowledge the intent in time."
    )


class TaxonomicNodeState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: TaxonomicNodeState is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on node_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), semantic_label (max_length=2000); constrained by
    @model_validator hooks (sort_taxonomic_arrays) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: GenerativeTaxonomyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on manifest_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), root_node_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), nodes (max_length=1000000000); constrained by @model_validator hooks
    (verify_dag_integrity) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: TaxonomicRestructureIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, restructure_heuristic. All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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


class IntentClassificationReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: IntentClassificationReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by @model_validator hooks
    (sort_concurrent_intents) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    primary_intent: ValidRoutingIntent = Field(description="The argmax intent with highest probability.")
    concurrent_intents: dict[ValidRoutingIntent, float] = Field(
        default_factory=dict,
        description="Dictionary of adjacent intents and confidence scores (0.0 to 1.0). Used for superposition branching.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_concurrent_intents(self) -> Self:
        if self.concurrent_intents:
            object.__setattr__(self, "concurrent_intents", dict(sorted(self.concurrent_intents.items())))
        return self


class TaxonomicRoutingPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: TaxonomicRoutingPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: intent_to_heuristic_matrix, fallback_heuristic; intrinsic Pydantic limits on policy_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), intent_to_heuristic_matrix (max_length=1000).
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    policy_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this pre-flight routing policy.",
    )
    intent_to_heuristic_matrix: dict[
        ValidRoutingIntent,
        Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"],
    ] = Field(
        max_length=1000,
        description="Strict dictionary binding classified natural language intents to bounded spatial heuristics.",
    )
    superposition_branching_threshold: float = Field(default=0.85)

    fallback_heuristic: Literal["chronological", "entity_centric", "semantic_cluster", "confidence_decay"] = Field(
        description="The deterministic default applied if intent classification falls below the safety threshold."
    )


class ProgramSynthesisIntent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A declarative neural intent representing Inductive Logic Programming (ILP).
    The agent proposes a generalized programmatic script (AST) based on a prior successful observation.
    """

    type: Literal["program_synthesis"] = Field(
        default="program_synthesis", description="Discriminator type for a program synthesis intent."
    )
    source_observation_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the positive example $E^+$ that the agent is generalizing.",
    )
    target_runtime: Literal["jsonata", "xpath", "wasm32-wasi", "python_ast", "regex"] = Field(
        description="The specific deterministic engine required to compile the payload."
    )
    synthesized_ast_payload: str = Field(
        max_length=100000, description="The raw code, query, or WebAssembly text proposed by the LLM."
    )
    expected_output_schema: dict[Annotated[str, StringConstraints(max_length=255)], Any] = Field(
        description="The strict JSON Schema the orchestrator must use to mathematically validate the script's output."
    )

    @field_validator("expected_output_schema", mode="before")
    def _validate_schema_bounds(cls, v: JsonPrimitiveState) -> JsonPrimitiveState:  # noqa: N805
        return _validate_payload_bounds(v)

    @model_validator(mode="after")
    def _sort_arrays(self) -> Self:
        object.__setattr__(
            self,
            "expected_output_schema",
            dict(sorted(self.expected_output_schema.items(), key=lambda x: x[0])),
        )
        return self


class SchemaInferenceIntent(CoreasonBaseState):
    """AGENT INSTRUCTION: A declarative neural intent representing probabilistic schema induction.
    The LLM evaluates a micro-batch of intercepted, obfuscated data and projects it into a strict StateContract."""

    type: Literal["schema_inference"] = Field(default="schema_inference")
    source_capture_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    sampled_micro_batch: list[JsonPrimitiveState] = Field(description="The isolated safe slice of the payload")
    inferred_schema_contract: StateContract = Field(
        description="The resulting rigid schema the LLM believes governs the data"
    )
    compiled_extraction_routine: DeterministicExtractionContract | None = Field(
        default=None,
        description="Optional mapping generated by the LLM, such as a JSONata query, "
        "to physically transform the raw intercept into the inferred schema",
    )

    @field_validator("sampled_micro_batch", mode="before")
    @classmethod
    def validate_payload(cls, v: Any) -> Any:
        return _validate_payload_bounds(v)

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "sampled_micro_batch", sorted(self.sampled_micro_batch, key=lambda x: str(x)))
        return self


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
    | LatentProjectionIntent
    | ProgramSynthesisIntent
    | QueryDecompositionManifest
    | SchemaInferenceIntent,
    Field(discriminator="type"),
]


class InputMappingContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: InputMappingContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on parent_key
    (max_length=2000), child_key (max_length=2000). All field limits must be strictly validated at instantiation
    to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    parent_key: str = Field(max_length=2000, description="The key in the parent's shared state contract.")
    child_key: str = Field(max_length=2000, description="The mapped key in the nested topology's state contract.")


class InsightCardProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: InsightCardProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on panel_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), title (max_length=2000), markdown_content (max_length=100000); enforced via
    @field_validator structural bounds (sanitize_markdown, _prevent_malicious_uri_schemes). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: InterventionIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on context_summary (max_length=2000), proposed_action
    (max_length=1000000000), adjudication_deadline (ge=0.0, le=253402300799.0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: InterventionalCausalTask is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on task_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), target_hypothesis_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), intervention_variable (max_length=2000), do_operator_state
    (max_length=2000), expected_causal_information_gain (ge=0.0, le=1.0), execution_cost_budget_magnitude
    (le=1000000000, ge=0). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: JSONRPCErrorState is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on code
    (le=1000000000), message (max_length=2000). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: JSONRPCErrorResponseState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: jsonrpc; intrinsic Pydantic limits on id (le=1000000000). All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: InterventionPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: BaseNodeProfile is a declarative and frozen snapshot representing N-dimensional geometry at
    a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on description
    (max_length=2000), architectural_intent (max_length=2000), justification (max_length=2000); constrained by
    @model_validator hooks (sort_agent_attestation_arrays) for exact graph determinism; enforced via
    @field_validator structural bounds (validate_domain_extensions_depth). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: HumanNodeProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    type: Literal["human"] = Field(default="human", description="Discriminator for a Human node.")
    required_attestation: AttestationMechanismProfile | None = Field(
        default=None,
        description="AGENT INSTRUCTION: If set, the orchestrator MUST NOT resolve\n        this node without a cryptographically matching WetwareAttestationContract\n        supplied in the InterventionReceipt.",  # noqa: E501
    )


class MemoizedNodeProfile(BaseNodeProfile):
    """
    AGENT INSTRUCTION: MemoizedNodeProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on expected_output_schema (max_length=1000000000). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: SystemNodeProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    type: Literal["system"] = Field(default="system", description="Discriminator for a System node.")


class LineageWatermarkReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: LineageWatermarkReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: watermark_protocol; intrinsic Pydantic limits on hop_signatures (max_length=1000000000),
    tamper_evident_root (max_length=2000). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    watermark_protocol: Literal["merkle_dag", "statistical_token", "homomorphic_mac"] = Field(
        description="The mathematical methodology used to embed the chain of custody."
    )
    hop_signatures: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=2000)]
    ] = Field(
        max_length=1000000000,
        description="A dictionary mapping intermediate participant NodeIdentifierStates to their deterministic execution signatures.",  # noqa: E501
    )
    tamper_evident_root: str = Field(
        max_length=2000,
        description="The overarching cryptographic hash (e.g., Merkle Root) proving the structural payload has not been laundered or structurally modified.",  # noqa: E501
    )


class MCPCapabilityWhitelistPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: MCPCapabilityWhitelistPolicy is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: MCPServerManifest is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: transport_type; intrinsic Pydantic limits on server_uri (max_length=2000), binary_hash (min_length=1,
    max_length=128, pattern='^[a-f0-9]{64}$'); constrained by @model_validator hooks
    (enforce_coreason_did_authority) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: KineticSeparationPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: enforcement_action; intrinsic Pydantic limits on policy_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks (sort_clusters) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: ActionSpaceManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    action_space_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), max_concurrent_tool_invocations
    (gt=0, le=1000000000), allowed_discovery_namespaces (max_length=1000); constrained by @model_validator hooks
    (verify_unique_tool_namespaces_and_sort) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    max_concurrent_tool_invocations: int | None = Field(
        default=None,
        gt=0,
        le=1000000000,
        description="The mathematical limit of parallel tool execution to prevent thread starvation.",
    )
    allowed_discovery_namespaces: list[DomainExtensionString] = Field(
        default_factory=list,
        max_length=1000,
        description="The strict whitelist of domain namespaces (e.g., 'ext:clinical') this Action Space is authorized to query via MCP.",  # noqa: E501
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
        # AGENT INSTRUCTION: NEW SORTING LOGIC INJECTED HERE
        object.__setattr__(self, "allowed_discovery_namespaces", sorted(self.allowed_discovery_namespaces))
        return self


class ProceduralMetadataManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ProceduralMetadataManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on metadata_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), target_sop_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), trigger_description (max_length=2000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: OntologicalSurfaceProjectionManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on projection_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1); constrained by @model_validator hooks
    (verify_unique_action_spaces) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: MCPClientIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: method; intrinsic Pydantic limits on method (le=1000000000). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

    method: Literal["mcp.ui.emit_intent"] = Field(..., le=1000000000, description="Method for intent bubbling.")


class MCPPromptReferenceState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: MCPPromptReferenceState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on server_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), prompt_name (max_length=2000), arguments
    (max_length=1000000000), fallback_persona (max_length=2000), prompt_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    """
    AGENT INSTRUCTION: MCPResourceManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on server_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: MCPClientBindingProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on server_uri
    (max_length=2000); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: MacroGridProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on layout_matrix
    (max_length=1000000000); constrained by @model_validator hooks (verify_referential_integrity) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: MarketContract is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    minimum_collateral (le=1000000000.0, ge=0.0), slashing_penalty (ge=0.0); constrained by @model_validator hooks
    (_enforce_economic_escrow_invariant) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: MarketResolutionState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on market_id
    (le=1000000000), winning_hypothesis_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    falsified_hypothesis_ids (max_length=1000000000); constrained by @model_validator hooks (sort_arrays) for
    exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: MechanisticAuditContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: trigger_conditions; intrinsic Pydantic limits on trigger_conditions (min_length=1), target_layers
    (min_length=1), max_features_per_layer (le=1000000000, gt=0); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    """
    AGENT INSTRUCTION: EpistemicProvenanceReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    source_event_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), source_artifact_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    """
    AGENT INSTRUCTION: MigrationContract is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on contract_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), source_version (max_length=2000), target_version
    (max_length=2000), path_transformations (le=1000000000); constrained by @model_validator hooks (sort_arrays)
    for exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    """
    AGENT INSTRUCTION: MultimodalArtifactReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on artifact_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), mime_type (max_length=2000), byte_stream_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), temporal_ingest_timestamp (ge=0.0,
    le=253402300799.0). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    AGENT INSTRUCTION: MutationPolicy is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on mutation_rate
    (ge=0.0, le=1.0), temperature_shift_variance (le=1000000000.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: NDimensionalTensorManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on shape
    (max_length=1000000000), vram_footprint_bytes (le=100000000000), merkle_root (min_length=1, max_length=128,
    pattern='^[a-fA-F0-9]{64}$'), storage_uri (min_length=1, max_length=128); constrained by @model_validator
    hooks (_enforce_physics_engine) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: NeuralAuditAttestationReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on audit_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    """
    AGENT INSTRUCTION: NeuroSymbolicHandoffContract is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: solver_protocol; intrinsic Pydantic limits on handoff_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), formal_grammar_payload (max_length=100000), timeout_ms
    (le=86400000, gt=0). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    handoff_id: str = Field(
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        min_length=1,
        description="Unique identifier for this symbolic delegation.",
    )
    solver_protocol: Literal[
        "z3", "lean4", "coq", "tla_plus", "sympy", "jsonata", "xpath", "wasm32-wasi", "python_ast"
    ] = Field(description="The target deterministic math/logic or data extraction engine.")
    max_vram_mb: int | None = Field(
        default=None,
        le=10000,
        gt=0,
        description="The strict physical VRAM memory ceiling allocated to the symbolic solver/Wasm runtime to prevent OOM extraction faults.",  # noqa: E501
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
    AGENT INSTRUCTION: NormativeDriftEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on tripped_rule_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), measured_semantic_drift (le=1000000000.0), contradiction_proof_hash
    (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: ObservabilityPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    traces_sampled: bool = Field(
        default=True, description="Whether the orchestrator must record telemetry for this topology."
    )
    detailed_events: bool = Field(default=False, description="Whether to include granular intra-tool loop events.")


class OntologicalHandshakeReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: OntologicalHandshakeReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: alignment_status; intrinsic Pydantic limits on handshake_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), participant_node_ids (max_length=1000000000, min_length=2),
    measured_cosine_similarity (ge=-1.0, le=1.0); constrained by @model_validator hooks (sort_arrays) for exact
    graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: OutputMappingContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on child_key
    (max_length=2000), parent_key (max_length=2000). All field limits must be strictly validated at instantiation
    to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    child_key: str = Field(max_length=2000, description="The key in the nested topology's state contract.")
    parent_key: str = Field(max_length=2000, description="The mapped key in the parent's shared state contract.")


class CompositeNodeProfile(BaseNodeProfile):
    """
    AGENT INSTRUCTION: CompositeNodeProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; constrained by @model_validator hooks (sort_composite_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: OverrideIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on override_action (max_length=1000000000), justification
    (max_length=2000). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    """
    AGENT INSTRUCTION: PeftAdapterContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on adapter_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), safetensors_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'), base_model_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'),
    adapter_rank (le=1000000000, gt=0), target_modules (min_length=1), eviction_ttl_seconds (le=86400, gt=0);
    constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

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
    """
    AGENT INSTRUCTION: PersistenceCommitReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on lakehouse_snapshot_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), committed_state_diff_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), target_table_uri (min_length=1). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    AGENT INSTRUCTION: PredictionMarketState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on market_id
    (le=1000000000), resolution_oracle_condition_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    lmsr_b_parameter (pattern='^\\d+\\.\\d+$', max_length=255), current_market_probabilities (le=1000000000);
    constrained by @model_validator hooks (sort_prediction_market_state_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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


class PredictiveEntropySLA(CoreasonBaseState):
    """
    AGENT INSTRUCTION: PredictiveEntropySLA is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: mandatory_fallback_intent; intrinsic Pydantic limits on max_entropy_for_reflex (ge=0.0). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    metric: EntropyMetric = Field(
        default="semantic_entropy",
        description="The specific mathematical uncertainty metric used to evaluate the latent space.",
    )
    max_entropy_for_reflex: float = Field(
        ge=0.0,
        description="If the distribution's entropy falls BELOW this exact float, the orchestrator is authorized to guess the intent and execute.",  # noqa: E501
    )
    mandatory_fallback_intent: Literal["drafting_elicitation", "escalation_request"] = Field(
        description="The strict routing fallback triggered if the entropy exceeds the safety boundary."
    )


class PresentationManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: PresentationManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    intent: AnyPresentationIntent = Field(description="The reason an agent is presenting this data to a human.")
    grid: MacroGridProfile = Field(description="The grid of panels being presented.")


class EpistemicSOPManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicSOPManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on sop_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), cognitive_steps (max_length=1000000000);
    constrained by @model_validator hooks (reject_ghost_nodes) for exact graph determinism. All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: ProcessRewardContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    pruning_threshold (ge=0.0, le=1.0), max_backtracks_allowed (le=1000000000, ge=0), evaluator_model_name
    (max_length=2000). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    convergence_sla: DynamicConvergenceSLA | None = Field(
        default=None,
        description="The dynamic circuit breaker that halts the search when PRM variance converges, preventing VRAM waste.",  # noqa: E501
    )
    enforce_reasoning_trace: bool = Field(
        default=True,
        description="Forces the LLM to output a CognitiveReasoningTraceState before attempting generation again.",
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
    AGENT INSTRUCTION: ComputeProvisioningIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on max_budget
    (le=1000000000.0), required_capabilities (max_length=1000000000); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: QuarantineIntent is a non-monotonic kinetic trigger bounding a formal capability request.
    Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on type (le=1000000000), reason (max_length=2000). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    """
    AGENT INSTRUCTION: SSETransportProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; enforced via @field_validator structural bounds (_prevent_crlf_injection). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    """
    AGENT INSTRUCTION: SalienceProfile is a declarative and frozen snapshot representing N-dimensional geometry at
    a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    baseline_importance (ge=0.0, le=1.0), decay_rate (le=1.0, ge=0.0). All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    baseline_importance: float = Field(
        ge=0.0, le=1.0, description="The starting importance score of this latent state from 0.0 to 1.0."
    )
    decay_rate: float = Field(
        le=1.0, ge=0.0, description="The rate at which this epistemic coordinate's relevance decays over time."
    )


type ScaleTypeProfile = Literal["linear", "log", "time", "ordinal", "nominal"]


class SelfCorrectionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SelfCorrectionPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on max_loops
    (ge=0, le=50). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    max_loops: int = Field(ge=0, le=50, description="The maximum number of self-correction loops allowed.")
    rollback_on_failure: bool = Field(description="Whether to rollback to the previous state on failure.")


class SemanticFirewallPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SemanticFirewallPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: action_on_violation; intrinsic Pydantic limits on max_input_tokens (le=1000000000, gt=0); constrained
    by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: InformationFlowPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on policy_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks
    (sort_rules) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    stream_interruption: StreamInterruptionPolicy | None = Field(default=None)

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
    AGENT INSTRUCTION: SimulationConvergenceSLA is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_monte_carlo_rollouts (le=1000000000, gt=0), variance_tolerance (ge=0.0, le=1.0). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: SimulationEscrowContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    locked_magnitude (le=1000000000, gt=0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    locked_magnitude: int = Field(
        le=1000000000,
        gt=0,
        description="The strictly typed boundary requiring locked magnitude to prevent zero-cost griefing of the swarm.",  # noqa: E501
    )


class ExogenousEpistemicEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ExogenousEpistemicEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on shock_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), target_node_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'), bayesian_surprise_score (le=1.0, ge=0.0), synthetic_payload
    (max_length=1000000000). All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    # Note: SimulationEscrowContract.locked_magnitude enforces gt=0 at the Field level.
    # No additional model_validator is needed for economic escrow bounds.


class SpanEvent(CoreasonBaseState):
    """
    AGENT INSTRUCTION: SpanEvent is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on name
    (max_length=2000), timestamp_unix_nano (ge=0, le=253402300799000000000), attributes (max_length=1000000000).
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: ExecutionSpanReceipt is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on trace_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), span_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), parent_span_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    name (max_length=2000), start_time_unix_nano (ge=0, le=253402300799000000000), end_time_unix_nano (ge=0,
    le=253402300799000000000), events (max_length=10000); constrained by @model_validator hooks
    (validate_temporal_bounds, sort_events) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: SpatialKinematicActionIntent is a non-monotonic kinetic trigger bounding a formal
    capability request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: action_type; intrinsic Pydantic limits on target_frame_cid (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), trajectory_duration_ms (le=86400000, gt=0), expected_visual_concept
    (max_length=2000); constrained by @model_validator hooks (enforce_tensor_symmetry) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
    """

    action_type: Literal["click", "double_click", "drag_and_drop", "scroll", "hover", "keystroke"] = Field(
        description="The specific kinematic interaction paradigm."
    )
    target_coordinate: SpatialCoordinateProfile | None = Field(
        default=None, description="The primary spatial terminus for clicks or hovers."
    )
    target_frame_cid: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="Cryptographic lock tying this physical kinematic action to the exact screenshot frame it was predicted on, preventing temporal mis-clicks.",  # noqa: E501
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
    temporal_waypoints_ms: list[Annotated[int, Field(ge=0)]] = Field(
        default_factory=list,
        description="The strictly typed array of temporal waypoints ($t$) corresponding 1:1 with bezier_control_points, completing the $(x, y, t)$ kinematic tensor.",  # noqa: E501
    )

    @model_validator(mode="after")
    def enforce_tensor_symmetry(self) -> Self:
        object.__setattr__(self, "temporal_waypoints_ms", sorted(self.temporal_waypoints_ms))
        if (
            self.temporal_waypoints_ms
            and self.bezier_control_points
            and len(self.temporal_waypoints_ms) != len(self.bezier_control_points)
        ):
            raise ValueError(
                "Kinematic Tensor Asymmetry: temporal_waypoints_ms and bezier_control_points must have the same length."
            )
        return self


class StateContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: StateContract is a rigid mathematical boundary enforcing systemic constraints globally.
    Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: OntologicalAlignmentPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    min_cosine_similarity (ge=-1.0, le=1.0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    """
    AGENT INSTRUCTION: StdioTransportProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on command (max_length=2000), args (max_length=1000000000). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: MCPServerBindingProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on server_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: SteadyStateHypothesisState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    expected_max_latency (le=1000000000.0, ge=0.0), max_loops_allowed (le=1000000000), required_tool_usage
    (max_length=1000000000); constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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


class StreamInterruptionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: StreamInterruptionPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    kinematic_reversal_threshold (ge=1, le=1000000000). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    kinematic_reversal_threshold: int = Field(
        default=3,
        ge=1,
        le=1000000000,
        description="Sequential number of backspaces/deletes required to trigger a hardware-level cache rewind.",
    )
    audio_spike_delta: float | None = Field(
        default=None,
        description="The Voice Activity Detection (VAD) decibel delta required to flag an acoustic barge-in.",
    )
    eviction_strategy: CacheEviction = Field(
        default="lru",
        description="Instructs the inference engine how to physically drop the VRAM context of the Reparandum.",
    )


class ChaosExperimentTask(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ChaosExperimentTask is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on experiment_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    """
    AGENT INSTRUCTION: StructuralCausalGraphProfile is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    observed_variables (max_length=1000000000), latent_variables (max_length=1000000000); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    """
    AGENT INSTRUCTION: HypothesisGenerationEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, status; intrinsic Pydantic limits on hypothesis_id (max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), premise_text (max_length=2000), bayesian_prior (ge=0.0, le=1.0),
    falsification_conditions (min_length=1); constrained by @model_validator hooks (sort_arrays) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    """
    AGENT INSTRUCTION: SyntheticGenerationProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on profile_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), target_schema_ref (min_length=1). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    AGENT INSTRUCTION: System1ReflexPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    confidence_threshold (ge=0.0, le=1.0), allowed_passive_tools (max_length=1000000000); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: System2RemediationIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on fault_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), failing_pointers (min_length=1),
    remediation_prompt (min_length=1); constrained by @model_validator hooks (_sort_failing_pointers) for exact
    graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: TaskAnnouncementIntent is a non-monotonic kinetic trigger bounding a formal capability
    request. Serves as a strictly typed execution coordinate.

    CAUSAL AFFORDANCE: Unlocks targeted execution paths or non-monotonic execution logic via Pearlian do-
    operators.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on task_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), required_action_space_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), max_budget_magnitude (le=1000000000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Kinetic Execution, Non-Monotonic Trigger, Pearlian Do-Operator, Active Inference
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
    AGENT INSTRUCTION: TaskAwardReceipt is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on task_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), cleared_price_magnitude (le=1000000000);
    constrained by @model_validator hooks (validate_escrow_bounds, verify_syndicate_allocation) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: AuctionState is a declarative and frozen snapshot representing N-dimensional geometry at a
    specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    clearing_timeout (le=1000000000, gt=0), minimum_tick_size (le=1000000000.0, gt=0.0); constrained by
    @model_validator hooks (sort_bids) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: LogEvent is a mathematically defined coordinate on the Merkle-DAG representing an immutable
    historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: level; intrinsic Pydantic limits on timestamp (ge=0.0, le=253402300799.0), message (max_length=2000).
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: SpanTraceReceipt is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: status; intrinsic Pydantic limits on span_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), parent_span_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    start_time (ge=0.0, le=253402300799.0), end_time (ge=0.0, le=253402300799.0). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: TemporalBoundsProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on valid_from
    (le=1000000000.0, ge=0.0), valid_to (le=1000000000.0); constrained by @model_validator hooks
    (validate_temporal_bounds) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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


class NegativeHeuristicProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: NegativeHeuristicProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: banned_modalities; constrained by @model_validator hooks (sort_arrays) for exact graph determinism.
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    forbidden_semantic_clusters: list[Annotated[str, StringConstraints(max_length=255)]] = Field(
        description="Explicit array of ontological clusters the orchestrator is mathematically forbidden from traversing.",  # noqa: E501
    )
    banned_modalities: (
        list[Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]] | None
    ) = Field(default=None, description="Strict exclusion of sensory inputs.")
    temporal_exclusion_bounds: list[TemporalBoundsProfile] = Field(
        description="Exact temporal zones mathematically severed from the retrieval graph."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "forbidden_semantic_clusters", sorted(self.forbidden_semantic_clusters))
        if self.banned_modalities is not None:
            object.__setattr__(self, "banned_modalities", sorted(self.banned_modalities))

        # Sort TemporalBoundsProfile. Pydantic models need to be compared somehow.
        # We can sort by dict representation or specific fields to be deterministic.
        # But a simpler way for objects is to sort by string rep.
        # However, for TemporalBoundsProfile it's deterministic to sort by dict or json strings.
        # We'll sort by their dumped JSON strings.
        object.__setattr__(
            self,
            "temporal_exclusion_bounds",
            sorted(self.temporal_exclusion_bounds, key=lambda x: x.model_dump_canonical()),
        )
        return self


class NetworkInterceptState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A deterministic physical actuator representing a headless wiretap
    on the browser/OS network layer (e.g., CDP Network.responseReceived or eBPF socket trace).
    """

    type: Literal["network_intercept"] = Field(default="network_intercept")
    capture_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    target_url_pattern: str = Field(max_length=2000, description="The regex/glob capturing the specific API endpoint")
    protocol: Literal["http_rest", "websocket", "grpc", "graphql"] = Field(
        description="The network protocol wiretapped"
    )
    raw_payload_hash: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="The exact Merkle root of the intercepted byte stream",
    )
    payload_byte_size: int = Field(le=1000000000, ge=0)


class MemoryHeapSnapshot(CoreasonBaseState):
    """AGENT INSTRUCTION: A deterministic physical actuator representing a raw pointer read from an OS-level heap
    or WebAssembly linear memory matrix."""

    type: Literal["memory_heap"] = Field(default="memory_heap")
    snapshot_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    memory_address_pointer: str = Field(
        max_length=255, pattern="^0x[a-fA-F0-9]+$", description="The exact hex coordinate of the buffer start"
    )
    buffer_size_bytes: int = Field(le=100000000000, gt=0)
    raw_buffer_hash: str = Field(min_length=1, max_length=128, pattern="^[a-f0-9]{64}$")


class TerminalBufferState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: TerminalBufferState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on working_directory (max_length=2000), stdout_hash (min_length=1,
    max_length=128, pattern='^[a-f0-9]{64}$'), stderr_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'), env_variables_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    BrowserDOMState | TerminalBufferState | ViewportRasterState | NetworkInterceptState | MemoryHeapSnapshot,
    Field(
        discriminator="type",
        description="A discriminated union of Causal Actuators defining strict perimeters for Exogenous Perturbations to the causal graph.",  # noqa: E501
    ),
]


class TheoryOfMindSnapshot(CoreasonBaseState):
    """
    AGENT INSTRUCTION: TheoryOfMindSnapshot is an exact topological boundary enforcing strict capability
    parameters and physical execution state.

    CAUSAL AFFORDANCE: Resolves graph constraints and unlocks specific spatial operations or API boundaries.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    empathy_confidence_score (ge=0.0, le=1.0); constrained by @model_validator hooks (sort_arrays) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: DAG Routing, Topographical Component, Capability Definition, Semantic Anchor
    """

    target_agent_id: (
        NodeIdentifierState
        | Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    ) = Field(description="The strict DID of the swarm node, or CID of an external user, whose mind is being modeled.")
    assumed_shared_beliefs: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        description="The explicit array of Content Identifiers (CIDs) acting as cryptographic Lineage Watermarks that the modeling agent assumes the target already possesses.",  # noqa: E501
    )
    identified_knowledge_gaps: list[
        Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")]
    ] = Field(
        default_factory=list,
        description="The explicit array of CIDs/DIDs representing the exact coordinate spaces (SemanticNodeStates or Domain Extensions) the target is mathematically proven to lack.",  # noqa: E501
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
    """
    AGENT INSTRUCTION: ToolInvocationEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on tool_name (max_length=2000), parameters (max_length=1000000000),
    authorized_budget_magnitude (le=1000000000, ge=0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    AGENT INSTRUCTION: TraceExportManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on batch_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks
    (sort_spans) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: TruthMaintenancePolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    decay_propagation_rate (ge=0.0, le=1.0), epistemic_quarantine_threshold (ge=0.0, le=1.0), max_cascade_depth
    (le=1000000000, gt=0), max_quarantine_blast_radius (le=1000000000, gt=0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    rebuttal_contract: DefeasibleRebuttalContract | None = Field(
        default=None,
        description="Governs exactly how an incoming correction zeroes out a previous node in the Epistemic Argument Graph without destroying the historical ledger.",  # noqa: E501
    )
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
    AGENT INSTRUCTION: UtilityJustificationGraphReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    optimizing_vectors (max_length=1000000000), degrading_vectors (max_length=1000000000),
    superposition_variance_threshold (le=1000000000.0, ge=0.0); constrained by @model_validator hooks
    (_enforce_mathematical_interlocks) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    optimizing_vectors: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ] = Field(
        max_length=1000000000,
        default_factory=dict,
        description="Multi-dimensional continuous values representing optimizations.",
    )
    degrading_vectors: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ] = Field(
        max_length=1000000000,
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
    """
    AGENT INSTRUCTION: VectorEmbeddingState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on vector_base64
    (pattern='^[A-Za-z0-9+/]*={0,2}$', max_length=5000000), model_name (max_length=2000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    vector_base64: str = Field(
        pattern="^[A-Za-z0-9+/]*={0,2}$", max_length=5000000, description="The base64-encoded dense vector array."
    )
    dimensionality: int = Field(description="The size of the vector array.")
    model_name: str = Field(
        max_length=2000, description="The provenance of the embedding model used (e.g., 'text-embedding-3-large')."
    )


class VisualAffordancePatchState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: VisualAffordancePatchState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: expected_kinetic_action; intrinsic Pydantic limits on patch_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), affordance_probability (ge=0.0, le=1.0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    patch_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    spatial_boundary: SpatialBoundingBoxProfile = Field(description="Strict Euclidean boundaries for the patch.")
    semantic_concept: VectorEmbeddingState = Field(
        description="The latent vector representation of what this patch means."
    )
    affordance_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="The neural track's calculated certainty that this spatial region possesses a kinetic "
        "affordance like clickability.",
    )
    expected_kinetic_action: Literal["click", "scroll", "drag", "type"] | None = Field(
        default=None, description="The predicted affordance type, if any."
    )


class ViewportRasterState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: ViewportRasterState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on screenshot_cid (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks (sort_arrays) for exact graph
    determinism. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    type: Literal["viewport_raster"] = Field(default="viewport_raster")
    viewport_size: tuple[int, int] = Field(
        description="The absolute (W, H) pixel coordinate space used for the affine scaling matrix."
    )
    screenshot_cid: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The cryptographic lock to the exact rasterized frame tensor.",
    )
    extracted_affordances: list[VisualAffordancePatchState] = Field(
        description="The array of identified interactive zones."
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "extracted_affordances", sorted(self.extracted_affordances, key=lambda x: x.patch_id))
        return self


class LatentIntentTrajectoryState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: LatentIntentTrajectoryState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    epistemic_entropy (ge=0.0, le=1.0), trajectory_momentum_scalar (le=1000000000.0, ge=-1000000000.0). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    current_intent_vector: VectorEmbeddingState = Field(
        description="High-dimensional representation of the user's active $E_{target}$."
    )
    epistemic_entropy: float = Field(ge=0.0, le=1.0, description="Shannon entropy of the intent distribution.")
    trajectory_momentum_scalar: float = Field(
        le=1000000000.0,
        ge=-1000000000.0,
        description="Mathematical velocity indicating the rate of convergence toward a terminal goal.",
    )


class EpistemicTransitionMatrixProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicTransitionMatrixProfile is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by standard Pydantic type
    bounds. All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    anticipated_subgoals: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[float, Field(ge=0.0, le=1.0)]
    ] = Field(description="Matrix mapping future intent CIDs to their transition probabilities.")


class SemanticGapAnalysisProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: A rigid set-theoretic evaluation matrix comparing generated claims against factual grounding.
    Isolates hallucinations and omissions.
    """

    target_generation_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The CID of the LLM generation being evaluated.",
    )
    hallucinated_claims: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="Represents G \\ F: Claims generated but not present in the source facts.",
    )
    omitted_context: list[Annotated[str, StringConstraints(max_length=2000)]] = Field(
        default_factory=list,
        description="Represents F \\ G: Critical facts present in the source but missing from the generation.",
    )
    factual_overlap_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="The Jaccard index or structural overlap between the two sets.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "hallucinated_claims", sorted(self.hallucinated_claims))
        object.__setattr__(self, "omitted_context", sorted(self.omitted_context))
        return self


class CognitiveCritiqueProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: CognitiveCritiqueProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    reasoning_trace_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), epistemic_penalty_scalar
    (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    flaw_taxonomy: Literal["hallucination", "omission", "contradiction", "sycophancy", "logical_leap"] | None = Field(
        default=None,
        description="The strict categorical classification of the reasoning flaw, allowing the orchestrator to route to specific deterministic remediation templates.",  # noqa: E501
    )


class KineticBudgetPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: KineticBudgetPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: exploration_decay_curve; intrinsic Pydantic limits on forced_exploitation_threshold_ms (le=86400000,
    gt=0), dynamic_temperature_asymptote (le=1000000000.0, ge=0.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: EpistemicEscalationContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    baseline_entropy_threshold (le=1000000000.0, ge=0.0), test_time_multiplier (le=1000000000.0, gt=1.0),
    max_escalation_tiers (le=1000000000, ge=1). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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


class EpistemicExtractionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicExtractionPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    required_relations (min_length=1), grounding_confidence_threshold (ge=0.0, le=1.0); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    strategy_tier: ComputeStrategyTier = Field(
        description="The mandatory hardware execution mode for this extraction pass."
    )
    required_relations: list[OBORelationEdge] = Field(
        min_length=1, description="The strict array of OBO Relation predicates authorized for edge generation."
    )
    grounding_confidence_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="The minimum cosine similarity required to authorize appending a CanonicalGroundingReceipt.",
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(self, "required_relations", sorted(self.required_relations))
        return self


class FederatedPeftContract(CoreasonBaseState):
    """
    AGENT INSTRUCTION: FederatedPeftContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    adapter_merkle_root (pattern='^[a-f0-9]{64}$'), vram_footprint_bytes (le=100000000000, gt=0), ephemeral_ttl_ms
    (le=86400000, gt=0), cache_priority_weight (ge=0.0, le=1.0). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: SemanticEdgeState is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: causal_relationship; intrinsic Pydantic limits on edge_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), subject_node_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    object_node_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), confidence_score (ge=0.0,
    le=1.0), predicate (max_length=2000). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: SemanticNodeState is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: scope; intrinsic Pydantic limits on node_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), label (max_length=2000), text_chunk (max_length=50000); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    tier: CognitiveMemoryDomain = Field(
        default="semantic", description="The cognitive tier this latent state resides in."
    )
    temporal_bounds: TemporalBoundsProfile | None = Field(
        default=None, description="The time window during which this node is considered valid."
    )
    salience: SalienceProfile | None = Field(
        default=None, description="The mathematical importance profile governing structural pruning."
    )
    canonical_groundings: list[CanonicalGroundingReceipt] = Field(
        default_factory=list, description="Cryptographic proofs of canonical vector alignment."
    )
    fhe_profile: HomomorphicEncryptionProfile | None = Field(
        default=None,
        description="The cryptographic envelope enabling privacy-preserving computation directly on this node's encrypted state.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_arrays(self) -> Self:
        object.__setattr__(
            self, "canonical_groundings", sorted(self.canonical_groundings, key=lambda x: x.canonical_id)
        )
        return self


class VerifiableCredentialPresentationReceipt(CoreasonBaseState):
    """
    AGENT INSTRUCTION: VerifiableCredentialPresentationReceipt is a mathematically defined coordinate on the
    Merkle-DAG representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: presentation_format; intrinsic Pydantic limits on cryptographic_proof_blob (max_length=100000),
    authorization_claims (max_length=86400000). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    AGENT INSTRUCTION: AgentAttestationReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    training_lineage_hash (min_length=1, max_length=128, pattern='^[a-f0-9]{64}$'), developer_signature
    (max_length=2000), capability_merkle_root (pattern='^[a-f0-9]{64}$'); constrained by @model_validator hooks
    (sort_arrays) for exact graph determinism. All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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


class AdversarialKinematicProfile(CoreasonBaseState):
    """
    AGENT INSTRUCTION: AdversarialKinematicProfile is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    stochastic_noise_variance (ge=0.0, le=1.0), bezier_complexity_ceiling (ge=2, le=100),
    error_injection_probability (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    stochastic_noise_variance: float = Field(
        ge=0.0,
        le=1.0,
        description="The magnitude of fractional Brownian motion or Perlin noise applied to the spline.",
    )
    bezier_complexity_ceiling: int = Field(
        ge=2,
        le=100,
        description="The maximum number of control points the generator is authorized to output for a single movement.",
    )
    keystroke_cadence: DistributionProfile = Field(
        description="The exact probability density function governing $\\Delta t$ delays between keystrokes."
    )
    error_injection_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="The probability of the neural engine intentionally generating an overshoot, transposition error, or backspace correction.",  # noqa: E501
    )


class AgentNodeProfile(BaseNodeProfile):
    """
    AGENT INSTRUCTION: AgentNodeProfile is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on description (max_length=2000), action_space_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); constrained by @model_validator hooks (sort_agent_node_arrays)
    for exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    description: str = Field(
        max_length=2000,
        description="The semantic boundary defining the objective function of the execution node. [SITD-Gamma: Neurosymbolic Substrate Alignment]",  # noqa: E501
    )
    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    mcts_navigation_policy: MonteCarloTreeSearchPolicy | None = Field(
        default=None, description="The policy governing multi-hop UI navigation via latent tree search."
    )
    token_merging: TokenMergingPolicy | None = Field(default=None)
    extraction_policy: EpistemicExtractionPolicy | None = Field(default=None)
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
    kinematic_emulation_policy: AdversarialKinematicProfile | None = Field(
        default=None,
        description="The mathematical constraints for generating adversarial pointer physics and human-like cadence.",
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
    AGENT INSTRUCTION: BaseTopologyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: lifecycle_phase; intrinsic Pydantic limits on epistemic_enforcement (le=1000000000),
    architectural_intent (max_length=2000), justification (max_length=2000). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CouncilTopologyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; constrained by @model_validator hooks (enforce_funded_byzantine_slashing, check_adjudicator_id)
    for exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: DAGTopologyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on max_depth (ge=1, le=256), max_fan_out (ge=1, le=1024); constrained
    by @model_validator hooks (sort_dag_topology_arrays, verify_edges_exist) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: DigitalTwinTopologyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on target_topology_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: EvaluatorOptimizerTopologyManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on max_revision_loops (le=1000000000, ge=1); constrained by
    @model_validator hooks (verify_bipartite_nodes) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: EvolutionaryTopologyManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on generations (le=1.0), population_size (le=1000000000); constrained
    by @model_validator hooks (sort_objectives) for exact graph determinism. All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: SMPCTopologyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, smpc_protocol; intrinsic Pydantic limits on joint_function_uri (max_length=2000),
    participant_node_ids (min_length=2). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: SwarmTopologyManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on spawning_threshold (ge=1, le=100), max_concurrent_agents (le=100);
    constrained by @model_validator hooks (enforce_concurrency_ceiling, sort_arrays) for exact graph determinism.
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: AdversarialMarketTopologyManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on blue_team_ids (min_length=1), red_team_ids (min_length=1);
    constrained by @model_validator hooks (verify_disjoint_sets, sort_arrays) for exact graph determinism. All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: ConsensusFederationTopologyManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on participant_ids (min_length=3); constrained by @model_validator
    hooks (verify_adjudicator_isolation, sort_arrays) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: WorkflowManifest is a declarative and frozen snapshot representing N-dimensional geometry
    at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on tenant_id
    (min_length=1, pattern='^[a-zA-Z0-9_.:-]+$', max_length=255), session_id (min_length=1,
    pattern='^[a-zA-Z0-9_.:-]+$', max_length=255), global_system_prompt_hash (min_length=64, max_length=64,
    pattern='^[a-f0-9]{64}$'); constrained by @model_validator hooks (sort_arrays) for exact graph determinism.
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    global_system_prompt_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern="^[a-f0-9]{64}$",
        description="The SHA-256 Merkle root of the master non-monotonic instruction set.",
    )
    global_observability: ObservabilityPolicy | None = Field(
        default=None, description="The overarching OpenTelemetry rules for the entire swarm graph."
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
    AGENT INSTRUCTION: WetwareAttestationContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on did_subject
    (pattern='^did:[a-z0-9]+:.*$'), cryptographic_payload (pattern='^[A-Za-z0-9+/=_-]+$'). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: InterventionReceipt is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on feedback (max_length=2000); constrained by @model_validator hooks
    (verify_attestation_nonce) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    """
    AGENT INSTRUCTION: EpistemicQuarantineSnapshot is an exact topological boundary enforcing strict capability
    parameters and physical execution state.

    CAUSAL AFFORDANCE: Resolves graph constraints and unlocks specific spatial operations or API boundaries.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on system_prompt
    (max_length=2000), active_context (le=1000000000); constrained by @model_validator hooks (sort_arrays) for
    exact graph determinism. All field limits must be strictly validated at instantiation to prevent epistemic
    contagion.

    MCP ROUTING TRIGGERS: DAG Routing, Topographical Component, Capability Definition, Semantic Anchor
    """

    active_information_state: "InformationStateManifest | None" = Field(
        default=None, description="The continuous POMDP epistemic coordinate currently driving active inference."
    )
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
    """
    AGENT INSTRUCTION: ZeroKnowledgeReceipt is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: proof_protocol; intrinsic Pydantic limits on public_inputs_hash (min_length=1, max_length=128,
    pattern='^[a-f0-9]{64}$'), verifier_key_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    cryptographic_blob (max_length=5000000), latent_state_commitments (le=1000000000). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    """
    AGENT INSTRUCTION: BeliefMutationEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on uncertainty_profile (le=1000000000); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism; enforced via @field_validator structural
    bounds (enforce_payload_topology). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    """
    AGENT INSTRUCTION: ObservationEvent is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on triggering_invocation_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'); enforced via @field_validator structural bounds (enforce_payload_topology). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

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
    AGENT INSTRUCTION: EpistemicTelemetryEvent is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type, interaction_modality; intrinsic Pydantic limits on target_node_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), dwell_duration_ms (le=86400000, ge=0). All field limits must be strictly
    validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: EpistemicAxiomState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    source_concept_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), target_concept_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'). All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    source_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of the origin node."
    )
    directed_edge_type: OBORelationEdge = Field(description="The topological relationship.")
    target_concept_id: str = Field(
        min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$", description="CID of destination node."
    )


class EpistemicSeedInjectionPolicy(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicSeedInjectionPolicy is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    similarity_threshold_alpha (ge=0.0, le=1.0), relation_diversity_bucket_size (le=1000000000, gt=0). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    similarity_threshold_alpha: float = Field(ge=0.0, le=1.0)
    relation_diversity_bucket_size: int = Field(le=1000000000, gt=0)


class EpistemicChainGraphState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicChainGraphState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on chain_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), syntactic_roots (min_length=1); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CognitivePredictionReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on source_chain_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), target_source_concept (max_length=2000), predicted_top_k_tokens (min_length=1).
    All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    type: Literal["cognitive_prediction"] = Field(default="cognitive_prediction")
    source_chain_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    target_source_concept: str = Field(max_length=2000)
    predicted_top_k_tokens: list[Annotated[str, StringConstraints(max_length=255)]] = Field(min_length=1)


class EpistemicAxiomVerificationReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: EpistemicAxiomVerificationReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on source_prediction_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), sequence_similarity_score (ge=0.0, le=1.0); constrained by @model_validator
    hooks (enforce_epistemic_quarantine) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    type: Literal["epistemic_axiom_verification"] = Field(default="epistemic_axiom_verification")
    source_prediction_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    sequence_similarity_score: float = Field(ge=0.0, le=1.0)
    fact_score_passed: bool
    tripped_falsification_condition_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="The specific condition_id from a FalsificationContract that this axiom mathematically violated.",
    )

    @model_validator(mode="after")
    def enforce_epistemic_quarantine(self) -> Self:
        if not self.fact_score_passed:
            raise ValueError("Epistemic Contagion Prevented: Axioms failing validation cannot be verified.")
        return self


class EpistemicDomainGraphManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicDomainGraphManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on graph_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), verified_axioms (min_length=1); constrained by
    @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: EpistemicTopologicalProofManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on proof_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), axiomatic_chain (min_length=1). All field limits
    must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    """
    AGENT INSTRUCTION: CognitiveSamplingPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    max_complexity_hops (le=1000000000, ge=1), inverse_frequency_smoothing_epsilon (le=1.0). All field limits must
    be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
    """

    max_complexity_hops: int = Field(le=1000000000, ge=1, description="The absolute physical limit on path length N.")
    inverse_frequency_smoothing_epsilon: float = Field(
        le=1.0, default=1.0, description="The epsilon constant ensuring unsampled nodes are mathematically prioritized."
    )


class CognitiveReasoningTraceState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: CognitiveReasoningTraceState is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on trace_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), source_proof_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), token_length (le=1000000000, ge=0), trace_payload (max_length=100000). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CognitiveDualVerificationReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are constrained by @model_validator hooks
    (enforce_dual_key_lock) for exact graph determinism. All field limits must be strictly validated at
    instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    primary_verifier_id: NodeIdentifierState = Field(description="The DID of the primary evaluating agent.")
    secondary_verifier_id: NodeIdentifierState = Field(
        description="The DID of the independent secondary evaluating agent."
    )
    trace_factual_alignment: bool = Field(
        description="Strict Boolean indicating if BOTH agents mathematically agree on factual alignment."
    )
    adjudicator_escalation_id: NodeIdentifierState | None = Field(
        default=None,
        description="The deterministic tie-breaker node (e.g., a more powerful model or human oversight) invoked if the primary and secondary verifiers disagree.",  # noqa: E501
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
    AGENT INSTRUCTION: EpistemicGroundedTaskManifest is a declarative and frozen snapshot representing
    N-dimensional geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on task_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), vignette_payload (max_length=100000). All field
    limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: EpistemicCurriculumManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on curriculum_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), tasks (min_length=1); constrained by
    @model_validator hooks (sort_tasks) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
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
    AGENT INSTRUCTION: CognitiveFormatContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    final_answer_regex (max_length=2000). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: EpistemicRewardModelPolicy is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on policy_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), reference_graph_id (min_length=1,
    max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), beta_path_weight (le=1.0, ge=0.0). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: CognitiveRewardEvaluationReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on source_generation_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), calculated_r_path (ge=0.0, le=1.0), total_advantage_score (le=100.0);
    constrained by @model_validator hooks (sort_arrays) for exact graph determinism. All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: CognitiveDetailedBalanceContract is a rigid mathematical boundary enforcing systemic
    constraints globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on
    target_balance_epsilon (le=1.0, ge=0.0), flow_estimation_model (max_length=2000), local_exploration_k (le=1.0,
    gt=0). All field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: EpistemicFlowStateReceipt is a mathematically defined coordinate on the Merkle-DAG
    representing an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on source_trajectory_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), estimated_flow_value (le=1000000000.0, ge=0.0). All field limits must be
    strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
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
    AGENT INSTRUCTION: TopologicalRewardContract is a rigid mathematical boundary enforcing systemic constraints
    globally. Dictates execution limits and mathematical thresholds.

    CAUSAL AFFORDANCE: Enforces rigid isolation perimeters and limits subgraph generation.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: aggregation_method; intrinsic Pydantic limits on min_link_criticality_score (ge=0.0, le=1.0),
    min_semantic_relevance_score (ge=0.0, le=1.0). All field limits must be strictly validated at instantiation to
    prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Mathematical Boundary, Slashing Penalty, Truth Maintenance, Systemic Perimeter
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
    AGENT INSTRUCTION: DifferentiableLogicConstraint is an exact topological boundary enforcing strict capability
    parameters and physical execution state.

    CAUSAL AFFORDANCE: Resolves graph constraints and unlocks specific spatial operations or API boundaries.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on constraint_id
    (max_length=128, pattern='^[a-zA-Z0-9_.:-]+$', min_length=1), formal_syntax_smt (max_length=2000),
    relaxation_epsilon (le=1.0, ge=0.0). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: DAG Routing, Topographical Component, Capability Definition, Semantic Anchor
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
    anomaly_classification: IEEEAnomalyClass
    solver_status: SMTSolverOutcome = Field(default="unknown")


class InformationStateManifest(CoreasonBaseState):
    """
    AGENT INSTRUCTION: InformationStateManifest is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on manifest_id
    (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'); enforced via @field_validator structural bounds
    (validate_working_context_variables). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

    manifest_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID).",
    )
    latent_trajectory: LatentIntentTrajectoryState = Field(description="The continuous POMDP belief distribution.")
    transition_matrix: EpistemicTransitionMatrixProfile = Field(description="SOTA HMM matrix.")
    negative_constraints: NegativeHeuristicProfile | None = Field(
        default=None, description="Rigid symbolic constraint ledger."
    )
    working_context_variables: dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState] = Field(
        description="SOTA Slot-filling memory."
    )

    @field_validator("working_context_variables", mode="before")
    @classmethod
    def validate_working_context_variables(cls, v: Any) -> Any:
        return _validate_payload_bounds(v)


class IntentTransitionEvent(BaseStateEvent):
    """
    AGENT INSTRUCTION: IntentTransitionEvent is a mathematically defined coordinate on the Merkle-DAG representing
    an immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on previous_state_hash (max_length=128, pattern='^[a-f0-9]{64}$'). All
    field limits must be strictly validated at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    type: Literal["intent_transition"] = Field(default="intent_transition", description="Discriminator type.")
    previous_state_hash: str | None = Field(
        default=None,
        max_length=128,
        pattern="^[a-f0-9]{64}$",
        description="Cryptographic link to the prior POMDP belief state.",
    )
    active_information_state: InformationStateManifest = Field(description="The current information state.")


class MDPTransitionEvent(BaseStateEvent):
    """
    AGENT INSTRUCTION: MDPTransitionEvent is a mathematically defined coordinate on the Merkle-DAG representing an
    immutable historical fact. Initializes as a frozen state vector.

    CAUSAL AFFORDANCE: Appends a frozen historical point to the epistemic ledger, mutating the state graph.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are strictly bounded categorical literals on
    fields: type; intrinsic Pydantic limits on source_state_event_id (min_length=1, max_length=128,
    pattern='^[a-zA-Z0-9_.:-]+$'), action_event_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'),
    resulting_state_event_id (min_length=1, max_length=128, pattern='^[a-zA-Z0-9_.:-]+$'), reward_signal
    (ge=-1000000000.0, le=1000000000.0). All field limits must be strictly validated at instantiation to prevent
    epistemic contagion.

    MCP ROUTING TRIGGERS: Append-Only Ledger, Merkle-DAG Coordinate, Cryptographic Receipt, Epistemic History
    """

    type: Literal["mdp_transition"] = Field(default="mdp_transition")
    source_state_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="CID pointing to the prior BrowserDOMState or ViewportRasterState.",
    )
    action_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="CID pointing to the executed ToolInvocationEvent or SpatialKinematicActionIntent.",
    )
    resulting_state_event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="CID pointing to the new, post-action BrowserDOMState or ViewportRasterState.",
    )
    reward_signal: float = Field(
        ge=-1000000000.0,
        le=1000000000.0,
        description="The actual dense or sparse reward emitted by the environment or PRM after the transition.",
    )
    is_terminal: bool = Field(description="Flags if this transition explicitly concluded the multi-hop trajectory.")


class SymbolicExecutionReceipt(BaseStateEvent):
    """
    AGENT INSTRUCTION: The immutable cryptographic log of a deterministic script execution.
    Provides the mathematical proof of success required to promote a script to an EpistemicSOPManifest.
    """

    type: Literal["symbolic_execution"] = Field(
        default="symbolic_execution", description="Discriminator type for a symbolic execution receipt."
    )
    handoff_contract_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="CID linking back to the NeuroSymbolicHandoffContract.",
    )
    execution_duration_ms: int = Field(
        ge=0,
        le=86400000,
        description="The physical computation duration in milliseconds.",
    )
    halting_state: Literal["success", "timeout", "memory_exhaustion", "runtime_error", "schema_mismatch"] = Field(
        description="The definitive deterministic outcome of the compilation/execution."
    )
    extracted_payload: JsonPrimitiveState | None = Field(
        default=None,
        description="The resulting structured data, if halting_state is 'success'.",
    )

    @field_validator("extracted_payload", mode="before")
    def _validate_payload(cls, v: JsonPrimitiveState | None) -> JsonPrimitiveState | None:  # noqa: N805
        if v is None:
            return None
        return _validate_payload_bounds(v)

    @model_validator(mode="after")
    def _sort_payload(self) -> Self:
        # We sort top-level dict to ensure Cryptographic Determinism.
        if isinstance(self.extracted_payload, dict):
            object.__setattr__(
                self,
                "extracted_payload",
                dict(sorted(self.extracted_payload.items(), key=lambda x: x[0])),
            )
        return self


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
    | CausalExplanationEvent
    | IntentTransitionEvent
    | MDPTransitionEvent
    | SymbolicExecutionReceipt,
    Field(discriminator="type", description="A discriminated union of state events."),
]


class EpistemicLedgerState(CoreasonBaseState):
    """
    AGENT INSTRUCTION: EpistemicLedgerState is a declarative and frozen snapshot representing N-dimensional
    geometry at a specific point in time. Structurally projects active coordinates.

    CAUSAL AFFORDANCE: Provides the baseline descriptive geometry and frozen boundaries for downstream workflow
    traversal.

    EPISTEMIC BOUNDS: The absolute mathematical and physical limits are intrinsic Pydantic limits on history
    (max_length=10000), checkpoints (max_length=1000000000), truth_maintenance_policy (le=1000000000),
    active_concept_bottlenecks (max_length=1000), active_extraction_policies (max_length=1000); constrained by
    @model_validator hooks (sort_history) for exact graph determinism. All field limits must be strictly validated
    at instantiation to prevent epistemic contagion.

    MCP ROUTING TRIGGERS: Declarative Geometry, Spatial Coordinate, N-Dimensional Snapshot, Topology Profile
    """

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
    active_concept_bottlenecks: dict[NodeIdentifierState, ConceptBottleneckPolicy] = Field(
        default_factory=dict,
        max_length=1000,
        description="Active XAI routing constraints currently locking the execution graph, mapped to specific agent DIDs.",  # noqa: E501
    )
    active_extraction_policies: dict[NodeIdentifierState, EpistemicExtractionPolicy] = Field(
        default_factory=dict,
        max_length=1000,
        description="Active hardware extraction rules governing the current ingestion cycle, mapped to specific agent DIDs.",  # noqa: E501
    )

    @model_validator(mode="after")
    def sort_history(self) -> Self:
        object.__setattr__(self, "history", sorted(self.history, key=lambda event: event.timestamp))
        object.__setattr__(self, "checkpoints", sorted(self.checkpoints, key=lambda x: x.checkpoint_id))
        object.__setattr__(self, "active_rollbacks", sorted(self.active_rollbacks, key=lambda x: x.request_id))
        object.__setattr__(self, "migration_contracts", sorted(self.migration_contracts, key=lambda x: x.contract_id))
        object.__setattr__(self, "active_cascades", sorted(self.active_cascades, key=lambda x: x.cascade_id))
        # AGENT INSTRUCTION: NEW SORTING LOGIC INJECTED HERE
        object.__setattr__(self, "active_concept_bottlenecks", dict(sorted(self.active_concept_bottlenecks.items())))
        object.__setattr__(self, "active_extraction_policies", dict(sorted(self.active_extraction_policies.items())))
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
IntentClassificationReceipt.model_rebuild()
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
DefeasibleRebuttalContract.model_rebuild()
TruthMaintenancePolicy.model_rebuild()
ProcessRewardContract.model_rebuild()
CanonicalGroundingReceipt.model_rebuild()
EpistemicExtractionPolicy.model_rebuild()
SemanticNodeState.model_rebuild()
AgentNodeProfile.model_rebuild()
IntentTransitionEvent.model_rebuild()
InformationStateManifest.model_rebuild()
ConceptBottleneckPolicy.model_rebuild()
PredictiveEntropySLA.model_rebuild()
StreamInterruptionPolicy.model_rebuild()
TokenMergingPolicy.model_rebuild()
InformationFlowPolicy.model_rebuild()
VisualAffordancePatchState.model_rebuild()
ViewportRasterState.model_rebuild()
DecomposedSubQueryState.model_rebuild()
QueryDecompositionManifest.model_rebuild()
AdversarialKinematicProfile.model_rebuild()
BrowserFingerprintManifest.model_rebuild()
MonteCarloTreeSearchPolicy.model_rebuild()
MDPTransitionEvent.model_rebuild()
ActionSpaceManifest.model_rebuild()
EpistemicLedgerState.model_rebuild()
WorkflowManifest.model_rebuild()
ProgramSynthesisIntent.model_rebuild()
SymbolicExecutionReceipt.model_rebuild()
SemanticGapAnalysisProfile.model_rebuild()
DeterministicExtractionContract.model_rebuild()
SemanticSlicingPolicy.model_rebuild()
EpistemicTransmutationTask.model_rebuild()
NetworkInterceptState.model_rebuild()
MemoryHeapSnapshot.model_rebuild()
SchemaInferenceIntent.model_rebuild()
