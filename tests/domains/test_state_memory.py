from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.state.events import (
    AnyStateEvent,
    BeliefUpdateEvent,
    ObservationEvent,
    SystemFaultEvent,
)
from coreason_manifest.state.memory import EpistemicLedger


@st.composite
def state_event_strategy(draw: st.DrawFn) -> AnyStateEvent:
    event_type = draw(st.sampled_from(["observation", "belief_update", "system_fault"]))
    event_id = draw(st.text(min_size=1, max_size=50))
    timestamp = draw(st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False))
    payload = draw(
        st.dictionaries(
            st.text(),
            st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans()),
            max_size=5,
        )
    )

    if event_type == "observation":
        return ObservationEvent(event_id=event_id, timestamp=timestamp, type="observation", payload=payload)
    if event_type == "belief_update":
        return BeliefUpdateEvent(event_id=event_id, timestamp=timestamp, type="belief_update", payload=payload)
    return SystemFaultEvent(event_id=event_id, timestamp=timestamp, type="system_fault")


@given(st.lists(state_event_strategy(), min_size=1, max_size=100))
def test_temporal_chaos_proof(events: list[AnyStateEvent]) -> None:
    # 1. The Temporal Chaos Proof
    ledger = EpistemicLedger(history=events)

    # Assert sorted by timestamp
    for i in range(len(ledger.history) - 1):
        assert ledger.history[i].timestamp <= ledger.history[i + 1].timestamp
