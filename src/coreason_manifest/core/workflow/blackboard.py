import asyncio
import time

from coreason_manifest.core.state.events import EpistemicEvent
from coreason_manifest.core.state.ledger import EpistemicLedger


class BlackboardBroker:
    """
    An async pub/sub broker for an event-driven Blackboard orchestration system.
    """

    def __init__(self, ledger: EpistemicLedger) -> None:
        self.ledger = ledger
        self.subscribers: dict[str, list[asyncio.Queue[EpistemicEvent]]] = {}
        # Stores the current claims: event_id -> (agent_signature, expiry_timestamp)
        self.claims: dict[str, tuple[str, float]] = {}
        # Mutex to prevent thundering herd race condition during claim_task
        self.claim_lock = asyncio.Lock()

    async def subscribe(self, event_type: str, queue: asyncio.Queue[EpistemicEvent]) -> None:
        """
        Subscribes a queue to a specific event type.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(queue)

    async def publish(self, event: EpistemicEvent) -> None:
        """
        Appends the event to the ledger and dynamically pushes it to all subscribed queues.
        """
        # 1. Append to ledger
        await self.ledger.aappend(event)

        # 2. Push to subscribed queues
        event_type = str(event.event_type)
        if event_type in self.subscribers:
            for queue in self.subscribers[event_type]:
                await queue.put(event)

    async def claim_task(self, event_id: str, agent_signature: str, ttl_seconds: int = 30) -> bool:
        """
        Attempts to claim a task (event) exclusively.
        Uses asyncio.Lock to prevent Thundering Herd race conditions.
        Maintains task leases via TTL.
        """
        async with self.claim_lock:
            current_time = time.time()
            # Check if the task is already claimed and the lease is still valid
            if event_id in self.claims:
                _, expiry = self.claims[event_id]
                if current_time < expiry:
                    # Task is currently claimed by someone else (or even the same agent, but still locked)
                    return False
                # If expiry is in the past, the lock has expired, and we can reclaim it.

            # Claim the task
            self.claims[event_id] = (agent_signature, current_time + ttl_seconds)
            return True
