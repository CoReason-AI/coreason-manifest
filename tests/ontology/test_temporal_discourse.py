# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for TemporalBoundsProfile and DiscourseTreeManifest DAG integrity."""

import time

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DiscourseNodeState,
    DiscourseTreeManifest,
    TemporalBoundsProfile,
)


class TestTemporalBoundsProfile:
    """Exercise validate_temporal_bounds validator."""

    def test_valid_open_ended(self) -> None:
        now = time.time()
        obj = TemporalBoundsProfile(valid_from=now)
        assert obj.valid_to is None

    def test_valid_closed_range(self) -> None:
        now = time.time()
        obj = TemporalBoundsProfile(valid_from=now, valid_to=now + 100.0)
        assert obj.valid_to > obj.valid_from  # type: ignore[operator]

    def test_valid_to_before_valid_from_rejected(self) -> None:
        now = time.time()
        with pytest.raises(ValidationError, match="valid_to cannot be before"):
            TemporalBoundsProfile(valid_from=now, valid_to=now - 100.0)

    def test_probabilistic_start_interval_valid(self) -> None:
        now = time.time()
        obj = TemporalBoundsProfile(
            valid_from=now,
            probabilistic_start_interval=(now - 1.0, now + 1.0),
        )
        assert obj.probabilistic_start_interval is not None

    def test_probabilistic_start_interval_inverted(self) -> None:
        now = time.time()
        with pytest.raises(ValidationError, match="probabilistic_start_interval"):
            TemporalBoundsProfile(
                valid_from=now,
                probabilistic_start_interval=(now + 1.0, now - 1.0),
            )

    def test_valid_from_outside_start_interval(self) -> None:
        now = time.time()
        with pytest.raises(ValidationError, match="valid_from must fall within"):
            TemporalBoundsProfile(
                valid_from=now,
                probabilistic_start_interval=(now + 10.0, now + 20.0),
            )

    def test_probabilistic_end_interval_valid(self) -> None:
        now = time.time()
        obj = TemporalBoundsProfile(
            valid_from=now,
            valid_to=now + 100.0,
            probabilistic_end_interval=(now + 50.0, now + 150.0),
        )
        assert obj.probabilistic_end_interval is not None

    def test_probabilistic_end_interval_inverted(self) -> None:
        now = time.time()
        with pytest.raises(ValidationError, match="probabilistic_end_interval"):
            TemporalBoundsProfile(
                valid_from=now,
                valid_to=now + 100.0,
                probabilistic_end_interval=(now + 150.0, now + 50.0),
            )

    def test_valid_to_outside_end_interval(self) -> None:
        now = time.time()
        with pytest.raises(ValidationError, match="valid_to must fall within"):
            TemporalBoundsProfile(
                valid_from=now,
                valid_to=now + 100.0,
                probabilistic_end_interval=(now + 200.0, now + 300.0),
            )

    @given(
        offset=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=15, deadline=None)
    def test_valid_range_property(self, offset: float) -> None:
        now = time.time()
        obj = TemporalBoundsProfile(valid_from=now, valid_to=now + offset)
        assert obj.valid_to >= obj.valid_from  # type: ignore[operator]


class TestDiscourseTreeManifest:
    """Exercise verify_discourse_dag_integrity validator."""

    def _node(self, cid: str, parent: str | None = None) -> DiscourseNodeState:
        return DiscourseNodeState(
            node_cid=cid,
            discourse_type="findings",
            parent_node_cid=parent,
        )

    def test_valid_single_root(self) -> None:
        obj = DiscourseTreeManifest(
            manifest_cid="dm-1",
            root_node_cid="did:z:root",
            discourse_nodes={"did:z:root": self._node("did:z:root")},
        )
        assert obj.root_node_cid == "did:z:root"

    def test_valid_tree(self) -> None:
        obj = DiscourseTreeManifest(
            manifest_cid="dm-2",
            root_node_cid="did:z:root",
            discourse_nodes={
                "did:z:root": self._node("did:z:root"),
                "did:z:child1": self._node("did:z:child1", "did:z:root"),
                "did:z:child2": self._node("did:z:child2", "did:z:root"),
            },
        )
        assert len(obj.discourse_nodes) == 3

    def test_root_not_found_rejected(self) -> None:
        with pytest.raises(ValidationError, match="root_node_cid not found"):
            DiscourseTreeManifest(
                manifest_cid="dm-3",
                root_node_cid="did:z:missing",
                discourse_nodes={"did:z:root": self._node("did:z:root")},
            )

    def test_ghost_pointer_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Ghost pointer"):
            DiscourseTreeManifest(
                manifest_cid="dm-4",
                root_node_cid="did:z:root",
                discourse_nodes={
                    "did:z:root": self._node("did:z:root"),
                    "did:z:child": self._node("did:z:child", "did:z:nonexistent"),
                },
            )

    def test_cycle_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cyclical reference"):
            DiscourseTreeManifest(
                manifest_cid="dm-5",
                root_node_cid="did:z:aaa",
                discourse_nodes={
                    "did:z:aaa": self._node("did:z:aaa", "did:z:bbb"),
                    "did:z:bbb": self._node("did:z:bbb", "did:z:aaa"),
                },
            )

    def test_contained_propositions_sorted(self) -> None:
        node = DiscourseNodeState(
            node_cid="did:z:n1",
            discourse_type="preamble",
            contained_propositions=["did:z:c", "did:z:a", "did:z:b"],
        )
        assert node.contained_propositions == sorted(node.contained_propositions)
