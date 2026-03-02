from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.domains.scivis_data import ChartThemePayload


@given(st.builds(ChartThemePayload, color_cycle=st.lists(st.from_regex(r"^#[0-9a-fA-F]{6}$"))))
def test_chart_theme_payload_serialization(payload: ChartThemePayload) -> None:
    # Serialize to dict and ensure it can be rebuilt
    serialized = payload.model_dump()
    deserialized = ChartThemePayload(**serialized)
    assert payload == deserialized
