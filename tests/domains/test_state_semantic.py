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

from coreason_manifest.state.semantic import DimensionalProjectionContract


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
