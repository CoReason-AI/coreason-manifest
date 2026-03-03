import asyncio
from typing import Literal

from pydantic import Field

from coreason_manifest.core.state.events import EpistemicEvent
from coreason_manifest.core.workflow.bidding import Bid
from coreason_manifest.core.workflow.blackboard import BlackboardBroker
from coreason_manifest.core.workflow.nodes.agent import AgentNode


class ETLNode(AgentNode):
    type: Literal["etl"] = Field("etl", description="The type of the node.")  # type: ignore
    hardware_profile: str = Field(..., description="The hardware capabilities of this node.")

    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        _ = event
        return Bid(score=0.0, agent_signature=self.hardware_profile)

    async def watch_board(self, broker: BlackboardBroker, event_type: str) -> None:
        queue: asyncio.Queue[EpistemicEvent] = asyncio.Queue()
        await broker.subscribe(event_type, queue)

        while True:
            event = await queue.get()
            bid = self.evaluate_capability(event)
            if bid.score > 0.5:
                claimed = await broker.claim_task(event.event_id, self.hardware_profile)
                if claimed:
                    pass
            queue.task_done()
