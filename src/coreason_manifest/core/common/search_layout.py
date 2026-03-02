# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.highlighting import HighlightConfig
from coreason_manifest.core.common.templating import ParameterizedDataRef
from coreason_manifest.core.common.transform import DataTransformSchema
from coreason_manifest.core.common.typeahead import TypeaheadConfig


class PartitionType(StrEnum):
    SEMANTIC_THOUGHT = "SEMANTIC_THOUGHT"
    GENERATIVE_ANSWER = "GENERATIVE_ANSWER"
    LEXICAL_RESULTS = "LEXICAL_RESULTS"
    CITATION_CARDS = "CITATION_CARDS"


class LayoutPartitionConfig(CoreasonModel):
    flex_ratio: int = Field(default=1, description="The CSS flex-grow ratio for desktop side-by-side rendering.")
    mobile_stack_order: int = Field(default=1, description="The vertical rendering order on small screens.")

    @model_validator(mode="after")
    def validate_layout(self) -> "LayoutPartitionConfig":
        if self.flex_ratio < 1:
            raise ValueError("flex_ratio must be strictly >= 1")
        if self.mobile_stack_order < 0:
            raise ValueError("mobile_stack_order must be >= 0")
        return self


class SearchPartitionNode(CoreasonModel):
    target_node_id: str = Field(
        ..., description="The unique DOM/Widget ID. Essential for SSE multiplexing to target this specific zone."
    )
    partition_type: PartitionType
    layout: LayoutPartitionConfig = Field(default_factory=LayoutPartitionConfig)
    data_ref: ParameterizedDataRef | None = Field(
        default=None, description="Reactive data source for this partition (e.g., for Lexical Results)."
    )
    transform: DataTransformSchema | None = Field(
        default=None, description="Edge-computed filtering/sorting rules for this partition's data."
    )
    highlighting: HighlightConfig | None = Field(
        default=None, description="Client-side highlighting rules (e.g., highlighting search terms in Citation Cards)."
    )


class HybridSearchLayout(CoreasonModel):
    search_bar_typeahead: TypeaheadConfig | None = Field(
        default=None, description="Fast-path autocomplete configuration for the global search input."
    )
    partitions: list[SearchPartitionNode] = Field(
        ..., description="The UI zones that make up the hybrid search interface."
    )

    @model_validator(mode="after")
    def validate_unique_node_ids(self) -> "HybridSearchLayout":
        node_ids = set()
        for partition in self.partitions:
            if partition.target_node_id in node_ids:
                raise ValueError(f"Duplicate target_node_id found: '{partition.target_node_id}'")
            node_ids.add(partition.target_node_id)
        return self
