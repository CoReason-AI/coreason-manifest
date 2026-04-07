# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import CoalgebraicHydrationPolicy


def test_coalgebraic_hydration_policy_bounds() -> None:
    """
    Test that initializing CoalgebraicHydrationPolicy with an invalid max_unfold_depth raises a ValidationError.
    """
    with pytest.raises(ValidationError) as excinfo:
        from hypothesis import given

        @given(
            policy=st.builds(
                CoalgebraicHydrationPolicy,
                max_unfold_depth=st.integers(max_value=0) | st.integers(min_value=101),
                lazy_fetch_timeout_ms=st.integers(min_value=1, max_value=60000),
                truncation_strategy=st.sampled_from(["hash_pointer", "nullify", "scalar_summary"]),
            )
        )
        def inner_test(policy: CoalgebraicHydrationPolicy) -> None:
            pass

        inner_test()

    # We catch the validation error raised by hypothesis when it tries to build the model with invalid data
    assert "max_unfold_depth" in str(excinfo.value)
