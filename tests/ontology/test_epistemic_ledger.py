# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for DefeasibleCascadeReceipt, MultimodalTokenAnchorState, and epistemic ledger models."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DefeasibleCascadeEvent,
    MultimodalTokenAnchorState,
)

# ---------------------------------------------------------------------------
# DefeasibleCascadeReceipt
# ---------------------------------------------------------------------------


class TestDefeasibleCascadeEvent:
    """Exercise temporal blast radius validation and quarantine paradox rejection."""

    def _make(self, **overrides) -> DefeasibleCascadeEvent:  # type: ignore[no-untyped-def]
        defaults = {
            "cascade_cid": "c-1",
            "root_falsified_event_cid": "root-1",
            "propagated_decay_factor": 0.5,
            "quarantined_event_cids": ["q-1"],
        }
        defaults.update(overrides)
        return DefeasibleCascadeEvent(**defaults)  # type: ignore[arg-type]

    def test_valid_cascade(self) -> None:
        obj = self._make()
        assert obj.cross_boundary_quarantine_issued is False

    def test_temporal_blast_radius_valid(self) -> None:
        obj = self._make(temporal_blast_radius=(1.0, 5.0))
        assert obj.temporal_blast_radius == (1.0, 5.0)

    def test_temporal_blast_radius_inverted(self) -> None:
        with pytest.raises(ValidationError, match="temporal_blast_radius"):
            self._make(temporal_blast_radius=(5.0, 1.0))

    def test_temporal_blast_radius_equal(self) -> None:
        """Equal bounds are valid (point in time)."""
        obj = self._make(temporal_blast_radius=(3.0, 3.0))
        assert obj.temporal_blast_radius[0] == obj.temporal_blast_radius[1]  # type: ignore[index]

    def test_root_in_quarantine_rejected(self) -> None:
        with pytest.raises(ValidationError, match="root_falsified_event_cid cannot be"):
            self._make(quarantined_event_cids=["root-1"])

    def test_quarantined_sorted(self) -> None:
        obj = self._make(quarantined_event_cids=["z-1", "a-1", "m-1"])
        assert obj.quarantined_event_cids == sorted(obj.quarantined_event_cids)

    @given(
        start=st.floats(min_value=-1e6, max_value=0.0, allow_nan=False, allow_infinity=False),
        end=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=15, deadline=None)
    def test_valid_blast_radius_range(self, start: float, end: float) -> None:
        obj = self._make(temporal_blast_radius=(start, end))
        assert obj.temporal_blast_radius[0] <= obj.temporal_blast_radius[1]  # type: ignore[index]


# ---------------------------------------------------------------------------
# MultimodalTokenAnchorState
# ---------------------------------------------------------------------------


class TestMultimodalTokenAnchorState:
    """Exercise token span, temporal span, and bounding box validators."""

    def test_valid_token_span(self) -> None:
        obj = MultimodalTokenAnchorState(token_span_start=0, token_span_end=10)
        assert obj.token_span_start < obj.token_span_end  # type: ignore[operator]

    def test_token_start_without_end_rejected(self) -> None:
        with pytest.raises(ValidationError, match="token_span_end MUST be defined"):
            MultimodalTokenAnchorState(token_span_start=5)

    def test_token_end_without_start_rejected(self) -> None:
        with pytest.raises(ValidationError, match="without a token_span_start"):
            MultimodalTokenAnchorState(token_span_end=5)

    def test_token_end_lte_start_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strictly greater"):
            MultimodalTokenAnchorState(token_span_start=5, token_span_end=5)

    def test_temporal_frame_valid(self) -> None:
        obj = MultimodalTokenAnchorState(temporal_frame_start_ms=0, temporal_frame_end_ms=1000)
        assert obj.temporal_frame_start_ms < obj.temporal_frame_end_ms  # type: ignore[operator]

    def test_temporal_start_without_end_rejected(self) -> None:
        with pytest.raises(ValidationError, match="temporal_frame_end_ms MUST be defined"):
            MultimodalTokenAnchorState(temporal_frame_start_ms=0)

    def test_temporal_end_without_start_rejected(self) -> None:
        with pytest.raises(ValidationError, match="without a temporal_frame_start_ms"):
            MultimodalTokenAnchorState(temporal_frame_end_ms=1000)

    def test_bounding_box_valid(self) -> None:
        obj = MultimodalTokenAnchorState(bounding_box=(0.0, 0.0, 1.0, 1.0))
        assert obj.bounding_box == (0.0, 0.0, 1.0, 1.0)

    def test_bounding_box_nan_rejected(self) -> None:
        with pytest.raises(ValidationError, match="NaN"):
            MultimodalTokenAnchorState(bounding_box=(float("nan"), 0.0, 1.0, 1.0))

    def test_bounding_box_inf_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Infinity"):
            MultimodalTokenAnchorState(bounding_box=(0.0, 0.0, float("inf"), 1.0))

    def test_bounding_box_inverted_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Spatial invariant"):
            MultimodalTokenAnchorState(bounding_box=(1.0, 0.0, 0.5, 1.0))

    def test_visual_patch_hashes_sorted(self) -> None:
        obj = MultimodalTokenAnchorState(visual_patch_hashes=["z", "a", "m"])
        assert obj.visual_patch_hashes == ["a", "m", "z"]

    @given(
        start=st.integers(min_value=0, max_value=1000),
        delta=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=15, deadline=None)
    def test_valid_token_spans(self, start: int, delta: int) -> None:
        obj = MultimodalTokenAnchorState(token_span_start=start, token_span_end=start + delta)
        assert obj.token_span_end > obj.token_span_start  # type: ignore[operator]

    def test_no_spans_valid(self) -> None:
        """Both spans can be None (empty anchor)."""
        obj = MultimodalTokenAnchorState()
        assert obj.token_span_start is None
        assert obj.temporal_frame_start_ms is None
