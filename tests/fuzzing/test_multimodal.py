from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import MultimodalTokenAnchorState


@given(
    start=st.one_of(st.none(), st.integers(min_value=0)),
    end=st.one_of(st.none(), st.integers(min_value=0)),
)
def test_multimodal_token_anchor_state_token_span(start: int | None, end: int | None) -> None:
    # A valid combination is when both are None, or when both are not None and end > start
    is_valid = (start is None and end is None) or (start is not None and end is not None and end > start)

    if is_valid:
        # Valid combination
        anchor = MultimodalTokenAnchorState(token_span_start=start, token_span_end=end)
        assert anchor.token_span_start == start
        assert anchor.token_span_end == end
    else:
        # Invalid combination
        with pytest.raises(ValidationError):
            MultimodalTokenAnchorState(token_span_start=start, token_span_end=end)


@given(
    x_min=st.floats(min_value=0.0, max_value=1.0),
    y_min=st.floats(min_value=0.0, max_value=1.0),
    x_max=st.floats(min_value=0.0, max_value=1.0),
    y_max=st.floats(min_value=0.0, max_value=1.0),
)
def test_multimodal_token_anchor_state_bounding_box(x_min: float, y_min: float, x_max: float, y_max: float) -> None:
    if x_min <= x_max and y_min <= y_max:
        # Valid bounding box
        anchor = MultimodalTokenAnchorState(
            token_span_start=0, token_span_end=1, bounding_box=(x_min, y_min, x_max, y_max)
        )
        assert anchor.bounding_box == (x_min, y_min, x_max, y_max)
    else:
        # Invalid bounding box
        with pytest.raises(ValidationError):
            MultimodalTokenAnchorState(
                token_span_start=0, token_span_end=1, bounding_box=(x_min, y_min, x_max, y_max)
            )


@given(
    hashes=st.lists(st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True)),
)
def test_multimodal_token_anchor_state_visual_patch_hashes_sorting(hashes: list[str]) -> None:
    anchor = MultimodalTokenAnchorState(token_span_start=0, token_span_end=1, visual_patch_hashes=hashes)
    assert anchor.visual_patch_hashes == sorted(hashes)
