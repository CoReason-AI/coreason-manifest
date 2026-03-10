# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.spec.ontology import SpatialBoundingBoxProfile, SpatialKinematicActionIntent


@st.composite
def draw_normalized_coordinate(draw: Any) -> dict[str, Any]:
    return {
        "x": draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        "y": draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
    }


@st.composite
def draw_bounding_box(draw: Any) -> dict[str, Any]:
    x1 = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    x2 = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    y1 = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    y2 = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))

    return {
        "x_min": min(x1, x2),
        "x_max": max(x1, x2),
        "y_min": min(y1, y2),
        "y_max": max(y1, y2),
    }


@st.composite
def draw_spatial_kinematic_action(draw: Any) -> dict[str, Any]:
    return {
        "action_type": draw(
            st.sampled_from(["click", "double_click", "drag_and_drop", "scroll", "hover", "keystroke"])
        ),
        "target_coordinate": draw(st.one_of(st.none(), draw_normalized_coordinate())),
        "trajectory_duration_ms": draw(st.one_of(st.none(), st.integers(min_value=1))),
        "bezier_control_points": draw(st.lists(draw_normalized_coordinate(), max_size=5)),
        "expected_visual_concept": draw(st.one_of(st.none(), st.text(min_size=1))),
    }


@given(draw_bounding_box())
def test_bounding_box_valid(payload: dict[str, Any]) -> None:
    TypeAdapter(SpatialBoundingBoxProfile).validate_python(payload)


def test_bounding_box_invalid_geometry() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(SpatialBoundingBoxProfile).validate_python({"x_min": 0.8, "x_max": 0.2, "y_min": 0.0, "y_max": 1.0})


def test_bounding_box_invalid_geometry_y() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(SpatialBoundingBoxProfile).validate_python({"x_min": 0.0, "x_max": 1.0, "y_min": 0.8, "y_max": 0.2})


@given(draw_spatial_kinematic_action())
def test_spatial_kinematic_action_routing(payload: dict[str, Any]) -> None:
    TypeAdapter(SpatialKinematicActionIntent).validate_python(payload)
