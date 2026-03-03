# Prosperity-3.0
from typing import Literal

from pydantic import BaseModel, Field

from coreason_manifest.workflow.nodes.base import Constraint
from coreason_manifest.workflow.nodes.oversight import InspectorNodeBase


class MultimodalConstraint(Constraint):
    """Multimodal constraint requiring visual context."""

    requires_visual_context: bool = Field(True, description="Whether this constraint requires visual context.")
    source_text_reference: str = Field(..., description="The text claim the image must visually satisfy.")


class VisBenchRubricConfig(BaseModel):
    """Rubrics for VLM-as-a-Judge multimodal evaluation."""

    check_alignment: bool = Field(True, description="Check visual alignment.")
    check_text_readability: bool = Field(True, description="Check text readability.")
    check_spatial_overlap: bool = Field(True, description="Check spatial overlap.")
    check_hallucinations: bool = Field(True, description="Check for hallucinations.")


class VisualInspectorNode(InspectorNodeBase):
    """A node that applies visual rubrics to an artifact."""

    type: Literal["visual_inspector"] = Field(
        "visual_inspector", description="The type of the node.", examples=["visual_inspector"]
    )

    is_security_guard: Literal[True] = Field(
        True, description="Indicates this node acts as a valid cryptographic barrier for high-risk execution."
    )

    rubrics: VisBenchRubricConfig = Field(
        default_factory=VisBenchRubricConfig, description="The visual rubrics to apply."
    )

    target_artifact_key: str = Field(
        ..., description="The state key where the rendering agent stored the image/SVG URL"
    )
