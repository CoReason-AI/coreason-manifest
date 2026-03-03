import time

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.suspense import SkeletonType, SuspenseConfig
from coreason_manifest.core.state.ledger import EpistemicLedger
from coreason_manifest.core.telemetry.suspense_envelope import StreamSuspenseEnvelope


class Bid(CoreasonModel):
    """
    A bid placed by a node to claim a task.
    """

    node_id: str = Field(..., description="The ID of the node placing the bid.")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="The confidence score of the node to handle the task, from 0.0 to 1.0."
    )


def yield_to_suspense(bids: list[Bid], ledger: EpistemicLedger, threshold: float = 0.5) -> StreamSuspenseEnvelope | Bid:
    """
    Evaluates bids and returns the highest bid if it meets the threshold.
    If no bid meets the threshold, returns a SuspenseEnvelope yielding to human oversight.
    """
    if not bids:
        return StreamSuspenseEnvelope(
            op="suspense_mount",
            p=SuspenseConfig(fallback_type=SkeletonType.SPINNER),
            timestamp=time.time(),
            ledger_history_snapshot=ledger.get_history(),
        )

    best_bid = max(bids, key=lambda b: b.confidence_score)

    if best_bid.confidence_score < threshold:
        return StreamSuspenseEnvelope(
            op="suspense_mount",
            p=SuspenseConfig(fallback_type=SkeletonType.SPINNER),
            timestamp=time.time(),
            ledger_history_snapshot=ledger.get_history(),
        )

    return best_bid
