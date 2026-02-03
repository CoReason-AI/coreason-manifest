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
from pydantic import ValidationError

from coreason_manifest.definitions.events import GraphEventNodeInit, NodeInit
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.session import Interaction, SessionState


def test_interaction_creation() -> None:
    """Test successful creation of an Interaction."""
    interaction = Interaction(
        input={"role": "user", "content": "hello"},
        output={"role": "assistant", "content": "hi"},
    )
    assert interaction.interaction_id is not None
    assert interaction.timestamp is not None
    assert isinstance(interaction.input, dict)
    assert interaction.input["content"] == "hello"
    assert interaction.output["content"] == "hi"
    assert interaction.events == []
    assert interaction.meta == {}


def test_interaction_with_events() -> None:
    """Test Interaction with GraphEvents."""
    payload = NodeInit(node_id="node-1", type="AGENT", visual_cue="THINKING")
    event = GraphEventNodeInit(
        event_type="NODE_INIT",
        run_id="run-1",
        trace_id="trace-1",
        node_id="node-1",
        timestamp=1234567890.0,
        payload=payload,
        visual_metadata={"color": "#FFFFFF"},
    )

    interaction = Interaction(input={"foo": "bar"}, output={"baz": "qux"}, events=[event])
    assert len(interaction.events) == 1
    assert interaction.events[0].event_type == "NODE_INIT"


def test_session_state_creation() -> None:
    """Test successful creation of a SessionState."""
    session_id = uuid4()
    now = datetime.now(timezone.utc)

    processor = Identity(id="agent-1", name="Agent 1", role="assistant")
    user = Identity(id="user-1", name="User 1", role="user")

    session = SessionState(
        session_id=session_id,
        processor=processor,
        user=user,
        created_at=now,
        last_updated_at=now,
    )

    assert session.session_id == session_id
    assert session.processor == processor
    assert session.processor.id == "agent-1"
    assert session.user == user
    assert session.user.id == "user-1"
    assert session.created_at == now
    assert session.last_updated_at == now
    assert session.history == []
    assert session.context_variables == {}


def test_session_state_immutability() -> None:
    """Test that SessionState is immutable (frozen)."""
    session_id = uuid4()
    now = datetime.now(timezone.utc)

    processor = Identity(id="agent-1", name="Agent 1", role="assistant")

    session = SessionState(
        session_id=session_id,
        processor=processor,
        created_at=now,
        last_updated_at=now,
    )

    with pytest.raises(ValidationError):  # Pydantic v2 raises ValidationError or TypeError depending on config
        session.processor = Identity(id="agent-2", name="Agent 2")

    # Note: session.history is a list, so append() works at runtime even if frozen=True.
    # frozen=True only prevents field reassignment.
    # To test frozen properly, we check field reassignment.
    with pytest.raises(ValidationError):
        session.history = []

    # Better test for frozen:
    with pytest.raises(ValidationError):
        session.user = Identity.anonymous()


def test_add_interaction() -> None:
    """Test add_interaction method."""
    session_id = uuid4()
    now = datetime.now(timezone.utc)

    processor = Identity(id="agent-1", name="Agent 1", role="assistant")

    session = SessionState(
        session_id=session_id,
        processor=processor,
        created_at=now,
        last_updated_at=now,
    )

    interaction = Interaction(input={"a": 1}, output={"b": 2})

    new_session = session.add_interaction(interaction)

    # Original session should be unchanged
    assert len(session.history) == 0

    # New session should have the interaction
    assert len(new_session.history) == 1
    assert new_session.history[0] == interaction

    # Last updated should be updated (greater than or equal to original)
    assert new_session.last_updated_at >= session.last_updated_at

    # Other fields should be preserved
    assert new_session.session_id == session.session_id
    assert new_session.processor == session.processor


def test_serialization() -> None:
    """Test JSON serialization."""
    interaction = Interaction(input={"k": "v"}, output={"x": "y"})
    json_str = interaction.to_json()
    # Check key presence without relying on exact whitespace
    assert '"k":"v"' in json_str.replace(" ", "")
    assert '"x":"y"' in json_str.replace(" ", "")
