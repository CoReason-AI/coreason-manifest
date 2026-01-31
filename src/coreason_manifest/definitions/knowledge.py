# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import CoReasonBaseModel


class ArtifactType(str, Enum):
    """Enumeration of supported knowledge artifact types."""

    TEXT = "TEXT"
    TABLE = "TABLE"
    IMAGE = "IMAGE"
    MOLECULE = "MOLECULE"


class EnrichmentLevel(str, Enum):
    RAW = "RAW"  # Just content (from Refinery)
    TAGGED = "TAGGED"  # Has entities (from Tagger)
    LINKED = "LINKED"  # Entities linked to Ontology (from Codex)


class KnowledgeArtifact(CoReasonBaseModel):
    """
    The Universal 'Atom' of Knowledge.
    This is the contract that Refinery produces and Cortex consumes.
    It serves as the 'Shared Kernel' between ingestion and reasoning domains.
    """

    # Identity & Content
    id: str = Field(..., description="Deterministic hash of content + source")
    content: str = Field(..., description="The markdown representation of the knowledge")
    artifact_type: ArtifactType = Field(default=ArtifactType.TEXT, description="The semantic type of the content")

    # Lineage (The "Where")
    source_urn: str = Field(..., description="URN of the source file (e.g., urn:s3:bucket/file.pdf)")
    source_location: Dict[str, Any] = Field(
        default_factory=dict, description="Pointer to location (page_number, bbox, slide_index)"
    )

    # Semantics (The "Meaning")
    vector: Optional[List[float]] = Field(
        default=None, description="Embedding vector (optional, can be computed late-bound)"
    )
    tags: List[str] = Field(default_factory=list, description="Semantic tags or entities")

    entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Structured entities extracted by Coreason Tagger (Service B)",
    )

    enrichment_level: EnrichmentLevel = Field(
        default=EnrichmentLevel.RAW,
        description="Quality gate status. Service A produces RAW; API promotes to TAGGED.",
    )

    # Access Control (The "Who")
    sensitivity: str = Field(default="INTERNAL", description="Data sensitivity level")
