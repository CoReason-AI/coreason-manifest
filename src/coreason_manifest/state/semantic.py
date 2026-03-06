# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID

type MemoryTier = Literal["working", "episodic", "semantic"]


class SpatialAnchor(CoreasonBaseModel):
    page_number: int | None = Field(default=None, description="The physical page or slide number.")
    bounding_box: tuple[float, float, float, float] | None = Field(
        default=None, description="The strictly typed [x_min, y_min, x_max, y_max] coordinate matrix."
    )
    block_type: Literal["paragraph", "table", "figure", "footnote", "header"] | None = Field(
        default=None, description="The structural classification of the source region."
    )


type CausalInterval = Literal["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]


class VectorEmbedding(CoreasonBaseModel):
    vector: list[float] = Field(description="The raw high-dimensional floating-point array.")
    dimensionality: int = Field(description="The size of the vector array.")
    model_name: str = Field(description="The provenance of the embedding model used (e.g., 'text-embedding-3-large').")

    @model_validator(mode="after")
    def verify_dimensionality(self) -> Any:
        if len(self.vector) != self.dimensionality:
            raise ValueError(f"Dimensionality mismatch: expected {self.dimensionality}, got {len(self.vector)}")
        return self


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


class MemoryProvenance(CoreasonBaseModel):
    extracted_by: NodeID = Field(description="The ID of the agent node that extracted this memory.")
    source_event_id: str = Field(description="The exact event ID in the EpistemicLedger that generated this fact.")
    spatial_anchor: SpatialAnchor | None = Field(
        default=None, description="The physical coordinate matrix where this data was extracted."
    )


class SalienceProfile(CoreasonBaseModel):
    baseline_importance: float = Field(description="The starting importance score of this memory from 0.0 to 1.0.")
    decay_rate: float = Field(description="The rate at which this memory's relevance decays over time.")


class SemanticNode(CoreasonBaseModel):
    node_id: str = Field(description="The unique identifier of this semantic concept.")
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
        default=None, description="The dense vector representation of the text chunk."
    )
    provenance: MemoryProvenance = Field(description="The cryptographic chain of custody for this memory.")
    tier: MemoryTier = Field(default="semantic", description="The cognitive tier this memory resides in.")
    temporal_bounds: TemporalBounds | None = Field(
        default=None, description="The time window during which this node is considered valid."
    )
    salience: SalienceProfile | None = Field(
        default=None, description="The importance profile used for memory pruning."
    )


class SemanticEdge(CoreasonBaseModel):
    edge_id: str = Field(description="The unique identifier of this relationship.")
    subject_node_id: str = Field(description="The origin SemanticNode ID.")
    object_node_id: str = Field(description="The destination SemanticNode ID.")
    confidence_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="The probabilistic certainty of this logical connection."
    )
    predicate: str = Field(description="The string representation of the relationship (e.g., 'WORKS_FOR').")
    embedding: VectorEmbedding | None = Field(
        default=None, description="The dense vector representing the relationship semantics."
    )
    provenance: MemoryProvenance | None = Field(
        default=None,
        description="Optional distinct provenance if the relationship was inferred separately from the nodes.",
    )
    temporal_bounds: TemporalBounds | None = Field(
        default=None, description="The time window during which this relationship holds true."
    )
