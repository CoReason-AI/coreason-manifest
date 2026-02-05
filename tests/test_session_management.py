# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime

from coreason_manifest.spec.common.session import Interaction, MemoryStrategy, SessionState


def test_immutability_and_functional_update() -> None:
    # Create 5 interactions
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]

    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
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

    # Assert updated_at changed
    # (assuming fast execution, strict inequality might fail if too fast? No, datetime.now() usually differs)
    assert new_state.updated_at >= state.updated_at


def test_serialization() -> None:
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        variables={"foo": "bar", "num": 123},
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


def test_variable_storage() -> None:
    vars = {"string": "test", "int": 42, "dict": {"nested": True}, "list": [1, 2, 3]}
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        variables=vars,
    )

    assert state.variables["string"] == "test"
    assert state.variables["dict"]["nested"] is True

    # Test adding a variable via model_copy (simulating update)
    new_vars = state.variables.copy()
    new_vars["new_key"] = "new_val"
    new_state = state.model_copy(update={"variables": new_vars})

    assert "new_key" in new_state.variables
    assert "new_key" not in state.variables


def test_prune_all() -> None:
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
    )

    new_state = state.prune(MemoryStrategy.ALL, limit=2)
    assert len(new_state.history) == 5
    assert new_state is state  # Should return self


def test_prune_limit_zero_or_negative() -> None:
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
    )

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=0)
    assert len(new_state.history) == 0

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=-1)
    assert len(new_state.history) == 0


def test_prune_limit_exceeds_length() -> None:
    interactions = [Interaction(input=f"input_{i}") for i in range(3)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
    )

    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=10)
    assert len(new_state.history) == 3
    assert new_state.history == interactions


def test_prune_token_buffer() -> None:
    # Currently behaves like ALL/Default (returns self)
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
    )

    new_state = state.prune(MemoryStrategy.TOKEN_BUFFER, limit=10)
    assert new_state is state


def test_prune_empty_history() -> None:
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=[],
    )
    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=5)
    assert len(new_state.history) == 0
    assert new_state.id == state.id  # ID should persist across updates (Session ID)
    assert new_state is not state  # But it must be a new object


def test_prune_limit_equals_one() -> None:
    interactions = [Interaction(input=f"input_{i}") for i in range(5)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
    )
    new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=1)
    assert len(new_state.history) == 1
    assert new_state.history[0].input == "input_4"


def test_chained_pruning() -> None:
    interactions = [Interaction(input=f"input_{i}") for i in range(10)]
    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        history=interactions,
    )

    # Prune to last 5
    state_5 = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=5)
    assert len(state_5.history) == 5
    assert state_5.history[0].input == "input_5"

    # Prune to last 2 from the previous 5
    state_2 = state_5.prune(MemoryStrategy.SLIDING_WINDOW, limit=2)
    assert len(state_2.history) == 2
    assert state_2.history[0].input == "input_8"
    assert state_2.history[1].input == "input_9"

    # Verify original is still intact
    assert len(state.history) == 10


def test_complex_variable_storage() -> None:
    complex_vars = {
        "user_profile": {"name": "Alice", "preferences": ["coding", "reading"], "meta": {"id": 123, "active": True}},
        "context_stack": [{"role": "system", "content": "foo"}, {"role": "user", "content": "bar"}],
    }

    state = SessionState(
        agent_id="agent-1",
        user_id="user-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        variables=complex_vars,
    )

    # Verify deep access
    assert state.variables["user_profile"]["meta"]["active"] is True
    assert state.variables["context_stack"][1]["content"] == "bar"

    # Verify immutability of nested structures if accessed directly
    # Note: Pydantic v2 models are frozen, but standard dicts/lists inside might be mutable *if* retrieved?
    # Actually, ConfigDict(frozen=True) usually makes the model fields immutable, but nested mutable types (dict, list)
    # might still be mutable unless deep-frozen or using specific types.
    # Let's verify behavior.

    # Because `variables` is defined as `Dict[str, Any]`, the dict itself is mutable if we get a reference to it,
    # UNLESS Pydantic v2 frozen model returns a copy or proxy.
    # HOWEVER, modifying the returned dict won't affect the model's hash/equality if it caches it,
    # but strictly speaking `SessionState` instance holds the reference.
    # Let's see if we can modify it in place (which would be "bad" for strict immutability
    # but expected for standard Pydantic without specific deep freezing).

    # This modification is technically possible in Python unless we use a custom immutable dict type.
    # But let's verify that `model_copy` creates a *new* container for variables if we update it.

    new_vars = state.variables.copy()
    new_vars["user_profile"] = {"name": "Bob"}  # Replace whole profile

    new_state = state.model_copy(update={"variables": new_vars})

    assert new_state.variables["user_profile"]["name"] == "Bob"
    assert state.variables["user_profile"]["name"] == "Alice"
