import asyncio
from typing import Literal

from pydantic import Field

from coreason_manifest.core.state.events import EpistemicEvent, EventType
from coreason_manifest.core.workflow.bidding import Bid
from coreason_manifest.core.workflow.blackboard import BlackboardBroker
from coreason_manifest.core.workflow.nodes.etl.base_etl import ETLNode


class SemanticNode(ETLNode):
    type: Literal["semantic_node"] = Field("semantic_node", description="The type of the node.")  # type: ignore

    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        if event.event_type == EventType.STRUCTURAL_PARSED:
            return Bid(score=0.9, agent_signature=self.hardware_profile)
        return Bid(score=0.0, agent_signature=self.hardware_profile)

    async def watch_board(self, broker: BlackboardBroker, event_type: str = str(EventType.STRUCTURAL_PARSED)) -> None:
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
