# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AnyStateEvent,
    BeliefUpdateEvent,
    CrystallizationPolicy,
    EpistemicLedger,
    ObservationEvent,
    SystemFaultEvent,
    TheoryOfMindSnapshot,
    WorkingMemorySnapshot,
)


def test_crystallization_policy_min_observations() -> None:
    # Valid
    CrystallizationPolicy(
        min_observations_required=10,
        aleatoric_entropy_threshold=0.1,
        target_memory_tier="semantic",
    )

    # Invalid
    with pytest.raises(ValidationError, match="Input should be greater than or equal to 10"):
        CrystallizationPolicy(
            min_observations_required=9,
            aleatoric_entropy_threshold=0.1,
            target_memory_tier="semantic",
        )


def test_crystallization_policy_entropy_threshold() -> None:
    # Valid
    CrystallizationPolicy(
        min_observations_required=10,
        aleatoric_entropy_threshold=0.05,
        target_memory_tier="semantic",
    )

    # Invalid
    with pytest.raises(ValidationError, match=r"Input should be less than or equal to 0\.1"):
        CrystallizationPolicy(
            min_observations_required=10,
            aleatoric_entropy_threshold=0.11,
            target_memory_tier="semantic",
        )


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


@st.composite
def draw_theory_of_mind_snapshot(draw: st.DrawFn) -> TheoryOfMindSnapshot:
    return TheoryOfMindSnapshot(
        target_agent_id=draw(st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)),
        assumed_shared_beliefs=draw(st.lists(st.text())),
        identified_knowledge_gaps=draw(st.lists(st.text())),
        empathy_confidence_score=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
    )


@given(st.text(), st.dictionaries(st.text(), st.text()), st.lists(draw_theory_of_mind_snapshot(), max_size=5))
def test_working_memory_theory_of_mind(
    system_prompt: str, active_context: dict[str, str], theory_of_mind_models: list[TheoryOfMindSnapshot]
) -> None:
    snapshot = WorkingMemorySnapshot(
        system_prompt=system_prompt,
        active_context=active_context,
        theory_of_mind_models=theory_of_mind_models,
    )
    assert snapshot.system_prompt == system_prompt
    assert snapshot.active_context == active_context
    assert snapshot.theory_of_mind_models == sorted(theory_of_mind_models, key=lambda x: x.target_agent_id)
