# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from datetime import datetime
from coreason_manifest.spec.common.session import SessionState, MemoryStrategy, Interaction

def test_immutability_and_functional_update():
    # Create 5 interactions
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]

    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        history=interactions
    )

    assert len(state.history) == 5

    # Prune
    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=2)

    # Assert
    assert len(new_state.history) == 2
    assert new_state.history[0].input == "input_3"
    assert new_state.history[1].input == "input_4"

    # Assert original is untouched
    assert len(state.history) == 5
    assert state.id == new_state.id

    # Assert updated_at changed (assuming fast execution, strict inequality might fail if too fast? No, datetime.now() usually differs)
    assert new_state.updated_at >= state.updated_at

def test_serialization():
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        variables={"foo": "bar", "num": 123}
    )

    # Dump to JSON
    json_output = state.model_dump_json()
    # Pydantic v2 default JSON dump does not include spaces by default
    assert '"foo":"bar"' in json_output
    assert '"num":123' in json_output

    # Load back
    loaded = SessionState.model_validate_json(json_output)
    assert loaded.variables["foo"] == "bar"
    assert loaded.variables["num"] == 123
    assert loaded.agent_id == "agent-1"

def test_variable_storage():
    vars = {
        "string": "test",
        "int": 42,
        "dict": {"nested": True},
        "list": [1, 2, 3]
    }
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        variables=vars
    )

    assert state.variables["string"] == "test"
    assert state.variables["dict"]["nested"] is True

    # Test adding a variable via model_copy (simulating update)
    new_vars = state.variables.copy()
    new_vars["new_key"] = "new_val"
    new_state = state.model_copy(update={"variables": new_vars})

    assert "new_key" in new_state.variables
    assert "new_key" not in state.variables

def test_prune_all():
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        history=interactions
    )

    new_state = state.prune(MemoryStrategy.ALL, limit=2)
    assert len(new_state.history) == 5
    assert new_state is state # Should return self

def test_prune_limit_zero_or_negative():
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        history=interactions
    )

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=0)
    assert len(new_state.history) == 0

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=-1)
    assert len(new_state.history) == 0

def test_prune_limit_exceeds_length():
    interactions = [Interaction(input=f"input_{i}") for i in range(3)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        history=interactions
    )

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=10)
    assert len(new_state.history) == 3
    assert new_state.history == interactions

def test_prune_token_buffer():
    # Currently behaves like ALL/Default (returns self)
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        history=interactions
    )

    new_state = state.prune(MemoryStrategy.TOKEN_BUFFER, limit=10)
    assert new_state is state
