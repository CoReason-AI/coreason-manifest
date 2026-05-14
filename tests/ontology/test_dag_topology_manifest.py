# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for DAGTopologyManifest — edge validation, cycle detection, depth limits, fan-out."""

from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveAgentNodeProfile,
    CognitiveSystemNodeProfile,
    DAGTopologyManifest,
    EpistemicTopologicalParadoxFalsificationEvent,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _agent(desc: str = "agent") -> CognitiveAgentNodeProfile:
    return CognitiveAgentNodeProfile(description=desc)


def _system(desc: str = "system") -> CognitiveSystemNodeProfile:
    return CognitiveSystemNodeProfile(description=desc)


# ---------------------------------------------------------------------------
# DAGTopologyManifest
# ---------------------------------------------------------------------------


class TestDAGTopologyManifest:
    """Exercise verify_edges_exist_and_compute_bounds validator."""

    def test_valid_dag(self) -> None:
        obj = DAGTopologyManifest(
            nodes={
                "did:z:a": _agent(),
                "did:z:b": _system(),
                "did:z:c": _system(),
            },
            edges=[("did:z:a", "did:z:b"), ("did:z:b", "did:z:c")],
            max_depth=10,
            max_fan_out=5,
        )
        assert len(obj.nodes) == 3

    def test_edge_source_not_found(self) -> None:
        with pytest.raises(ValidationError, match="does not exist"):
            DAGTopologyManifest(
                nodes={"did:z:a": _agent()},
                edges=[("did:z:missing", "did:z:a")],
                max_depth=10,
                max_fan_out=5,
            )

    def test_edge_target_not_found(self) -> None:
        with pytest.raises(ValidationError, match="does not exist"):
            DAGTopologyManifest(
                nodes={"did:z:a": _agent()},
                edges=[("did:z:a", "did:z:missing")],
                max_depth=10,
                max_fan_out=5,
            )

    def test_fan_out_exceeded(self) -> None:
        with pytest.raises(ValidationError, match="max_fan_out"):
            DAGTopologyManifest(
                nodes={
                    "did:z:a": _agent(),
                    "did:z:b": _system(),
                    "did:z:c": _system(),
                    "did:z:d": _system(),
                },
                edges=[
                    ("did:z:a", "did:z:b"),
                    ("did:z:a", "did:z:c"),
                    ("did:z:a", "did:z:d"),
                ],
                max_depth=10,
                max_fan_out=2,
            )

    def test_cycle_detected(self) -> None:
        with pytest.raises((ValidationError, EpistemicTopologicalParadoxFalsificationEvent)):
            DAGTopologyManifest(
                nodes={
                    "did:z:a": _agent(),
                    "did:z:b": _system(),
                },
                edges=[("did:z:a", "did:z:b"), ("did:z:b", "did:z:a")],
                allow_cycles=False,
                max_depth=10,
                max_fan_out=5,
            )

    def test_cycles_allowed(self) -> None:
        obj = DAGTopologyManifest(
            nodes={
                "did:z:a": _agent(),
                "did:z:b": _system(),
            },
            edges=[("did:z:a", "did:z:b"), ("did:z:b", "did:z:a")],
            allow_cycles=True,
            max_depth=10,
            max_fan_out=5,
        )
        assert len(obj.edges) == 2

    def test_depth_exceeded(self) -> None:
        with pytest.raises(ValidationError, match="exceeds max_depth"):
            DAGTopologyManifest(
                nodes={
                    "did:z:a": _agent(),
                    "did:z:b": _system(),
                    "did:z:c": _system(),
                    "did:z:d": _system(),
                },
                edges=[
                    ("did:z:a", "did:z:b"),
                    ("did:z:b", "did:z:c"),
                    ("did:z:c", "did:z:d"),
                ],
                allow_cycles=False,
                max_depth=2,
                max_fan_out=5,
            )

    def test_draft_phase_skips_validation(self) -> None:
        """lifecycle_phase='draft' skips edge validation."""
        obj = DAGTopologyManifest(
            nodes={"did:z:a": _agent()},
            edges=[],
            lifecycle_phase="draft",
            max_depth=10,
            max_fan_out=5,
        )
        assert obj.lifecycle_phase == "draft"

    def test_empty_nodes_valid(self) -> None:
        obj = DAGTopologyManifest(nodes={}, edges=[], max_depth=10, max_fan_out=5)
        assert len(obj.nodes) == 0

    @given(n=st.integers(min_value=2, max_value=8))
    @settings(max_examples=10, deadline=None)
    def test_linear_chain_depth_equals_n(self, n: int) -> None:
        """A linear chain of n nodes has depth n (longest path + 1)."""
        nodes = {f"did:z:{i}": _agent() for i in range(n)}
        edges = [(f"did:z:{i}", f"did:z:{i + 1}") for i in range(n - 1)]
        obj = DAGTopologyManifest(
            nodes=nodes,  # type: ignore[arg-type]
            edges=edges,
            allow_cycles=False,
            max_depth=n,
            max_fan_out=5,
        )
        assert len(obj.edges) == n - 1


# ---------------------------------------------------------------------------
# Pure-Python fallback branch
# ---------------------------------------------------------------------------


class TestDAGTopologyManifestPurePython:
    """Monkeypatch _HAS_RUSTWORKX to False to exercise pure-Python DAG path."""

    def test_cycle_detected_pure_python(self) -> None:
        with (
            patch("coreason_manifest.spec.ontology._HAS_RUSTWORKX", False),
            pytest.raises((ValidationError, EpistemicTopologicalParadoxFalsificationEvent)),
        ):
            DAGTopologyManifest(
                nodes={
                    "did:z:a": _agent(),
                    "did:z:b": _system(),
                },
                edges=[("did:z:a", "did:z:b"), ("did:z:b", "did:z:a")],
                allow_cycles=False,
                max_depth=10,
                max_fan_out=5,
            )

    def test_valid_dag_pure_python(self) -> None:
        with patch("coreason_manifest.spec.ontology._HAS_RUSTWORKX", False):
            obj = DAGTopologyManifest(
                nodes={
                    "did:z:a": _agent(),
                    "did:z:b": _system(),
                    "did:z:c": _system(),
                },
                edges=[("did:z:a", "did:z:b"), ("did:z:b", "did:z:c")],
                allow_cycles=False,
                max_depth=10,
                max_fan_out=5,
            )
            assert len(obj.nodes) == 3

    def test_depth_exceeded_pure_python(self) -> None:
        with (
            patch("coreason_manifest.spec.ontology._HAS_RUSTWORKX", False),
            pytest.raises(ValidationError, match="exceeds max_depth"),
        ):
            DAGTopologyManifest(
                nodes={
                    "did:z:a": _agent(),
                    "did:z:b": _system(),
                    "did:z:c": _system(),
                    "did:z:d": _system(),
                },
                edges=[
                    ("did:z:a", "did:z:b"),
                    ("did:z:b", "did:z:c"),
                    ("did:z:c", "did:z:d"),
                ],
                allow_cycles=False,
                max_depth=2,
                max_fan_out=5,
            )
