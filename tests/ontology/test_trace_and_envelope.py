# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for TraceContextState, StateVectorProfile, and ExecutionEnvelopeState."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ExecutionEnvelopeState,
    GradingCriterionProfile,
    StateVectorProfile,
    TraceContextState,
)
from tests.ontology.strategies import ulid_strategy

# ---------------------------------------------------------------------------
# TraceContextState
# ---------------------------------------------------------------------------


class TestTraceContextState:
    """Exercise verify_span_topology validator."""

    VALID_ULID_1 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    VALID_ULID_2 = "01ARZ3NDEKTSV4RRFFQ69G5FAW"

    def test_valid_root_span(self) -> None:
        tc = TraceContextState(trace_cid=self.VALID_ULID_1, span_cid=self.VALID_ULID_2)
        assert tc.parent_span_cid is None

    def test_valid_child_span(self) -> None:
        tc = TraceContextState(
            trace_cid=self.VALID_ULID_1,
            span_cid=self.VALID_ULID_2,
            parent_span_cid=self.VALID_ULID_1,
        )
        assert tc.parent_span_cid == self.VALID_ULID_1

    def test_self_pointer_rejected(self) -> None:
        """span_cid == parent_span_cid is a self-loop violation."""
        with pytest.raises(ValidationError, match="cannot equal parent_span_cid"):
            TraceContextState(
                trace_cid=self.VALID_ULID_1,
                span_cid=self.VALID_ULID_2,
                parent_span_cid=self.VALID_ULID_2,
            )

    def test_invalid_trace_cid_format(self) -> None:
        with pytest.raises(ValidationError):
            TraceContextState(trace_cid="not-a-ulid", span_cid=self.VALID_ULID_1)

    @given(
        trace=ulid_strategy(),
        span=ulid_strategy(),
    )
    @settings(max_examples=15, deadline=None)
    def test_distinct_ulids_create_valid_spans(self, trace: str, span: str) -> None:
        tc = TraceContextState(trace_cid=trace, span_cid=span)
        assert tc.causal_clock == 0


# ---------------------------------------------------------------------------
# StateVectorProfile
# ---------------------------------------------------------------------------


class TestStateVectorProfile:
    """Exercise memory bounds validation via payload bounds."""

    def test_valid_immutable_matrix(self) -> None:
        sv = StateVectorProfile(immutable_matrix={"key": "val"})
        assert sv.immutable_matrix["key"] == "val"

    def test_valid_with_mutable(self) -> None:
        sv = StateVectorProfile(
            immutable_matrix={"task": "test"},
            mutable_matrix={"history": "entry1"},
            is_delta=True,
        )
        assert sv.is_delta is True

    def test_deeply_nested_mutable_rejected(self) -> None:
        """Payload exceeding recursion depth is rejected."""
        nested: dict = {"a": None}  # type: ignore[type-arg]
        current = nested
        for _ in range(15):
            child: dict = {"inner": None}  # type: ignore[type-arg]
            current["a"] = child
            current = child
        with pytest.raises(ValidationError, match="recursion depth"):
            StateVectorProfile(mutable_matrix=nested)

    @given(
        keys=st.lists(
            st.text(alphabet="abcdef", min_size=1, max_size=5),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    @settings(max_examples=15, deadline=None)
    def test_small_dicts_always_valid(self, keys: list[str]) -> None:
        matrix = dict.fromkeys(keys, "v")
        sv = StateVectorProfile(immutable_matrix=matrix)  # type: ignore[arg-type]
        assert len(sv.immutable_matrix) == len(keys)


# ---------------------------------------------------------------------------
# ExecutionEnvelopeState
# ---------------------------------------------------------------------------


class TestExecutionEnvelopeState:
    """Exercise the generic envelope wrapper."""

    VALID_ULID_1 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    VALID_ULID_2 = "01ARZ3NDEKTSV4RRFFQ69G5FAW"

    def test_valid_envelope(self) -> None:
        tc = TraceContextState(trace_cid=self.VALID_ULID_1, span_cid=self.VALID_ULID_2)
        sv = StateVectorProfile(immutable_matrix={"mode": "test"})
        payload = GradingCriterionProfile(criterion_cid="g1", description="d", weight=1.0)
        env = ExecutionEnvelopeState(trace_context=tc, state_vector=sv, payload=payload)
        assert env.payload.criterion_cid == "g1"
