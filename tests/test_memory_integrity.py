import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError
from coreason_manifest.spec.core.memory import (
    WorkingMemoryConfig,
    EpisodicMemoryConfig,
)
from coreason_manifest.spec.interop.telemetry import MemoryMutationEvent

def test_working_memory_boundaries():
    """Test strict boundaries for WorkingMemoryConfig."""
    # Valid
    config = WorkingMemoryConfig(max_tokens=1024, enable_active_paging=True)
    assert config.max_tokens == 1024

    # Invalid: max_tokens <= 0
    with pytest.raises(ValidationError):
        WorkingMemoryConfig(max_tokens=0, enable_active_paging=True)

    with pytest.raises(ValidationError):
        WorkingMemoryConfig(max_tokens=-100, enable_active_paging=True)

def test_episodic_memory_boundaries():
    """Test strict boundaries for EpisodicMemoryConfig."""
    # Valid
    config = EpisodicMemoryConfig(salience_threshold=0.5, consolidation_interval_turns=10)
    assert config.salience_threshold == 0.5
    assert config.consolidation_interval_turns == 10

    # Invalid: salience_threshold < 0.0 or > 1.0
    with pytest.raises(ValidationError):
        EpisodicMemoryConfig(salience_threshold=-0.1)

    with pytest.raises(ValidationError):
        EpisodicMemoryConfig(salience_threshold=1.1)

    # Invalid: consolidation_interval_turns <= 0
    with pytest.raises(ValidationError):
        EpisodicMemoryConfig(salience_threshold=0.5, consolidation_interval_turns=0)

def test_memory_mutation_event_integrity():
    """Test MemoryMutationEvent with new integrity fields."""
    event = MemoryMutationEvent(
        parent_request_id=str(uuid4()),
        root_request_id=str(uuid4()),
        tier="working",
        operation="EVICT",
        mutation_payload={"tokens": 100},
        timestamp=datetime.now(),
        # New fields
        parent_hash="abc123hash",
        mutation_hash="def456hash"
    )

    assert event.hash_version == "v2"
    assert event.parent_hash == "abc123hash"
    assert event.mutation_hash == "def456hash"
    assert "mutation_hash" in event._hash_exclude_
