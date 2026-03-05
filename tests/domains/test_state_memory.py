import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.state.events import (
    AnyStateEvent,
    BeliefUpdateEvent,
    ObservationEvent,
    SystemFaultEvent,
)
from coreason_manifest.state.memory import EpistemicLedger
from coreason_manifest.state.toolchains import BrowserStateSnapshot, TerminalStateSnapshot


@st.composite
def state_event_strategy(draw: st.DrawFn) -> AnyStateEvent:
    event_type = draw(st.sampled_from(["observation", "belief_update", "system_fault"]))
    event_id = draw(st.text(min_size=1, max_size=50))
    timestamp = draw(st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False))

    if event_type == "observation":
        return ObservationEvent(event_id=event_id, timestamp=timestamp, type="observation")
    if event_type == "belief_update":
        return BeliefUpdateEvent(event_id=event_id, timestamp=timestamp, type="belief_update")
    return SystemFaultEvent(event_id=event_id, timestamp=timestamp, type="system_fault")


@given(st.lists(state_event_strategy(), min_size=1, max_size=100))
def test_temporal_chaos_proof(events: list[AnyStateEvent]) -> None:
    # 1. The Temporal Chaos Proof
    ledger = EpistemicLedger(history=events)

    # Assert sorted by timestamp
    for i in range(len(ledger.history) - 1):
        assert ledger.history[i].timestamp <= ledger.history[i + 1].timestamp


@given(st.text(min_size=1000).map(lambda s: s * 11))
def test_buffer_spillage_proof(large_buffer: str) -> None:
    # 2. The Buffer Spillage Proof
    with pytest.raises(ValidationError) as exc_info:
        TerminalStateSnapshot(cwd="/valid/path", stdout_buffer=large_buffer)

    assert "stdout_buffer" in str(exc_info.value)
    assert "String should have at most 10000 characters" in str(exc_info.value)


@given(st.one_of(
    st.text().map(lambda s: f"..{s}"),
    st.text().map(lambda s: f"{s}.."),
    st.text().map(lambda s: f"\0{s}"),
    st.text().map(lambda s: f"{s}\0"),
    st.text().map(lambda s: f"foo{s}../bar"),
))
def test_path_traversal_proof(adversarial_cwd: str) -> None:
    # 3. The Path Traversal Proof
    assume(".." in adversarial_cwd or "\0" in adversarial_cwd)

    with pytest.raises(ValidationError) as exc_info:
        TerminalStateSnapshot(cwd=adversarial_cwd, stdout_buffer="normal")

    assert "cwd" in str(exc_info.value)
    assert "Path traversal or null bytes are strictly forbidden in cwd." in str(exc_info.value)


@given(st.text())
def test_protocol_smuggling_proof(adversarial_url: str) -> None:
    # 4. The Protocol Smuggling Proof
    assume(not adversarial_url.startswith("http://") and not adversarial_url.startswith("https://"))

    with pytest.raises(ValidationError) as exc_info:
        BrowserStateSnapshot(current_url=adversarial_url, dom_hash="fakehash123")

    assert "current_url" in str(exc_info.value)
    assert "String should match pattern" in str(exc_info.value)
