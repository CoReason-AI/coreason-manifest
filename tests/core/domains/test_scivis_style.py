"""
Tests for the Academic Style Profiles DesignSystemConfig schema.
"""

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.core.domains.scivis_style import (
    AcademicJournal,
    CanvasGeometry,
    ColorPalette,
    ColorToken,
    DesignSystemConfig,
    SemanticColorMap,
    TypographyConfig,
)


@st.composite
def canvas_geometry_strategy(draw: st.DrawFn) -> CanvasGeometry:
    return CanvasGeometry(
        target_column_width_mm=draw(st.floats(min_value=1.0, max_value=500.0)),
        aspect_ratio_constraint=draw(st.sampled_from(["16:9", "4:3", "1:1", "auto"])),
    )


@st.composite
def typography_config_strategy(draw: st.DrawFn) -> TypographyConfig:
    return TypographyConfig(
        font_family=draw(st.text(min_size=1)),
        base_font_size_pt=draw(st.floats(min_value=1.0, max_value=72.0)),
        title_font_size_pt=draw(st.floats(min_value=1.0, max_value=100.0)),
    )


@st.composite
def color_palette_strategy(draw: st.DrawFn) -> ColorPalette:
    tokens_dict = draw(
        st.dictionaries(
            st.sampled_from(ColorToken),
            st.from_regex(r"^#[0-9a-fA-F]{6}$"),
            min_size=1,
            max_size=len(ColorToken),
        )
    )
    return ColorPalette(
        is_colorblind_safe=draw(st.booleans()),
        tokens=tokens_dict,
    )


@st.composite
def semantic_color_map_strategy(draw: st.DrawFn) -> SemanticColorMap:
    role_to_token_dict = draw(
        st.dictionaries(
            st.text(min_size=1),
            st.sampled_from(ColorToken),
            min_size=1,
        )
    )
    return SemanticColorMap(role_to_token=role_to_token_dict)


@st.composite
def design_system_config_strategy(draw: st.DrawFn) -> DesignSystemConfig:
    return DesignSystemConfig(
        journal=draw(st.sampled_from(AcademicJournal)),
        geometry=draw(canvas_geometry_strategy()),
        typography=draw(typography_config_strategy()),
        palette=draw(color_palette_strategy()),
        semantic_map=draw(semantic_color_map_strategy()),
    )


@given(design_system_config_strategy())
def test_design_system_config_fuzz(config: DesignSystemConfig) -> None:
    """Fuzz test the generation and serialization of DesignSystemConfig."""
    dump = config.model_dump(mode="json")

    # Verify Enums serialize to correct string representations
    assert dump["journal"] in [j.value for j in AcademicJournal]

    for token_key in dump["palette"]["tokens"]:
        assert token_key in [t.value for t in ColorToken]

    for token_val in dump["semantic_map"]["role_to_token"].values():
        assert token_val in [t.value for t in ColorToken]

    # Re-parse from dump to ensure valid serialization round-trip
    parsed = DesignSystemConfig.model_validate(dump)
    assert parsed == config


def test_serialization_of_enums() -> None:
    """Test standard JSON serialization string formats."""
    config = DesignSystemConfig(
        journal=AcademicJournal.IEEE,
        geometry=CanvasGeometry(target_column_width_mm=88.9, aspect_ratio_constraint="16:9"),
        typography=TypographyConfig(font_family="Arial", base_font_size_pt=10.0, title_font_size_pt=12.0),
        palette=ColorPalette(
            is_colorblind_safe=True, tokens={ColorToken.BACKGROUND: "#ffffff", ColorToken.PRIMARY_STROKE: "#000000"}
        ),
        semantic_map=SemanticColorMap(role_to_token={"bg": ColorToken.BACKGROUND}),
    )
    json_str = config.model_dump_json()
    json_dict = json.loads(json_str)

    assert json_dict["journal"] == "IEEE"
    assert json_dict["palette"]["tokens"]["BACKGROUND"] == "#ffffff"
    assert json_dict["semantic_map"]["role_to_token"]["bg"] == "BACKGROUND"


def test_missing_required_fields_fails() -> None:
    """Test that missing mandatory fields raises validation error."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Field required"):
        CanvasGeometry(target_column_width_mm=88.9)  # type: ignore[call-arg] # missing aspect_ratio_constraint

    with pytest.raises(ValidationError, match="Field required"):
        ColorPalette(is_colorblind_safe=True)  # type: ignore[call-arg] # missing tokens
