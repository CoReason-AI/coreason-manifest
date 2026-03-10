# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest import DimensionalProjectionContract, MultimodalTokenAnchor


@given(isometry_preservation_score=st.floats(max_value=-0.000001) | st.floats(min_value=1.000001))
def test_dimensional_projection_contract_mathematical_bounds(isometry_preservation_score: float) -> None:
    """Test: Prove DimensionalProjectionContract decisively rejects values outside [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        DimensionalProjectionContract(
            source_model_name="source",
            target_model_name="target",
            projection_matrix_hash="hash",
            isometry_preservation_score=isometry_preservation_score,
        )


def test_multimodal_token_anchor_bounds() -> None:
    MultimodalTokenAnchor(token_span_start=5, token_span_end=10)
    with pytest.raises(ValidationError, match="token_span_end cannot be defined without a token_span_start"):
        MultimodalTokenAnchor(token_span_end=10)
    with pytest.raises(ValidationError, match="token_span_end MUST be strictly greater than token_span_start"):
        MultimodalTokenAnchor(token_span_start=5, token_span_end=5)
    with pytest.raises(ValidationError, match="If token_span_start is defined, token_span_end MUST be defined"):
        MultimodalTokenAnchor(token_span_start=5)


def test_multimodal_token_anchor_spatial_invariant() -> None:
    """Verify that inverted bounding boxes raise strict struct-legible ValueErrors."""
    from coreason_manifest import MultimodalTokenAnchor

    # Valid geometry
    anchor = MultimodalTokenAnchor(bounding_box=(0.0, 0.0, 10.0, 10.0))
    assert anchor.bounding_box == (0.0, 0.0, 10.0, 10.0)

    # Invalid geometry (x_min > x_max)
    with pytest.raises(ValidationError, match="Spatial invariant violated"):
        MultimodalTokenAnchor(bounding_box=(15.0, 0.0, 10.0, 10.0))

    # Invalid geometry (y_min > y_max)
    with pytest.raises(ValidationError, match="Spatial invariant violated"):
        MultimodalTokenAnchor(bounding_box=(0.0, 20.0, 10.0, 10.0))
