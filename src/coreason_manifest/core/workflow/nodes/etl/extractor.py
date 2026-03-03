import asyncio
from typing import Literal

from pydantic import Field

from coreason_manifest.core.state.events import EpistemicEvent, EventType
from coreason_manifest.core.workflow.bidding import Bid
from coreason_manifest.core.workflow.blackboard import BlackboardBroker
from coreason_manifest.core.workflow.nodes.etl.base_etl import ETLNode


class ExtractorNode(ETLNode):
    type: Literal["extractor_node"] = Field("extractor_node", description="The type of the node.")  # type: ignore

    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        # Check against EventType string value or enum
        raw_doc_enum = getattr(EventType, "RAW_DOCUMENT", "RAW_DOCUMENT")
        if str(event.event_type) == "RAW_DOCUMENT" or event.event_type == raw_doc_enum:
            return Bid(score=1.0, agent_signature=self.hardware_profile)
        return Bid(score=0.0, agent_signature=self.hardware_profile)

    async def watch_board(self, broker: BlackboardBroker, event_type: str = "RAW_DOCUMENT") -> None:
        queue: asyncio.Queue[EpistemicEvent] = asyncio.Queue()
        await broker.subscribe(event_type, queue)

        while True:
            event = await queue.get()
            bid = self.evaluate_capability(event)
            if bid.score > 0.0:
                claimed = await broker.claim_task(event.event_id, self.hardware_profile)
                if claimed:
                    pass
            queue.task_done()
