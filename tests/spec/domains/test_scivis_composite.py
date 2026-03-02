import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.domains.scivis_composite import (
    CompositeFigureBlueprint,
    MacroGrid,
    PanelDefinition,
    PanelLetter,
    PanelModality,
)


def test_happy_path_valid_layout() -> None:
    grid = MacroGrid(template_areas=["A A", "B C"], row_gap_mm=5.0, column_gap_mm=5.0)
    panels = [
        PanelDefinition(
            letter=PanelLetter.A,
            title="Overview",
            modality=PanelModality.VECTOR_DIAGRAM,
            payload_reference="urn:workflow:1",
        ),
        PanelDefinition(
            letter=PanelLetter.B,
            title="Stats",
            modality=PanelModality.STATISTICAL_PLOT,
            payload_reference="urn:workflow:2",
        ),
        PanelDefinition(
            letter=PanelLetter.C, title="Image", modality=PanelModality.RASTER_IMAGE, payload_reference="urn:workflow:3"
        ),
    ]
    blueprint = CompositeFigureBlueprint(figure_id="fig-1", global_caption="A test figure", grid=grid, panels=panels)
    assert blueprint.figure_id == "fig-1"
    assert len(blueprint.panels) == 3


def test_missing_panel_definition_error() -> None:
    grid = MacroGrid(template_areas=["A A", "B C"], row_gap_mm=5.0, column_gap_mm=5.0)
    # Missing panel C
    panels = [
        PanelDefinition(
            letter=PanelLetter.A, modality=PanelModality.VECTOR_DIAGRAM, payload_reference="urn:workflow:1"
        ),
        PanelDefinition(
            letter=PanelLetter.B, modality=PanelModality.STATISTICAL_PLOT, payload_reference="urn:workflow:2"
        ),
    ]
    with pytest.raises(ValueError, match=r"Grid uses panels .* which are not defined in the panels list."):
        CompositeFigureBlueprint(figure_id="fig-1", global_caption="A test figure", grid=grid, panels=panels)


def test_orphaned_panel_error() -> None:
    grid = MacroGrid(template_areas=["A A"], row_gap_mm=5.0, column_gap_mm=5.0)
    panels = [
        PanelDefinition(
            letter=PanelLetter.A, modality=PanelModality.VECTOR_DIAGRAM, payload_reference="urn:workflow:1"
        ),
        PanelDefinition(
            letter=PanelLetter.B,  # B is not in grid
            modality=PanelModality.STATISTICAL_PLOT,
            payload_reference="urn:workflow:2",
        ),
    ]
    with pytest.raises(ValueError, match=r"Panels list defines .* which are not placed in the grid."):
        CompositeFigureBlueprint(figure_id="fig-1", global_caption="A test figure", grid=grid, panels=panels)


def test_json_serialization_resolves_enums() -> None:
    grid = MacroGrid(
        template_areas=["A A", "B ."],
    )
    panels = [
        PanelDefinition(
            letter=PanelLetter.A, modality=PanelModality.VECTOR_DIAGRAM, payload_reference="urn:workflow:1"
        ),
        PanelDefinition(
            letter=PanelLetter.B, modality=PanelModality.STATISTICAL_PLOT, payload_reference="urn:workflow:2"
        ),
    ]
    blueprint = CompositeFigureBlueprint(figure_id="fig-1", global_caption="A test figure", grid=grid, panels=panels)
    dumped = blueprint.model_dump_json()
    data = json.loads(dumped)

    # Check Enums are pure strings in the dumped JSON
    assert data["panels"][0]["letter"] == "A"
    assert data["panels"][0]["modality"] == "VECTOR_DIAGRAM"
    assert data["panels"][1]["letter"] == "B"
    assert data["panels"][1]["modality"] == "STATISTICAL_PLOT"


# Hypothesis Fuzzing Strategy
# Let's generate a valid subset of letters to use for grid and panels
from typing import Any

@st.composite
def blueprint_data(draw: st.DrawFn) -> dict[str, Any]:
    # Pick a random non-empty subset of valid panel letters
    all_letters = ["A", "B", "C", "D", "E", "F"]
    used_letters = draw(st.lists(st.sampled_from(all_letters), min_size=1, max_size=6, unique=True))

    # Generate some grid strings using these letters
    # For simplicity, let's just create one row containing all the used letters
    row_string = " ".join(used_letters)
    template_areas = [row_string]

    grid = {
        "template_areas": template_areas,
        "row_gap_mm": draw(st.floats(min_value=0.0, max_value=100.0)),
        "column_gap_mm": draw(st.floats(min_value=0.0, max_value=100.0)),
    }

    panels = [
        {
            "letter": letter,
            "title": draw(st.one_of(st.none(), st.text())),
            "modality": draw(st.sampled_from(["VECTOR_DIAGRAM", "STATISTICAL_PLOT", "RASTER_IMAGE"])),
            "payload_reference": draw(st.text(min_size=1)),
        }
        for letter in used_letters
    ]

    return {
        "figure_id": draw(st.text(min_size=1)),
        "global_caption": draw(st.text()),
        "grid": grid,
        "panels": panels,
    }


@given(blueprint_data())
def test_fuzz_composite_figure_blueprint(data: dict[str, Any]) -> None:
    # This should always successfully validate since we generated matching grids and panels
    blueprint = CompositeFigureBlueprint.model_validate(data)
    assert blueprint.figure_id == data["figure_id"]
    assert len(blueprint.panels) == len(data["panels"])
