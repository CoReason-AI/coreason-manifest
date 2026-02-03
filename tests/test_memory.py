# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.memory import MemoryConfig, MemoryStrategy
from coreason_manifest.definitions.session import (
    Interaction,
    SessionContext,
    SessionState,
    TraceContext,
    UserContext,
)


def create_dummy_session(interaction_count: int = 10) -> SessionState:
    session_id = uuid4()
    agent_id = uuid4()

    context = SessionContext(
        session_id=session_id,
        agent_id=agent_id,
        user=UserContext(user_id="user-1", email="test@example.com", tier="free", locale="en-US"),
        trace=TraceContext(trace_id=uuid4(), span_id=uuid4(), parent_id=None),
        permissions=["read", "write"],
        created_at=datetime.now(timezone.utc),
    )

    processor = Identity(id="agent-1", name="Agent 1", role="assistant")

    session = SessionState(context=context, processor=processor, last_updated_at=datetime.now(timezone.utc), history=[])

    for i in range(interaction_count):
        interaction = Interaction(input={"content": f"msg {i}"}, output={"content": f"reply {i}"})
        session = session.add_interaction(interaction)

    return session


def test_agent_definition_with_memory_config() -> None:
    """Test that AgentDefinition accepts a MemoryConfig."""
    # We construct a minimal valid AgentDefinition
    # This requires constructing a lot of nested objects.
    # To save effort, we can try to validate just the AgentRuntimeConfig
    # if we can, but AgentDefinition validation is stricter.

    # Let's check if we can just test AgentRuntimeConfig directly first as it's the one modified.
    from coreason_manifest.definitions.agent import AgentRuntimeConfig, ModelConfig

    mem_config = MemoryConfig(strategy=MemoryStrategy.SLIDING_WINDOW, limit=5, summary_prompt="Summarize me")

    runtime_config = AgentRuntimeConfig(
        nodes=[], edges=[], llm_config=ModelConfig(model="gpt-4", temperature=0.5), memory=mem_config
    )

    assert runtime_config.memory is not None
    assert runtime_config.memory.strategy == MemoryStrategy.SLIDING_WINDOW
    assert runtime_config.memory.limit == 5
    assert runtime_config.memory.summary_prompt == "Summarize me"


def test_prune_sliding_window() -> None:
    """Test pruning with SLIDING_WINDOW strategy."""
    session = create_dummy_session(interaction_count=10)
    assert len(session.history) == 10

    # Prune to last 5
    pruned_session = session.prune(MemoryStrategy.SLIDING_WINDOW, limit=5)

    assert len(pruned_session.history) == 5

    # Check that we have the LAST 5 interactions (indices 5, 6, 7, 8, 9)
    # The input content was "msg {i}"
    assert isinstance(pruned_session.history[0].input, dict)
    assert pruned_session.history[0].input["content"] == "msg 5"
    assert isinstance(pruned_session.history[4].input, dict)
    assert pruned_session.history[4].input["content"] == "msg 9"

    # Check context preservation
    assert pruned_session.context.session_id == session.context.session_id
    assert pruned_session.processor.id == session.processor.id

    # Check immutability of original session
    assert len(session.history) == 10
    assert isinstance(session.history[0].input, dict)
    assert session.history[0].input["content"] == "msg 0"


def test_prune_sliding_window_limit_larger_than_history() -> None:
    """Test pruning when limit is larger than history size."""
    session = create_dummy_session(interaction_count=5)

    # Prune to last 10 (should keep all 5)
    pruned_session = session.prune(MemoryStrategy.SLIDING_WINDOW, limit=10)

    assert len(pruned_session.history) == 5
    assert isinstance(pruned_session.history[0].input, dict)
    assert pruned_session.history[0].input["content"] == "msg 0"


def test_prune_sliding_window_limit_zero() -> None:
    """Test pruning with limit 0 (should clear history)."""
    session = create_dummy_session(interaction_count=5)

    pruned_session = session.prune(MemoryStrategy.SLIDING_WINDOW, limit=0)

    assert len(pruned_session.history) == 0


def test_prune_unsupported_strategy() -> None:
    """Test pruning with unsupported strategies raises NotImplementedError."""
    session = create_dummy_session(interaction_count=5)

    with pytest.raises(NotImplementedError) as excinfo:
        session.prune(MemoryStrategy.SUMMARY, limit=5)

    assert "Kernel only supports SLIDING_WINDOW pruning" in str(excinfo.value)

    with pytest.raises(NotImplementedError):
        session.prune(MemoryStrategy.VECTOR_STORE, limit=5)

    with pytest.raises(NotImplementedError):
        session.prune(MemoryStrategy.TOKEN_BUFFER, limit=5)
