# Prosperity-3.0
from typing import Any

from pydantic import TypeAdapter

from coreason_manifest.core.workflow.nodes import AnyNode
from coreason_manifest.core.workflow.nodes.base import ConstraintOperator
from coreason_manifest.core.workflow.nodes.visual_oversight import (
    MultimodalConstraint,
    VisBenchRubricConfig,
    VisualInspectorNode,
)


def test_visual_inspector_node_schema_instantiation() -> None:
    """Test that default rubrics populate correctly upon initialization."""
    node = VisualInspectorNode(
        id="test_visual_node",
        target_variable="input_image",
        criteria="Check if the image matches the source text.",
        output_variable="inspection_result",
        target_artifact_key="rendered_image_url",
    )
    assert node.type == "visual_inspector"
    assert isinstance(node.rubrics, VisBenchRubricConfig)
    assert node.rubrics.check_alignment is True
    assert node.rubrics.check_text_readability is True
    assert node.rubrics.check_spatial_overlap is True
    assert node.rubrics.check_hallucinations is True
    assert node.target_artifact_key == "rendered_image_url"


def test_visual_inspector_node_polymorphic_deserialization() -> None:
    """Test polymorphic deserialization through AnyNode."""
    raw_data = {
        "type": "visual_inspector",
        "id": "test_critic",
        "target_variable": "input_img",
        "criteria": "Check alignment",
        "output_variable": "is_aligned",
        "target_artifact_key": "artifact_1",
    }

    adapter: TypeAdapter[Any] = TypeAdapter(AnyNode)
    node = adapter.validate_python(raw_data)

    assert isinstance(node, VisualInspectorNode)
    assert node.id == "test_critic"
    assert node.target_artifact_key == "artifact_1"
    assert node.rubrics.check_alignment is True


def test_multimodal_constraint_instantiation() -> None:
    """Test instantiation of MultimodalConstraint to ensure coverage."""
    constraint = MultimodalConstraint(
        variable="image_content",
        operator=ConstraintOperator.EQ,
        value="expected_diagram",
        source_text_reference="The text claim.",
    )
    assert constraint.requires_visual_context is True
    assert constraint.source_text_reference == "The text claim."
