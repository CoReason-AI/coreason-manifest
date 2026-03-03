# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

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
