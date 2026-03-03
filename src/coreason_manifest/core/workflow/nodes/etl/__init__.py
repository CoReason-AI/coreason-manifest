import asyncio
from abc import ABC, abstractmethod
from typing import Any

from coreason_manifest.core.state.events import EpistemicEvent
from coreason_manifest.core.workflow.bidding import Bid


class BaseNode(ABC):
    """
    Abstract base class for all ETL Hardware-Aligned Nodes.
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        # Note: In practice, this would be an asyncio.Queue instance created per node
        # or passed in during subscription, which holds EpistemicEvent objects.
        self.queue: asyncio.Queue[EpistemicEvent] = asyncio.Queue()

    @abstractmethod
    async def watch_board(self) -> None:
        """
        Continuously pulls from its specific asyncio.Queue to process events.
        """

    @abstractmethod
    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        """
        Returns a Bid object estimating capability for the given event.
        """


class ExtractorNode(BaseNode):
    """
    Watches for raw document upload events.
    """

    async def watch_board(self) -> None:
        while True:
            _ = await self.queue.get()
            # Simulate processing the event
            await asyncio.sleep(0.1)
            self.queue.task_done()

    def evaluate_capability(self, event: EpistemicEvent | Any) -> Bid:
        # The argument event is purposefully unused in this simulation,
        # but kept to satisfy the interface.
        _ = event
        return Bid(node_id=self.node_id, confidence_score=0.85)


class SemanticNode(BaseNode):
    """
    Watches for STRUCTURAL_MILESTONE events.
    """

    async def watch_board(self) -> None:
        while True:
            _ = await self.queue.get()
            # Simulate processing the event
            await asyncio.sleep(0.1)
            self.queue.task_done()

    def evaluate_capability(self, event: EpistemicEvent | Any) -> Bid:
        _ = event
        return Bid(node_id=self.node_id, confidence_score=0.85)


class AuditorNode(BaseNode):
    """
    Watches for SEMANTIC_MILESTONE events.
    """

    async def watch_board(self) -> None:
        while True:
            _ = await self.queue.get()
            # Simulate processing the event
            await asyncio.sleep(0.1)
            self.queue.task_done()

    def evaluate_capability(self, event: EpistemicEvent | Any) -> Bid:
        _ = event
        return Bid(node_id=self.node_id, confidence_score=0.85)
