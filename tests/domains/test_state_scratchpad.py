# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import LatentScratchpadTrace, ThoughtBranch


def test_latent_scratchpad_trace_valid() -> None:
    branch1 = ThoughtBranch(
        branch_id="b1",
        latent_content_hash="a" * 64,
        prm_score=0.9,
    )
    branch2 = ThoughtBranch(
        branch_id="b2",
        parent_branch_id="b1",
        latent_content_hash="b" * 64,
        prm_score=0.4,
    )

    trace = LatentScratchpadTrace(
        trace_id="t1",
        explored_branches=[branch1, branch2],
        discarded_branches=["b2"],
        resolution_branch_id="b1",
        total_latent_tokens=150,
    )

    assert trace.trace_id == "t1"
    assert trace.resolution_branch_id == "b1"


def test_latent_scratchpad_trace_invalid_resolution_branch() -> None:
    branch1 = ThoughtBranch(
        branch_id="b1",
        latent_content_hash="a" * 64,
    )

    with pytest.raises(ValidationError) as exc:
        LatentScratchpadTrace(
            trace_id="t1",
            explored_branches=[branch1],
            discarded_branches=[],
            resolution_branch_id="ghost_b",
            total_latent_tokens=150,
        )

    assert "resolution_branch_id 'ghost_b' not found in explored_branches." in str(exc.value)


def test_latent_scratchpad_trace_invalid_discarded_branch() -> None:
    branch1 = ThoughtBranch(
        branch_id="b1",
        latent_content_hash="a" * 64,
    )

    with pytest.raises(ValidationError) as exc:
        LatentScratchpadTrace(
            trace_id="t1",
            explored_branches=[branch1],
            discarded_branches=["ghost_b"],
            resolution_branch_id="b1",
            total_latent_tokens=150,
        )

    assert "discarded branch 'ghost_b' not found in explored_branches." in str(exc.value)
