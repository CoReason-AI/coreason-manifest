# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for StochasticTopologyManifestManifestManifest, HypothesisSuperpositionStateStateState, and StochasticNodeState."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    HypothesisSuperpositionStateStateState,
    IdeationPhaseProfileProfile,
    StochasticNodeState,
    StochasticTopologyManifestManifestManifest,
)

CID_ST = st.from_regex(r"[a-zA-Z0-9_.:-]{1,30}", fullmatch=True)
ENTROPY_ST = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


class TestStochasticNodeState:
    """Exercise epistemic entropy field_validator."""

    @given(cid=CID_ST, entropy=ENTROPY_ST)
    @settings(max_examples=20, deadline=None)
    def test_valid_entropy_accepted(self, cid: str, entropy: float) -> None:
        node = StochasticNodeState(
            node_cid=cid,
            agent_role="generator",
            stochastic_tensor="test-tensor",
            epistemic_entropy=entropy,
        )
        assert 0.0 <= node.epistemic_entropy <= 1.0

    def test_entropy_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StochasticNodeState(
                node_cid="n1",
                agent_role="generator",
                stochastic_tensor="tensor",
                epistemic_entropy=-0.1,
            )

    def test_entropy_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StochasticNodeState(
                node_cid="n1",
                agent_role="generator",
                stochastic_tensor="tensor",
                epistemic_entropy=1.1,
            )


class TestHypothesisSuperpositionStateStateState:
    """Exercise probability conservation and canonical sort validators."""

    def test_valid_superposition(self) -> None:
        hss = HypothesisSuperpositionStateStateState(
            superposition_cid="sp1",
            competing_manifolds={"a": 0.5, "b": 0.3},
            wave_collapse_function="plurality_vote",
        )
        assert sum(hss.competing_manifolds.values()) <= 1.0

    def test_probability_exceeds_one(self) -> None:
        with pytest.raises(ValidationError, match="Conservation of Probability"):
            HypothesisSuperpositionStateStateState(
                superposition_cid="sp2",
                competing_manifolds={"a": 0.6, "b": 0.5},
                wave_collapse_function="highest_confidence",
            )

    def test_residual_entropy_vectors_sorted(self) -> None:
        hss = HypothesisSuperpositionStateStateState(
            superposition_cid="sp3",
            competing_manifolds={"x": 0.2},
            wave_collapse_function="deterministic_compiler",
            residual_entropy_vectors=["zebra", "alpha", "middle"],
        )
        assert hss.residual_entropy_vectors == ["alpha", "middle", "zebra"]

    @given(
        probs=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghij"),
            values=st.floats(min_value=0.0, max_value=0.25, allow_nan=False),
            min_size=1,
            max_size=4,
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_low_probabilities_always_valid(self, probs: dict[str, float]) -> None:
        hss = HypothesisSuperpositionStateStateState(
            superposition_cid="sp-gen",
            competing_manifolds=probs,
            wave_collapse_function="plurality_vote",
        )
        assert sum(hss.competing_manifolds.values()) <= 1.0 + 1e-9


class TestStochasticTopologyManifestManifestManifest:
    """Exercise acyclic DAG integrity and canonical sort validators."""

    def _make_node(self, cid: str, parent: str | None = None) -> StochasticNodeState:
        return StochasticNodeState(
            node_cid=cid,
            agent_role="generator",
            stochastic_tensor="tensor",
            epistemic_entropy=0.5,
            parent_node_cid=parent,
        )

    def test_valid_dag(self) -> None:
        stm = StochasticTopologyManifestManifestManifest(
            topology_cid="t1",
            phase=IdeationPhaseProfileProfile.STOCHASTIC_DIFFUSION,
            stochastic_graph=[
                self._make_node("a"),
                self._make_node("b", "a"),
            ],
        )
        assert stm.stochastic_graph[0].node_cid <= stm.stochastic_graph[1].node_cid

    def test_parent_before_child_ordering(self) -> None:
        with pytest.raises(ValidationError, match="must appear before child"):
            StochasticTopologyManifestManifestManifest(
                topology_cid="t2",
                phase=IdeationPhaseProfileProfile.MANIFOLD_COLLAPSE,
                stochastic_graph=[
                    self._make_node("b", "a"),
                    self._make_node("a"),
                ],
            )

    def test_single_root_node(self) -> None:
        stm = StochasticTopologyManifestManifestManifest(
            topology_cid="t3",
            phase=IdeationPhaseProfileProfile.STOCHASTIC_DIFFUSION,
            stochastic_graph=[self._make_node("root")],
        )
        assert len(stm.stochastic_graph) == 1

    def test_canonical_sort_applied(self) -> None:
        stm = StochasticTopologyManifestManifestManifest(
            topology_cid="t4",
            phase=IdeationPhaseProfileProfile.STOCHASTIC_DIFFUSION,
            stochastic_graph=[
                self._make_node("c"),
                self._make_node("a"),
                self._make_node("b"),
            ],
        )
        cids = [n.node_cid for n in stm.stochastic_graph]
        assert cids == sorted(cids)
