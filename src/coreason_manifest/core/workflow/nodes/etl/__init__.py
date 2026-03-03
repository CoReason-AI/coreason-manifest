import asyncio
from abc import ABC, abstractmethod

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

    @abstractmethod
    async def watch_board(self) -> None:
        pass

    @abstractmethod
    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        pass


class SemanticNode(BaseNode):
    """
    Watches for STRUCTURAL_MILESTONE events.
    """

    @abstractmethod
    async def watch_board(self) -> None:
        pass

    @abstractmethod
    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        pass


class AuditorNode(BaseNode):
    """
    Watches for SEMANTIC_MILESTONE events.
    """

    @abstractmethod
    async def watch_board(self) -> None:
        pass

    @abstractmethod
    def evaluate_capability(self, event: EpistemicEvent) -> Bid:
        pass
