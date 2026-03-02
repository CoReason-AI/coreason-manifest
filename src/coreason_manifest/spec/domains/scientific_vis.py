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
from pydantic_core import PydanticCustomError

from coreason_manifest.spec.domains.scivis_templates import ComponentTemplate


class VisInformationType(str, Enum):  # noqa: UP042
    """
    Taxonomy for scientific visualization types.
    """

    QUALITATIVE_SCHEMATIC = "QUALITATIVE_SCHEMATIC"
    QUANTITATIVE_STATISTICAL = "QUANTITATIVE_STATISTICAL"
    SPATIAL_GEOMETRIC = "SPATIAL_GEOMETRIC"
    HYBRID_META = "HYBRID_META"


class SciVisIntent(BaseModel):
    vis_type: VisInformationType = Field(
        ...,
        description="Classify the scientific visualization type based on the MECE taxonomy.",
        examples=[VisInformationType.QUALITATIVE_SCHEMATIC, VisInformationType.QUANTITATIVE_STATISTICAL],
    )
    requires_code_execution: bool = Field(
        description="Indicates if code execution is required for exact numerics (e.g., Matplotlib)."
    )
    requires_vector_layout: bool = Field(
        description="Indicates if vector layout is required for SVG/mxGraph hierarchy."
    )


class GraphicElement(BaseModel):
    id: str
    semantic_role: str
    proposed_shape: Literal["rectangle", "cylinder", "document", "none"]


class FunctionalModule(BaseModel):
    module_id: str
    title: str
    elements: list[GraphicElement]
    template_reference: ComponentTemplate | None = Field(
        default=None,
        description="If provided, the execution engine loads this URN. The 'elements' list can be left empty.",
    )


class InterModuleConnection(BaseModel):
    source_module_id: str
    target_module_id: str
    label: str | None = None
    flow_type: Literal["sequential", "feedback", "bidirectional"]
    source_port: str | None = Field(default=None, description="The specific egress port on the source template/module.")
    target_port: str | None = Field(
        default=None, description="The specific ingress port on the target template/module."
    )


class HierarchicalBlueprint(BaseModel):
    modules: list[FunctionalModule]
    connections: list[InterModuleConnection]
    aspect_ratio_preference: Literal["16:9", "4:3", "1:1"]

    @model_validator(mode="after")
    def validate_connections(self) -> "HierarchicalBlueprint":
        module_ids = {module.module_id for module in self.modules}
        for connection in self.connections:
            if connection.source_module_id not in module_ids:
                raise PydanticCustomError(
                    "hallucinated_module_reference",
                    'Module ID "{invalid_id}" does not exist in the declared modules list.',
                    {"invalid_id": connection.source_module_id},
                )
            if connection.target_module_id not in module_ids:
                raise PydanticCustomError(
                    "hallucinated_module_reference",
                    'Module ID "{invalid_id}" does not exist in the declared modules list.',
                    {"invalid_id": connection.target_module_id},
                )
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
    provenance_manifest_reference: str | None = Field(
        default=None, description="Pointer to the C2PA ProvenanceManifest to be embedded in the SVG metadata."
    )
