from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class PanelLetter(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class PanelModality(StrEnum):
    VECTOR_DIAGRAM = "VECTOR_DIAGRAM"
    STATISTICAL_PLOT = "STATISTICAL_PLOT"
    RASTER_IMAGE = "RASTER_IMAGE"


class MacroGrid(BaseModel):
    template_areas: list[str] = Field(
        ..., description='CSS-like grid strings, e.g., ["A A", "B C"] to dictate spanning.'
    )
    row_gap_mm: float = Field(default=5.0, ge=0)
    column_gap_mm: float = Field(default=5.0, ge=0)


class PanelDefinition(BaseModel):
    letter: PanelLetter
    title: str | None = Field(default=None, description="Optional subtitle for the specific panel.")
    modality: PanelModality
    payload_reference: str = Field(
        ...,
        description=(
            "A state-safe pointer/URN to the sub-workflow's output "
            "(e.g., a SpatialLayoutBlueprint or DataPlotBlueprint)."
        ),
    )


class CompositeFigureBlueprint(BaseModel):
    figure_id: str
    global_caption: str = Field(..., description="The master caption for the entire multi-panel figure.")
    grid: MacroGrid
    panels: list[PanelDefinition]

    @model_validator(mode="after")
    def validate_grid_and_panels(self) -> Self:
        # Extract unique valid letters from the template_areas
        grid_letters: set[str] = set()
        for row in self.grid.template_areas:
            # We assume template_areas strings are space separated (e.g., "A A", "B C")
            for token in row.split():
                if token != ".":  # noqa: S105
                    grid_letters.add(token)

        # Extract unique letters from panels
        panel_letters: set[str] = {panel.letter.value for panel in self.panels}

        # Check for missing panel definitions: a letter is in grid, but not in panels.
        missing_panels = grid_letters - panel_letters
        if missing_panels:
            raise ValueError(f"Grid uses panels {missing_panels} which are not defined in the panels list.")

        # Check for orphaned panels: a letter is in panels, but not in grid.
        orphaned_panels = panel_letters - grid_letters
        if orphaned_panels:
            raise ValueError(f"Panels list defines {orphaned_panels} which are not placed in the grid.")

        return self
