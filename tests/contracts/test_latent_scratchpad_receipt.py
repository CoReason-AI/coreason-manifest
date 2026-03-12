import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import LatentScratchpadReceipt, ThoughtBranchState


def test_latent_scratchpad_receipt_valid() -> None:
    branch_1 = ThoughtBranchState(branch_id="branch_1", latent_content_hash="a" * 64, prm_score=0.9)
    branch_2 = ThoughtBranchState(branch_id="branch_2", latent_content_hash="b" * 64, prm_score=0.8)

    receipt = LatentScratchpadReceipt(
        trace_id="trace_123",
        explored_branches=[branch_1, branch_2],
        discarded_branches=["branch_2"],
        resolution_branch_id="branch_1",
        total_latent_tokens=100,
    )

    assert receipt.trace_id == "trace_123"
    assert len(receipt.explored_branches) == 2
    assert receipt.discarded_branches == ["branch_2"]
    assert receipt.resolution_branch_id == "branch_1"


def test_latent_scratchpad_receipt_resolution_branch_missing() -> None:
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
    branch_1 = ThoughtBranchState(branch_id="branch_1", latent_content_hash="a" * 64, prm_score=0.9)

    with pytest.raises(ValidationError, match="discarded branch 'branch_invalid' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="trace_123",
            explored_branches=[branch_1],
            discarded_branches=["branch_invalid"],
            resolution_branch_id=None,
            total_latent_tokens=100,
        )
