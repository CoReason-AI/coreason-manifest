# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Critical last-mile tests for the remaining largest uncovered blocks.

These tests specifically target the DocumentLayoutManifest DAG validator
and other large contiguous blocks that are close to pushing us over 95%.
"""

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    LatentSmoothingProfile,
    MultimodalTokenAnchorState,
    SaeLatentPolicy,
)


def _anchor() -> MultimodalTokenAnchorState:
    return MultimodalTokenAnchorState()


def _block(cid: str, cls: str = "paragraph") -> DocumentLayoutRegionState:
    return DocumentLayoutRegionState(block_cid=cid, block_class=cls, anchor=_anchor())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# DocumentLayoutManifest.verify_dag_and_integrity — 26 lines (4688-4713)
# ---------------------------------------------------------------------------


class TestDocumentLayoutManifestDAG:
    """Exercise the DAG validator with edges, invalid refs, and cycles."""

    def test_valid_dag_with_edges(self) -> None:
        obj = DocumentLayoutManifest(
            blocks={"b1": _block("b1"), "b2": _block("b2", "header"), "b3": _block("b3")},
            chronological_flow_edges=[("b1", "b2"), ("b2", "b3")],
        )
        assert len(obj.blocks) == 3

    def test_invalid_source_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Source block"):
            DocumentLayoutManifest(
                blocks={"b1": _block("b1")},
                chronological_flow_edges=[("missing", "b1")],
            )

    def test_invalid_target_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Target block"):
            DocumentLayoutManifest(
                blocks={"b1": _block("b1")},
                chronological_flow_edges=[("b1", "missing")],
            )

    def test_cycle_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cyclical"):
            DocumentLayoutManifest(
                blocks={"b1": _block("b1")},
                chronological_flow_edges=[("b1", "b1")],
            )

    def test_diamond_dag(self) -> None:
        """Diamond shape is valid DAG: b1->b2, b1->b3, b2->b4, b3->b4."""
        obj = DocumentLayoutManifest(
            blocks={
                "b1": _block("b1"),
                "b2": _block("b2"),
                "b3": _block("b3"),
                "b4": _block("b4"),
            },
            chronological_flow_edges=[("b1", "b2"), ("b1", "b3"), ("b2", "b4"), ("b3", "b4")],
        )
        assert len(obj.chronological_flow_edges) == 4


# ---------------------------------------------------------------------------
# SaeLatentPolicy — validate_smooth_decay (8 lines at 2555-2562)
# ---------------------------------------------------------------------------


class TestSaeLatentPolicy:
    """Exercise smooth_decay conditional validator."""

    def test_smooth_decay_requires_profile(self) -> None:
        with pytest.raises(ValidationError, match="smoothing_profile"):
            SaeLatentPolicy(
                monitored_hook_points=["blocks.0.hook_resid_post"],
                target_feature_index=42,
                max_activation_threshold=1.0,
                violation_action="smooth_decay",
                sae_dictionary_hash="a" * 64,
                smoothing_profile=None,
                clamp_value=None,
            )

    def test_smooth_decay_requires_clamp_value(self) -> None:
        with pytest.raises(ValidationError, match="clamp_value"):
            SaeLatentPolicy(
                monitored_hook_points=["blocks.0.hook_resid_post"],
                target_feature_index=42,
                max_activation_threshold=1.0,
                violation_action="smooth_decay",
                sae_dictionary_hash="a" * 64,
                smoothing_profile=LatentSmoothingProfile(
                    transition_window_tokens=100,
                    decay_function="exponential",
                ),
                clamp_value=None,
            )


# ---------------------------------------------------------------------------
# _pure_python_is_dag — fallback path (never reached when rustworkx is installed)
# ---------------------------------------------------------------------------


class TestPurePythonDAG:
    """Directly exercise the pure Python DAG checker for coverage."""

    def test_valid_dag(self) -> None:
        from coreason_manifest.spec.ontology import _pure_python_is_dag

        adjacency = {"a": ["b"], "b": ["c"], "c": []}
        assert _pure_python_is_dag(adjacency) is True

    def test_cycle(self) -> None:
        from coreason_manifest.spec.ontology import _pure_python_is_dag

        adjacency = {"a": ["b"], "b": ["a"]}
        assert _pure_python_is_dag(adjacency) is False

    def test_self_loop(self) -> None:
        from coreason_manifest.spec.ontology import _pure_python_is_dag

        adjacency = {"a": ["a"]}
        assert _pure_python_is_dag(adjacency) is False

    def test_empty_graph(self) -> None:
        from coreason_manifest.spec.ontology import _pure_python_is_dag

        adjacency: dict[str, list[str]] = {}
        assert _pure_python_is_dag(adjacency) is True


# ---------------------------------------------------------------------------
# _inject_* schema cluster functions (dead code) — lines 485-509
# ---------------------------------------------------------------------------


class TestInjectClusterFunctions:
    """Directly exercise the cluster injection functions for coverage."""

    def test_inject_spatial_cluster(self) -> None:
        from coreason_manifest.spec.ontology import _inject_spatial_cluster

        schema: dict[str, object] = {}
        _inject_spatial_cluster(schema)
        assert schema["x-domain-cluster"] == "spatial_kinematics"

    def test_inject_epistemic_cluster(self) -> None:
        from coreason_manifest.spec.ontology import _inject_epistemic_cluster

        schema: dict[str, object] = {}
        _inject_epistemic_cluster(schema)
        assert schema["x-domain-cluster"] == "epistemic_ledger"

    def test_inject_cognitive_routing_cluster(self) -> None:
        from coreason_manifest.spec.ontology import _inject_cognitive_routing_cluster

        schema: dict[str, object] = {}
        _inject_cognitive_routing_cluster(schema)
        assert schema["x-domain-cluster"] == "cognitive_routing"

    def test_inject_thermodynamic_cluster(self) -> None:
        from coreason_manifest.spec.ontology import _inject_thermodynamic_cluster

        schema: dict[str, object] = {}
        _inject_thermodynamic_cluster(schema)
        assert schema["x-domain-cluster"] == "thermodynamic_orchestration"
