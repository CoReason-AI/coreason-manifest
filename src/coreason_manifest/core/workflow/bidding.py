from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.suspense import SkeletonType, SuspenseConfig
from coreason_manifest.core.state.events import EpistemicEvent
from coreason_manifest.core.telemetry.suspense_envelope import StreamSuspenseEnvelope


class Bid(CoreasonModel):
    score: float = Field(..., description="Capability score (0.0 to 1.0) of the node for this task.")
    agent_signature: str = Field(..., description="The unique hardware/agent signature submitting the bid.")


class SuspenseEnvelopeFallback(CoreasonModel):
    event_id: str
    reason: str
    highest_bid: float


class CapabilityRouter:
    def __init__(self, suspense_threshold: float = 0.5) -> None:
        self.suspense_threshold = suspense_threshold

    async def offer_task(self, event: EpistemicEvent, nodes: list[Any]) -> Any:
        best_bid = None
        winning_node = None

        for node in nodes:
            if hasattr(node, "evaluate_capability"):
                bid = node.evaluate_capability(event)
                if bid and (best_bid is None or bid.score > best_bid.score):
                    best_bid = bid
                    winning_node = node

        if best_bid is None or best_bid.score < self.suspense_threshold:
            return StreamSuspenseEnvelope(
                op="suspense_mount",
                p=SuspenseConfig(fallback_type=SkeletonType.SPINNER),
                trace_id=f"suspense-{event.event_id}",
                timestamp=datetime.now(UTC).timestamp(),
            )

        return winning_node
