# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import AmbientState, MacroGridProfile, PresentationManifest


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=2)
    | st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=4, max_size=4)
)
def test_fractional_grid_topology_contradiction(column_weights: list[float]) -> None:
    layout_matrix = [["p1", "p2", "p3"], ["p4", "p5", "p6"], ["p7", "p8", "p9"]]
    # Valid dummy panels so we don't trigger missing required fields or invalid panel validation
    panels: Any = [
        {
            "type": "insight_card",
            "panel_cid": "p1",
            "title": "Title 1",
            "markdown_content": "Content 1",
        },
        {"type": "insight_card", "panel_cid": "p2", "title": "Title 2", "markdown_content": "Content 2"},
        {"type": "insight_card", "panel_cid": "p3", "title": "Title 3", "markdown_content": "Content 3"},
        {"type": "insight_card", "panel_cid": "p4", "title": "Title 4", "markdown_content": "Content 4"},
        {"type": "insight_card", "panel_cid": "p5", "title": "Title 5", "markdown_content": "Content 5"},
        {"type": "insight_card", "panel_cid": "p6", "title": "Title 6", "markdown_content": "Content 6"},
        {"type": "insight_card", "panel_cid": "p7", "title": "Title 7", "markdown_content": "Content 7"},
        {"type": "insight_card", "panel_cid": "p8", "title": "Title 8", "markdown_content": "Content 8"},
        {"type": "insight_card", "panel_cid": "p9", "title": "Title 9", "markdown_content": "Content 9"},
    ]

    try:
        MacroGridProfile(layout_matrix=layout_matrix, column_fractional_weights=column_weights, panels=panels)
    except ValidationError as e:
        if "Topological Contradiction" not in str(e):
            raise AssertionError(f"Expected verify_matrix_dimensions validation error, got: {e}") from e
    else:
        raise AssertionError("ValidationError not raised for invalid column_fractional_weights length")


@given(st.floats(max_value=-0.01) | st.floats(min_value=1.01))
def test_entropic_telemetry_bounds(invalid_entropy: float) -> None:
    try:
        AmbientState(status_message="test", epistemic_entropy_score=invalid_entropy)
    except ValidationError:
        pass
    else:
        raise AssertionError("ValidationError not raised for out of bounds epistemic_entropy_score")


@given(st.floats(max_value=0.0) | st.floats(min_value=100.01))
def test_focal_plane_integrity(invalid_focal_depth: float) -> None:
    # Dummy mock objects for PresentationManifest to ensure we don't fail other fields' validations first
    valid_intent: Any = {
        "type": "drafting_intent",
        "description": "Mock drafting intent",
        "target_audience": "human_supervisor",
        "proposed_schemas": [],
        "draft_urgency_level": "standard",
    }
    valid_grid: Any = {"layout_matrix": [], "panels": []}

    try:
        PresentationManifest(
            intent=valid_intent,
            grid=valid_grid,
            focal_depth_meters=invalid_focal_depth,
        )
    except ValidationError as e:
        if "focal_depth_meters" not in str(e):
            raise AssertionError(f"Expected validation error for focal_depth_meters, got: {e}") from e
    else:
        raise AssertionError("ValidationError not raised for out of bounds focal_depth_meters")
