from pydantic import BaseModel, Field


class ChartThemePayload(BaseModel):
    primary_font_family: str
    base_font_size_pt: float
    color_cycle: list[str] = Field(
        ...,
        description="List of hex codes derived from Epic 1's SemanticColorMap to strictly enforce data-point colors.",
    )
    background_color: str | None = Field(
        default=None,
        description="Typically None/transparent for Naked SVGs, allowing the layout canvas to show through.",
    )
    gridline_color: str | None
    stroke_width_pt: float
