import asyncio
from datetime import UTC, datetime

from coreason_manifest.core.state.events import EpistemicEvent
from coreason_manifest.core.state.ledger import EpistemicLedger


class BlackboardBroker:
    """
    The Event-Driven Pub/Sub system acting as the Blackboard.
    Agents watch a shared Epistemic Ledger and opportunistically claim tasks.
    """

    def __init__(self, ledger: EpistemicLedger) -> None:
        self.ledger = ledger
        self._subscribers: dict[str, list[asyncio.Queue[EpistemicEvent]]] = {}
        self._locks: dict[str, tuple[str, float]] = {}
        self._mutex = asyncio.Lock()

    async def subscribe(self, event_type: str, queue: asyncio.Queue[EpistemicEvent]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(queue)

    async def publish(self, event: EpistemicEvent) -> None:
        await self.ledger.aappend(event)
        event_type = str(event.event_type)
        if event_type in self._subscribers:
            for queue in self._subscribers[event_type]:
                await queue.put(event)

    async def claim_task(self, event_id: str, agent_signature: str, ttl_seconds: int = 30) -> bool:
        now = datetime.now(UTC).timestamp()
        async with self._mutex:
            if event_id in self._locks:
                current_owner, expiry = self._locks[event_id]
                if now < expiry and current_owner != agent_signature:
                    return False
            self._locks[event_id] = (agent_signature, now + ttl_seconds)
            return True
