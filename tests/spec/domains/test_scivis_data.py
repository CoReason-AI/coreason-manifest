import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.domains.scivis_data import ChartThemePayload

# Generate valid hex color codes
hex_colors = st.from_regex(r"^#[0-9a-fA-F]{6}$", fullmatch=True)


@given(
    primary_font_family=st.text(min_size=1),
    base_font_size_pt=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    color_cycle=st.lists(hex_colors, min_size=1),
    background_color=st.one_of(st.none(), hex_colors),
    gridline_color=st.one_of(st.none(), hex_colors),
    stroke_width_pt=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_chart_theme_payload_fuzzing(
    primary_font_family: str,
    base_font_size_pt: float,
    color_cycle: list[str],
    background_color: str | None,
    gridline_color: str | None,
    stroke_width_pt: float,
) -> None:
    payload = ChartThemePayload(
        primary_font_family=primary_font_family,
        base_font_size_pt=base_font_size_pt,
        color_cycle=color_cycle,
        background_color=background_color,
        gridline_color=gridline_color,
        stroke_width_pt=stroke_width_pt,
    )

    assert payload.primary_font_family == primary_font_family
    assert payload.base_font_size_pt == pytest.approx(base_font_size_pt)
    assert payload.color_cycle == color_cycle
    assert payload.background_color == background_color
    assert payload.gridline_color == gridline_color
    assert payload.stroke_width_pt == pytest.approx(stroke_width_pt)

    # Test serialization and deserialization
    serialized = payload.model_dump()
    deserialized = ChartThemePayload(**serialized)
    assert deserialized == payload
