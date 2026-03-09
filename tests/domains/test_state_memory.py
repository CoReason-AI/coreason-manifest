import pytest
from pydantic import ValidationError

from coreason_manifest.state.memory import (
    EpisodicTraceMemory,
    LatentWorkingMemory,
    SemanticCrystallization,
)


def test_latent_working_memory_oom_alarm() -> None:
    # Valid
    mem = LatentWorkingMemory(
        node_id="did:web:test",
        max_ttl_seconds=3600,
        max_context_window_tokens=1000,
        current_tokens=500,
        state_envelope=["some", "state"],
    )
    assert mem.current_tokens == 500

    # Invalid - Exceeds context bounds
    with pytest.raises(ValidationError) as exc_info:
        LatentWorkingMemory(
            node_id="did:web:test",
            max_ttl_seconds=3600,
            max_context_window_tokens=1000,
            current_tokens=1001,
            state_envelope=["some", "state"],
        )
    assert "OOM ALARM" in str(exc_info.value)


def test_episodic_trace_memory_byzantine_fault() -> None:
    # Valid
    trace = EpisodicTraceMemory(
        trace_id="trace_1", node_id="did:web:test", events=[], parent_hash="abc", merkle_root="valid_root"
    )
    assert trace.merkle_root == "valid_root"

    # Invalid - Missing Merkle Root (empty string triggers validation in this schema structure)
    with pytest.raises(ValidationError) as exc_info:
        EpisodicTraceMemory(trace_id="trace_1", node_id="did:web:test", events=[], parent_hash="abc", merkle_root="")
    assert "Byzantine Fault" in str(exc_info.value)


def test_semantic_crystallization_economic_validation() -> None:
    # Valid
    cryst = SemanticCrystallization(
        axiom_id="ax_1",
        source_trace_id="trace_1",
        aleatoric_entropy_threshold=0.5,
        entropy_delta_score=0.6,
        semantic_payload="fact",
    )
    assert cryst.entropy_delta_score >= cryst.aleatoric_entropy_threshold

    # Invalid - Entropy delta score below threshold
    with pytest.raises(ValidationError) as exc_info:
        SemanticCrystallization(
            axiom_id="ax_1",
            source_trace_id="trace_1",
            aleatoric_entropy_threshold=0.5,
            entropy_delta_score=0.4,
            semantic_payload="fact",
        )
    assert "Economic Validation Failed" in str(exc_info.value)
