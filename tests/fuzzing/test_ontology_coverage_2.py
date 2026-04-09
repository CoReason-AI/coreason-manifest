# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import math

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DynamicLayoutManifest,
    EnsembleTopologyProfile,
    EpistemicArgumentClaimState,
    EvictionPolicy,
    EvidentiaryWarrantState,
    MultimodalTokenAnchorState,
)


@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(st.integers(min_value=1, max_value=2))
def test_dynamic_layout_manifest_ast_complexity(budget: int) -> None:
    # A string that evaluates to f"{a} {b}" and creates multiple AST nodes
    test_str = "{a} {b} {c} {d} {e} {f} {g}"
    with pytest.raises(ValidationError, match="AST Complexity Overload"):
        DynamicLayoutManifest(layout_tstring=test_str, max_ast_node_budget=budget)


@given(
    st.sampled_from(
        [(math.nan, 0.0, 0.0, 0.0), (0.0, math.nan, 0.0, 0.0), (0.0, 0.0, math.nan, 0.0), (0.0, 0.0, 0.0, math.nan)]
    )
)
def test_multimodal_token_anchor_state_nan(bbox: tuple[float, float, float, float]) -> None:
    with pytest.raises(ValidationError, match="Spatial bounds cannot be NaN"):
        MultimodalTokenAnchorState(bounding_box=bbox)


@given(
    st.sampled_from(
        [(math.inf, 0.0, 1.0, 1.0), (0.0, math.inf, 1.0, 1.0), (0.0, 0.0, math.inf, 1.0), (0.0, 0.0, 0.0, math.inf)]
    )
)
def test_multimodal_token_anchor_state_inf(bbox: tuple[float, float, float, float]) -> None:
    with pytest.raises(ValidationError, match="Spatial bounds cannot be Infinity"):
        MultimodalTokenAnchorState(bounding_box=bbox)


@given(st.lists(st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True), min_size=2, max_size=5))
def test_ensemble_topology_profile_sorting(dids: list[str]) -> None:
    prof = EnsembleTopologyProfile(concurrent_branch_cids=dids, fusion_function="weighted_consensus")
    assert prof.concurrent_branch_cids == sorted(dids)


@given(st.lists(st.text(min_size=1, max_size=128), min_size=1, max_size=5))
def test_eviction_policy_sorting(cids: list[str]) -> None:
    policy = EvictionPolicy(strategy="fifo", max_retained_tokens=1000, protected_event_cids=cids)
    assert policy.protected_event_cids == sorted(cids)


@given(st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=5))
def test_epistemic_argument_claim_state_sorting(justifications: list[str]) -> None:
    warrants = [EvidentiaryWarrantState(justification=j) for j in justifications]
    claim = EpistemicArgumentClaimState(
        claim_cid="claim_1", proponent_cid="proponent_1", text_chunk="text chunk", warrants=warrants
    )
    # The warrants should be sorted by the justification field
    assert [w.justification for w in claim.warrants] == sorted(justifications)
