from typing import Any

from coreason_manifest.core.state.events import EpistemicEvent


class EpistemicLedger:
    """
    The central CRDT (Conflict-Free Replicated Data Type) memory object.
    It holds an append-only sequence of EpistemicEvent objects.
    """

    def __init__(self) -> None:
        # We store events in a dictionary mapped by event_id to maintain O(1) idempotency checks
        self._events: dict[str, EpistemicEvent] = {}

    def append(self, event: EpistemicEvent) -> None:
        """
        Asynchronously appends an event.
        Idempotency: if the same event (by event_id) is appended twice, it handles it gracefully.
        """
        # If the event already exists, we ignore it (idempotent append)
        if event.event_id not in self._events:
            self._events[event.event_id] = event

    async def aappend(self, event: EpistemicEvent) -> None:
        """
        Asynchronous out-of-order event appending.
        """
        self.append(event)

    def get_events(self) -> list[EpistemicEvent]:
        """
        Returns all events sorted by causal order (timestamp).
        """
        return sorted(self._events.values(), key=lambda e: e.timestamp)

    def project(self, projection_class: type[Any]) -> Any:
        """
        Replays the event stream in causal order and folds it into a single Pydantic state model
        using the provided projection class.
        """
        ordered_events = self.get_events()
        # The projection class handles the folding/aggregating logic via the .project() classmethod.
        if hasattr(projection_class, "project"):
            return projection_class.project(ordered_events)
        return projection_class(ordered_events)
