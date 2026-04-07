# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import hypothesis.strategies as st
import pytest
from hypothesis import given
from pydantic import AnyUrl, ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveCritiqueProfile,
    ContextualizedSourceEntity,
    DerivationMode,
    EpistemicProvenanceReceipt,
    InterventionIntent,
    InterventionPolicy,
    TerminalCognitiveFailure,
)


@given(loops=st.integers(min_value=101))
def test_epistemic_sealing_bounds(loops: int) -> None:
    with pytest.raises(ValidationError) as exc:
        EpistemicProvenanceReceipt(
            extracted_by="did:coreason:test1",
            source_event_cid="test-event-id",
            derivation_mode=DerivationMode.DIRECT_TRANSLATION,
            revision_loops_executed=loops,
        )
    assert "Input should be less than or equal to 100" in str(exc.value)


@given(loops=st.integers(min_value=0, max_value=100))
def test_epistemic_sealing_bounds_valid(loops: int) -> None:
    receipt = EpistemicProvenanceReceipt(
        extracted_by="did:coreason:test1",
        source_event_cid="test-event-id",
        derivation_mode=DerivationMode.DIRECT_TRANSLATION,
        revision_loops_executed=loops,
    )
    assert receipt.revision_loops_executed == loops


def test_hotl_telemetry_policy_gate() -> None:
    with pytest.raises(ValidationError) as exc:
        InterventionPolicy(trigger="on_start", emit_telemetry_on_revision=True, async_observation_port=None)
    assert (
        "HOTL Misconfiguration: Cannot emit shadow telemetry without defining a valid async_observation_port."
        in str(exc.value)
    )

    # Valid
    policy = InterventionPolicy(
        trigger="on_start",
        emit_telemetry_on_revision=True,
        async_observation_port=AnyUrl("wss://telemetry.coreason.ai/hotl"),
    )
    assert policy.emit_telemetry_on_revision is True
    assert str(policy.async_observation_port) == "wss://telemetry.coreason.ai/hotl"


def test_terminal_handoff_isomorphism() -> None:
    source_entity = ContextualizedSourceEntity(
        target_string="test string", contextual_envelope=[], source_system_provenance_flag=False
    )
    critique = CognitiveCritiqueProfile(reasoning_trace_hash="a" * 64, epistemic_penalty_scalar=0.5)

    failure = TerminalCognitiveFailure(
        source_entity=source_entity,
        last_rejected_hypothesis_hash="b" * 64,
        final_critique_schema=critique,
        loops_exhausted=100,
    )

    intent = InterventionIntent(
        target_node_cid="did:coreason:test2",
        context_summary="Terminal failure",
        proposed_action={},
        adjudication_deadline=123456789.0,
        failure_context=failure,
    )

    assert intent.failure_context is not None
    assert intent.failure_context.loops_exhausted == 100
