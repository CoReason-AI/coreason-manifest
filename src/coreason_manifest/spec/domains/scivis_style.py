"""
Academic Style Profiles defining the DesignSystemConfig schema for academic journal constraints.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class AcademicJournal(StrEnum):
    """Enumeration of supported academic journals."""

    NATURE = "NATURE"
    IEEE = "IEEE"
    CELL = "CELL"
    ICLR = "ICLR"
    DEFAULT_ACADEMIC = "DEFAULT_ACADEMIC"


class ColorToken(StrEnum):
    """Semantic CSS-like color variables."""

    BACKGROUND = "BACKGROUND"
    PRIMARY_STROKE = "PRIMARY_STROKE"
    TEXT_PRIMARY = "TEXT_PRIMARY"
    ACCENT_1 = "ACCENT_1"
    ACCENT_2 = "ACCENT_2"


class CanvasGeometry(BaseModel):
    """Defines the rigid mathematical dimensions and layout properties of the canvas."""

    target_column_width_mm: float = Field(
        ...,
        description="The exact width of the column in millimeters required by the journal.",
        examples=[88.9, 180.0],
    )
    aspect_ratio_constraint: Literal["16:9", "4:3", "1:1", "auto"] = Field(
        ...,
        description="The aspect ratio constraint for the visualization canvas.",
        examples=["16:9", "auto"],
    )


class TypographyConfig(BaseModel):
    """Defines typography constraints including fonts and specific sizes for semantic elements."""

    font_family: str = Field(
        ...,
        description="The CSS font-family string required for the visualization text.",
        examples=["Helvetica, Arial, sans-serif", "Times New Roman, serif"],
    )
    base_font_size_pt: float = Field(
        ...,
        description="The base font size in points (pt) for standard text.",
        examples=[8.0, 10.0],
    )
    title_font_size_pt: float = Field(
        ...,
        description="The font size in points (pt) for titles and primary headers.",
        examples=[10.0, 12.0],
    )


class ColorPalette(BaseModel):
    """Defines the strictly typed set of semantic colors to be used, ensuring accessibility compliance."""

    is_colorblind_safe: bool = Field(
        ...,
        description="Crucial 2026 A11y flag. Must be true if the palette guarantees WCAG 2.2+ colorblind safety.",
        examples=[True, False],
    )
    tokens: dict[ColorToken, str] = Field(
        ...,
        description="A mapping from semantic ColorToken to valid CSS hex color codes.",
        examples=[
            {
                ColorToken.BACKGROUND: "#FFFFFF",
                ColorToken.PRIMARY_STROKE: "#000000",
                ColorToken.TEXT_PRIMARY: "#333333",
                ColorToken.ACCENT_1: "#0072B2",
                ColorToken.ACCENT_2: "#D55E00",
            }
        ],
    )


class SemanticColorMap(BaseModel):
    """Maps logical rendering roles to specific semantic color tokens to prevent aesthetic drift."""

    role_to_token: dict[str, ColorToken] = Field(
        ...,
        description="A dictionary mapping logical entity roles to semantic ColorToken enums.",
        examples=[
            {
                "neural_network_layer": ColorToken.ACCENT_1,
                "attention_head": ColorToken.ACCENT_2,
                "canvas_bg": ColorToken.BACKGROUND,
            }
        ],
    )


class DesignSystemConfig(BaseModel):
    """
    The master contract for an Academic Journal style profile.
    This acts as a rigid, mathematical Style Envelope that forces downstream AI renderers
    to blindly apply correct, journal-compliant CSS/SVG styles.
    """

    journal: AcademicJournal = Field(
        ...,
        description="The target academic journal for this design system.",
        examples=[AcademicJournal.IEEE, AcademicJournal.NATURE],
    )
    geometry: CanvasGeometry = Field(
        ...,
        description="The geometric constraints for the visualization canvas.",
    )
    typography: TypographyConfig = Field(
        ...,
        description="The typography rules and sizes for all text elements.",
    )
    palette: ColorPalette = Field(
        ...,
        description="The strict color palette defining tokens and accessibility status.",
    )
    semantic_map: SemanticColorMap = Field(
        ...,
        description="The mapping from logical roles to color tokens to ensure aesthetic consistency.",
    )
