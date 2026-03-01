# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class VisInformationType(str, Enum):  # noqa: UP042
    QUALITATIVE_SCHEMATIC = "QUALITATIVE_SCHEMATIC"
    QUANTITATIVE_STATISTICAL = "QUANTITATIVE_STATISTICAL"
    SPATIAL_GEOMETRIC = "SPATIAL_GEOMETRIC"
    HYBRID_META = "HYBRID_META"


class SciVisIntent(BaseModel):
    vis_type: VisInformationType
    requires_code_execution: bool = Field(
        description="Indicates if code execution is required for exact numerics (e.g., Matplotlib)."
    )
    requires_vector_layout: bool = Field(
        description="Indicates if vector layout is required for SVG/mxGraph hierarchy."
    )


class GraphicElement(BaseModel):
    id: str
    semantic_role: str
    proposed_shape: str


class FunctionalModule(BaseModel):
    module_id: str
    title: str
    elements: list[GraphicElement]


class InterModuleConnection(BaseModel):
    source_module_id: str
    target_module_id: str
    label: str
    flow_type: str


class HierarchicalBlueprint(BaseModel):
    modules: list[FunctionalModule]
    connections: list[InterModuleConnection]
    aspect_ratio_preference: str

    @model_validator(mode="after")
    def validate_connections(self) -> "HierarchicalBlueprint":
        module_ids = {module.module_id for module in self.modules}
        for connection in self.connections:
            if connection.source_module_id not in module_ids:
                raise ValueError(f"source_module_id '{connection.source_module_id}' not found in modules.")
            if connection.target_module_id not in module_ids:
                raise ValueError(f"target_module_id '{connection.target_module_id}' not found in modules.")
        return self


class SpatialCorrection(BaseModel):
    target_element_id: str
    issue: Literal["overlap", "out_of_bounds", "misaligned", "poor_contrast"]
    suggested_action: str


class VisualCriticFeedback(BaseModel):
    is_publication_ready: bool
    hallucinated_elements: list[str]
    missing_required_elements: list[str]
    readability_issues: list[str]
    spatial_corrections: list[SpatialCorrection]
    global_aesthetic_score: float = Field(ge=0, le=10)


class VectorRenderPayload(BaseModel):
    format: Literal["svg", "mxgraph_xml", "tikz", "mcp_visio_trace"]
    source_code: str
    interaction_steps: int
    raster_preview_url: str | None = None
