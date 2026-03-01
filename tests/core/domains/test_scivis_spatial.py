import json

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.core.domains.scivis_spatial import (
    BoundingBox,
    LayoutDirection,
    PaddingConfig,
    RelativeConstraint,
    RoutingAlgorithm,
    SpatialLayoutBlueprint,
    SpatialRelation,
)


@given(
    st.builds(
        SpatialLayoutBlueprint,
        primary_direction=st.sampled_from(LayoutDirection),
        fallback_directions=st.lists(st.sampled_from(LayoutDirection)),
        edge_routing=st.sampled_from(RoutingAlgorithm),
        constraints=st.lists(
            st.builds(
                RelativeConstraint,
                target_id=st.text(min_size=1),
                relation=st.sampled_from(SpatialRelation),
                anchor_id=st.text(min_size=1),
                offset_mm=st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
            )
        ),
        calculated_bounds=st.one_of(
            st.none(),
            st.dictionaries(
                keys=st.text(min_size=1),
                values=st.builds(
                    BoundingBox,
                    x=st.floats(allow_nan=False, allow_infinity=False),
                    y=st.floats(allow_nan=False, allow_infinity=False),
                    width=st.floats(min_value=0, allow_nan=False, allow_infinity=False),
                    height=st.floats(min_value=0, allow_nan=False, allow_infinity=False),
                    padding=st.one_of(
                        st.none(),
                        st.builds(
                            PaddingConfig,
                            top=st.floats(allow_nan=False, allow_infinity=False),
                            right=st.floats(allow_nan=False, allow_infinity=False),
                            bottom=st.floats(allow_nan=False, allow_infinity=False),
                            left=st.floats(allow_nan=False, allow_infinity=False),
                        ),
                    ),
                ),
            ),
        ),
    )
)
def test_blueprint_fuzzing(blueprint: SpatialLayoutBlueprint) -> None:
    # Verify that hypothesis builds are valid Pydantic models
    assert isinstance(blueprint, SpatialLayoutBlueprint)

    # Verify serialization/deserialization works correctly
    json_data = blueprint.model_dump_json()
    reconstructed = SpatialLayoutBlueprint.model_validate_json(json_data)
    assert reconstructed == blueprint


def test_nested_validation() -> None:
    # Test valid BoundingBox with negative coords
    bbox = BoundingBox(x=-10.5, y=-20.5, width=100.0, height=200.0)
    assert bbox.x == -10.5
    assert bbox.y == -20.5
    assert bbox.width == 100.0
    assert bbox.height == 200.0
    assert bbox.padding is None

    # Test valid BoundingBox with padding and negative coords
    padding = PaddingConfig(top=-5.0, right=10.0, bottom=5.0, left=10.0)
    bbox_with_padding = BoundingBox(x=-50.0, y=50.0, width=0.0, height=10.0, padding=padding)
    assert bbox_with_padding.padding is not None
    assert bbox_with_padding.padding.top == -5.0

    # Test invalid BoundingBox (negative width/height)
    with pytest.raises(ValidationError):
        BoundingBox(x=0.0, y=0.0, width=-1.0, height=10.0)

    with pytest.raises(ValidationError):
        BoundingBox(x=0.0, y=0.0, width=10.0, height=-1.0)


def test_enum_json_serialization() -> None:
    # Build a simple relative constraint to test enum JSON serialization
    constraint = RelativeConstraint(
        target_id="node_a", relation=SpatialRelation.LEFT_OF, anchor_id="node_b", offset_mm=10.5
    )

    json_str = constraint.model_dump_json()
    data = json.loads(json_str)

    assert data["relation"] == "LEFT_OF"

    # Test layout direction string representation
    blueprint = SpatialLayoutBlueprint(
        primary_direction=LayoutDirection.TOP_TO_BOTTOM,
        fallback_directions=[],
        edge_routing=RoutingAlgorithm.ORTHOGONAL,
        constraints=[constraint],
    )

    json_str_bp = blueprint.model_dump_json()
    data_bp = json.loads(json_str_bp)

    assert data_bp["primary_direction"] == "TOP_TO_BOTTOM"
    assert data_bp["edge_routing"] == "ORTHOGONAL"
