# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable semantic knowledge schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from typing import Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID

type MemoryTier = Literal["working", "episodic", "semantic"]


class MultimodalArtifact(CoreasonBaseModel):
    """AGENT INSTRUCTION: The root Genesis Block for an unstructured document entering the Merkle-DAG."""

    artifact_id: str = Field(description="The definitive Content Identifier (CID) bounding the raw file.")
    mime_type: str = Field(description="Strict MIME typing of the source artifact (e.g., 'application/pdf').")
    byte_stream_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$", description="The undeniable SHA-256 hash of the pre-transmutation byte stream."
    )
    temporal_ingest_timestamp: float = Field(description="The UNIX timestamp anchoring the genesis block.")


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
                    f"Spatial invariant violated: min bounds (x:{x_min}, y:{y_min}) "
                    f"exceed max bounds (x:{x_max}, y:{y_max})"
                )
        return self


type CausalInterval = Literal["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]


class DimensionalProjectionContract(CoreasonBaseModel):
    source_model_name: str = Field(description="The native embedding model of the origin agent.")
    target_model_name: str = Field(description="The native embedding model of the destination agent.")
    projection_matrix_hash: str = Field(
        description="The SHA-256 hash of the exact mathematical matrix used to "
        "compress or translate the latent dimensions."
    )
    isometry_preservation_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Mathematical proof (e.g., Earth Mover's Distance preservation) of "
        "how accurately relative semantic distances were maintained during projection.",
    )


class OntologicalHandshake(CoreasonBaseModel):
    handshake_id: str = Field(
        min_length=1,
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking "
            "this protocol handshake to the Merkle-DAG."
        ),
    )
    participant_node_ids: list[str] = Field(min_length=2, description="The agents establishing semantic alignment.")
    measured_cosine_similarity: float = Field(
        ge=-1.0,
        le=1.0,
        description="The calculated geometric alignment of the agents' core definitions.",
    )
    alignment_status: Literal["aligned", "projected", "fallback_triggered", "incommensurable"] = Field(
        description="The final verdict of the handshake protocol."
    )
    applied_projection: DimensionalProjectionContract | None = Field(
        default=None,
        description="The projection applied if the agents natively used different embedding dimensionalities.",
    )


class VectorEmbedding(CoreasonBaseModel):
    vector_base64: str = Field(
        pattern=r"^[A-Za-z0-9+/]*={0,2}$", max_length=5_000_000, description="The base64-encoded dense vector array."
    )
    dimensionality: int = Field(description="The size of the vector array.")
    model_name: str = Field(description="The provenance of the embedding model used (e.g., 'text-embedding-3-large').")


class TemporalBounds(CoreasonBaseModel):
    valid_from: float | None = Field(
        default=None, ge=0.0, description="The UNIX timestamp when this memory became true."
    )
    valid_to: float | None = Field(default=None, description="The UNIX timestamp when this memory was invalidated.")
    interval_type: CausalInterval | None = Field(
        default=None, description="The Allen's interval algebra or causal relationship classification."
    )

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Any:
        if self.valid_from is not None and self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to cannot be before valid_from")
        return self


class LineageWatermark(CoreasonBaseModel):
    watermark_protocol: Literal["merkle_dag", "statistical_token", "homomorphic_mac"] = Field(
        description="The mathematical methodology used to embed the chain of custody."
    )
    hop_signatures: dict[str, str] = Field(
        description=(
            "A dictionary mapping intermediate participant NodeIDs to their deterministic execution signatures."
        )
    )
    tamper_evident_root: str = Field(
        description=(
            "The overarching cryptographic hash (e.g., Merkle Root) proving "
            "the dataset has not been laundered or structurally modified."
        )
    )


class MemoryProvenance(CoreasonBaseModel):
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
        description=(
            "The cryptographic, tamper-evident chain of custody tracing this memory across multiple swarm hops."
        ),
    )


class SalienceProfile(CoreasonBaseModel):
    baseline_importance: float = Field(description="The starting importance score of this memory from 0.0 to 1.0.")
    decay_rate: float = Field(description="The rate at which this memory's relevance decays over time.")


class HomomorphicEncryptionProfile(CoreasonBaseModel):
    fhe_scheme: Literal["ckks", "bgv", "bfv", "tfhe"] = Field(
        description="The specific homomorphic encryption dialect used to encode the ciphertext."
    )
    public_key_id: str = Field(
        description=(
            "The Content Identifier (CID) of the public evaluation key the "
            "orchestrator must utilize to perform privacy-preserving geometric "
            "math on ciphertext without epistemic contamination."
        )
    )
    ciphertext_blob: str = Field(max_length=5_000_000, description="The base64-encoded homomorphic ciphertext.")


class SemanticNode(CoreasonBaseModel):
    node_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking "
            "this semantic node to the Merkle-DAG."
        )
    )
    label: str = Field(description="The categorical label of the node (e.g., 'Person', 'Concept').")
    scope: Literal["global", "tenant", "session"] = Field(
        default="session",
        description=(
            "The cryptographic namespace partitioning boundary. "
            "Global is public, Tenant is corporate, Session is ephemeral."
        ),
    )
    text_chunk: str = Field(max_length=50000, description="The raw natural language representation of the memory.")
    embedding: VectorEmbedding | None = Field(
        default=None,
        description=(
            "Topologically Bounded Latent Spaces used to calculate exact geometric distance "
            "and preserve structural Isometry."
        ),
    )
    provenance: MemoryProvenance = Field(description="The cryptographic chain of custody for this memory.")
    tier: MemoryTier = Field(default="semantic", description="The cognitive tier this memory resides in.")
    temporal_bounds: TemporalBounds | None = Field(
        default=None, description="The time window during which this node is considered valid."
    )
    salience: SalienceProfile | None = Field(
        default=None, description="The importance profile used for memory pruning."
    )
    fhe_profile: HomomorphicEncryptionProfile | None = Field(
        default=None,
        description=(
            "The cryptographic envelope enabling privacy-preserving computation "
            "directly on this node's encrypted state."
        ),
    )


class SemanticEdge(CoreasonBaseModel):
    edge_id: str = Field(
        description=(
            "A Content Identifier (CID) acting as a cryptographic Lineage Watermark linking "
            "this semantic edge to the Merkle-DAG."
        )
    )
    subject_node_id: str = Field(description="The origin SemanticNode Content Identifier (CID).")
    object_node_id: str = Field(description="The destination SemanticNode Content Identifier (CID).")
    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="The probabilistic certainty of this logical connection."
    )
    predicate: str = Field(description="The string representation of the relationship (e.g., 'WORKS_FOR').")
    embedding: VectorEmbedding | None = Field(
        default=None,
        description=(
            "Topologically Bounded Latent Spaces used to calculate exact geometric distance "
            "and preserve structural Isometry."
        ),
    )
    provenance: MemoryProvenance | None = Field(
        default=None,
        description="Optional distinct provenance if the relationship was inferred separately from the nodes.",
    )
    temporal_bounds: TemporalBounds | None = Field(
        default=None, description="The time window during which this relationship holds true."
    )
    causal_relationship: Literal["causes", "confounds", "correlates_with", "undirected"] = Field(
        default="undirected", description="The Pearlian directionality of the semantic relationship."
    )
