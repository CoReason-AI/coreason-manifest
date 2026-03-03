from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from coreason_manifest.core.state.events import (
    EpistemicAnchor,
    EpistemicEvent,
    EventType,
)
from coreason_manifest.core.state.ledger import EpistemicLedger
from coreason_manifest.core.state.projections import DocumentTextProjection


def test_epistemic_event_utc_validation() -> None:
    # Non-UTC timezone should raise error
    with pytest.raises(ValidationError):
        EpistemicEvent(
            event_id="test-1",
            timestamp=datetime.now(),  # naive local time
            context_envelope={"agent_signature": "agent1"},
            event_type=EventType.STRUCTURAL_PARSED,
            payload={},
            epistemic_anchor=EpistemicAnchor(),
        )

    # UTC timezone should pass
    event = EpistemicEvent(
        event_id="test-1",
        timestamp=datetime.now(UTC),
        context_envelope={"agent_signature": "agent1"},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={},
        epistemic_anchor=EpistemicAnchor(),
    )
    assert event.timestamp.tzinfo == UTC


def test_ledger_append_idempotency() -> None:
    ledger = EpistemicLedger()
    event = EpistemicEvent(
        event_id="unique-id-123",
        timestamp=datetime.now(UTC),
        context_envelope={"agent_signature": "agent1"},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={},
        epistemic_anchor=EpistemicAnchor(),
    )

    ledger.append(event)
    assert len(ledger.get_events()) == 1

    # Appending the exact same event by ID should be idempotent
    ledger.append(event)
    assert len(ledger.get_events()) == 1


@pytest.mark.asyncio
async def test_ledger_aappend() -> None:
    ledger = EpistemicLedger()
    event = EpistemicEvent(
        event_id="async-id-123",
        timestamp=datetime.now(UTC),
        context_envelope={"agent_signature": "agent1"},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={},
        epistemic_anchor=EpistemicAnchor(),
    )

    await ledger.aappend(event)
    assert len(ledger.get_events()) == 1


def test_ledger_out_of_order_causal_sorting() -> None:
    ledger = EpistemicLedger()
    base_time = datetime.now(UTC)

    event1 = EpistemicEvent(
        event_id="event-1",
        timestamp=base_time,
        context_envelope={},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={},
        epistemic_anchor=EpistemicAnchor(),
    )
    event2 = EpistemicEvent(
        event_id="event-2",
        timestamp=base_time + timedelta(seconds=1),
        context_envelope={},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={},
        epistemic_anchor=EpistemicAnchor(),
    )
    event3 = EpistemicEvent(
        event_id="event-3",
        timestamp=base_time + timedelta(seconds=2),
        context_envelope={},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={},
        epistemic_anchor=EpistemicAnchor(),
    )

    # Append out of order
    ledger.append(event3)
    ledger.append(event1)
    ledger.append(event2)

    events = ledger.get_events()
    assert len(events) == 3
    # Check that events are sorted by timestamp (causal order)
    assert events[0].event_id == "event-1"
    assert events[1].event_id == "event-2"
    assert events[2].event_id == "event-3"


def test_document_text_projection() -> None:
    ledger = EpistemicLedger()
    base_time = datetime.now(UTC)

    event1 = EpistemicEvent(
        event_id="event-1",
        timestamp=base_time,
        context_envelope={},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={"text_block": "Hello"},
        epistemic_anchor=EpistemicAnchor(),
    )
    event2 = EpistemicEvent(
        event_id="event-2",
        timestamp=base_time + timedelta(seconds=1),
        context_envelope={},
        event_type=EventType.SEMANTIC_EXTRACTED,
        payload={"extracted_entity": "World"},
        epistemic_anchor=EpistemicAnchor(),
    )
    event3 = EpistemicEvent(
        event_id="event-3",
        timestamp=base_time + timedelta(seconds=2),
        context_envelope={},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={"text_block": "World"},
        epistemic_anchor=EpistemicAnchor(),
    )

    ledger.append(event3)
    ledger.append(event1)
    ledger.append(event2)  # This should be ignored by the projection

    projection = ledger.project(DocumentTextProjection)

    assert isinstance(projection, DocumentTextProjection)
    assert projection.blocks_processed == 2
    assert projection.aggregated_text == "Hello\nWorld"


def test_fallback_project() -> None:
    ledger = EpistemicLedger()
    from datetime import datetime

    base_time = datetime.now(UTC)

    event1 = EpistemicEvent(
        event_id="event-1",
        timestamp=base_time,
        context_envelope={},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={"text_block": "Hello"},
        epistemic_anchor=EpistemicAnchor(),
    )
    ledger.append(event1)

    def dummy_projection(events: list[EpistemicEvent]) -> int:
        return len(events)

    result = ledger.project(dummy_projection)  # type: ignore
    assert result == 1
