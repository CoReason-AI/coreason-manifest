# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    IdeationPhase,
    LatentScratchpadReceipt,
    StochasticTopology,
    ThoughtBranchState,
)


@st.composite
def valid_scratchpad_strategy(draw: st.DrawFn) -> dict[str, Any]:
    branch_ids = draw(
        st.lists(st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True), min_size=2, max_size=15, unique=True)
    )
    explored = []
    for b_cid in branch_ids:
        if draw(st.booleans()):
            explored.append(ThoughtBranchState(branch_cid=b_cid, latent_content_hash="a" * 64, prm_score=0.9))
        else:
            explored.append(
                StochasticTopology(topology_cid=b_cid, phase=IdeationPhase.STOCHASTIC_DIFFUSION, stochastic_graph=[])
            )
    discarded = draw(st.lists(st.sampled_from(branch_ids), max_size=len(branch_ids), unique=True))
    resolution_cid = draw(st.one_of(st.none(), st.sampled_from(branch_ids)))
    return {"explored_branches": explored, "discarded_branches": discarded, "resolution_branch_cid": resolution_cid}


@given(data=valid_scratchpad_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_latent_scratchpad_receipt_fuzz_sorting_determinism(data: dict[str, Any]) -> None:
    receipt = LatentScratchpadReceipt(
        trace_cid="trace_fuzz_1",
        explored_branches=data["explored_branches"],
        discarded_branches=data["discarded_branches"],
        resolution_branch_cid=data["resolution_branch_cid"],
        total_latent_tokens=100,
    )
    assert [
        getattr(b, "branch_cid", getattr(b, "topology_cid", "unknown")) for b in receipt.explored_branches
    ] == sorted([getattr(b, "branch_cid", getattr(b, "topology_cid", "unknown")) for b in data["explored_branches"]])
    assert receipt.discarded_branches == sorted(data["discarded_branches"])


def test_latent_scratchpad_receipt_resolution_branch_missing() -> None:
    branch_1 = ThoughtBranchState(branch_cid="branch_1", latent_content_hash="a" * 64, prm_score=0.9)
    with pytest.raises(ValidationError, match="resolution_branch_cid 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_cid="trace_123",
            explored_branches=[branch_1],
            discarded_branches=[],
            resolution_branch_cid="branch_invalid",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_discarded_branch_missing() -> None:
    branch_1 = ThoughtBranchState(branch_cid="branch_1", latent_content_hash="a" * 64, prm_score=0.9)
    with pytest.raises(ValidationError, match="discarded branch 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_cid="trace_123",
            explored_branches=[branch_1],
            discarded_branches=["branch_invalid"],
            resolution_branch_cid=None,
            total_latent_tokens=100,
        )
