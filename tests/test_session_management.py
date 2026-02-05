# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from datetime import UTC, datetime

from coreason_manifest import MemoryStrategy, SessionState
from coreason_manifest.spec.common.session import Interaction


def test_session_state_immutability_and_pruning() -> None:
    """Test that SessionState is immutable and prune returns a new instance."""
    # Create 5 interactions
    history = [Interaction(input=f"message {i}") for i in range(5)]

    state = SessionState(
        agent_id="test_agent",
        user_id="test_user",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=history,
        variables={"foo": "bar"},
    )

    assert len(state.history) == 5

    # Prune
    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=2)

    # Assert
    assert len(new_state.history) == 2
    assert new_state.history[0].input == "message 3"
    assert new_state.history[1].input == "message 4"

    # Verify immutability of original
    assert len(state.history) == 5
    assert state.history[0].input == "message 0"

    # Verify ID match
    assert new_state.id == state.id

    # Verify updated_at changed
    assert new_state.updated_at > state.updated_at

    # Verify ALL strategy
    same_state = state.prune(MemoryStrategy.ALL, limit=2)
    assert same_state is state  # Should return self if optimized, or equal


def test_session_serialization() -> None:
    """Test serialization of SessionState."""
    history = [Interaction(input="test")]
    variables = {"key": "value", "number": 42, "nested": {"a": 1}}

    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=history,
        variables=variables,
    )

    json_str = state.model_dump_json()
    data = json.loads(json_str)

    assert data["agent_id"] == "agent-1"
    assert data["user_id"] == "user-1"
    assert len(data["history"]) == 1
    assert data["history"][0]["input"] == "test"
    assert data["variables"]["key"] == "value"
    assert data["variables"]["number"] == 42
    assert data["variables"]["nested"]["a"] == 1


def test_variable_storage() -> None:
    """Verify variables can store arbitrary JSON-serializable data."""
    complex_vars = {"string": "s", "int": 10, "float": 3.14, "bool": True, "list": [1, 2, 3], "dict": {"x": "y"}}

    state = SessionState(
        agent_id="agent",
        user_id="user",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        variables=complex_vars,
    )

    assert state.variables["list"] == [1, 2, 3]
    assert state.variables["dict"]["x"] == "y"

    # Verify we can dump and load back
    dumped = state.model_dump()
    assert dumped["variables"] == complex_vars


def test_prune_unsupported_strategy() -> None:
    """Test pruning with unsupported strategy returns self."""
    state = SessionState(
        agent_id="agent",
        user_id="user",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=[Interaction(input="msg")],
    )

    # Token buffer not implemented here
    new_state = state.prune(MemoryStrategy.TOKEN_BUFFER, limit=10)
    assert new_state is state


def test_sliding_window_zero_limit() -> None:
    """Test sliding window with limit <= 0 clears history."""
    history = [Interaction(input="msg") for _ in range(3)]
    state = SessionState(
        agent_id="a", user_id="u", created_at=datetime.now(UTC), updated_at=datetime.now(UTC), history=history
    )

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=0)
    assert len(new_state.history) == 0

    new_state_neg = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=-1)
    assert len(new_state_neg.history) == 0
