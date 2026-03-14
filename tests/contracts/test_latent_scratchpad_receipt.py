# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import LatentScratchpadReceipt, ThoughtBranchState


# 1. Fuzzing Array Sorting Determinism
@st.composite
def valid_scratchpad_strategy(draw: st.DrawFn) -> dict[str, Any]:
    """Generates mathematically guaranteed valid branch matrices to test sorting determinism."""
    # Generate chaotic, unsorted branch IDs
    branch_ids = draw(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=15, unique=True))

    explored = [ThoughtBranchState(branch_id=b_id, latent_content_hash="a" * 64, prm_score=0.9) for b_id in branch_ids]

    discarded = draw(st.lists(st.sampled_from(branch_ids), max_size=len(branch_ids), unique=True))
    resolution_id = draw(st.one_of(st.none(), st.sampled_from(branch_ids)))

    return {"explored_branches": explored, "discarded_branches": discarded, "resolution_branch_id": resolution_id}


@given(data=valid_scratchpad_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_latent_scratchpad_receipt_fuzz_sorting_determinism(data: dict[str, Any]) -> None:
    """
    AGENT INSTRUCTION: Prove that explored and discarded branches are mathematically
    sorted regardless of input order, guaranteeing canonical hashing determinism.
    """
    receipt = LatentScratchpadReceipt(
        trace_id="trace_fuzz_1",
        explored_branches=data["explored_branches"],
        discarded_branches=data["discarded_branches"],
        resolution_branch_id=data["resolution_branch_id"],
        total_latent_tokens=100,
    )

    # Assert deterministic sorting
    assert [b.branch_id for b in receipt.explored_branches] == sorted([b.branch_id for b in data["explored_branches"]])
    assert receipt.discarded_branches == sorted(data["discarded_branches"])


# 2. Atomic Error Tests for Referential Integrity
def test_latent_scratchpad_receipt_resolution_branch_missing() -> None:
    """Prove that the orchestrator rejects resolution branches not found in the explored matrix."""
    branch_1 = ThoughtBranchState(branch_id="branch_1", latent_content_hash="a" * 64, prm_score=0.9)

    with pytest.raises(ValidationError, match="resolution_branch_id 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="trace_123",
            explored_branches=[branch_1],
            discarded_branches=[],
            resolution_branch_id="branch_invalid",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_discarded_branch_missing() -> None:
    """Prove that the orchestrator rejects discarded branches not found in the explored matrix."""
    branch_1 = ThoughtBranchState(branch_id="branch_1", latent_content_hash="a" * 64, prm_score=0.9)

    with pytest.raises(ValidationError, match="discarded branch 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="trace_123",
            explored_branches=[branch_1],
            discarded_branches=["branch_invalid"],
            resolution_branch_id=None,
            total_latent_tokens=100,
        )
