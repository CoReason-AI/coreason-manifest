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
from typing import Optional
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.events import GraphEventNodeInit, NodeInit
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.session import (
    Interaction,
    SessionContext,
    SessionState,
    TraceContext,
    UserContext,
)


def create_default_context(
    session_id: UUID, agent_id: UUID, user_id: str = "user-1", trace_id: Optional[UUID] = None
) -> SessionContext:
    if trace_id is None:
        trace_id = uuid4()

    return SessionContext(
        session_id=session_id,
        agent_id=agent_id,
        user=UserContext(user_id=user_id, email="test@example.com", tier="free", locale="en-US"),
        trace=TraceContext(trace_id=trace_id, span_id=uuid4(), parent_id=None),
        permissions=["read", "write"],
        created_at=datetime.now(timezone.utc),
    )


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

    context = create_default_context(session_id, uuid4(), user.id)

    session = SessionState(
        session_id=session_id,
        context=context,
        processor=processor,
        user=user,
        created_at=now,
        last_updated_at=now,
    )

    assert session.session_id == session_id
    assert session.context == context
    assert session.context.user.user_id == "user-1"
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
    context = create_default_context(session_id, uuid4())

    session = SessionState(
        session_id=session_id,
        context=context,
        processor=processor,
        created_at=now,
        last_updated_at=now,
    )

    with pytest.raises(ValidationError):  # Pydantic v2 raises ValidationError or TypeError depending on config
        session.processor = Identity(id="agent-2", name="Agent 2")  # type: ignore[misc]

    # Note: session.history is a list, so append() works at runtime even if frozen=True.
    # frozen=True only prevents field reassignment.
    # To test frozen properly, we check field reassignment.
    with pytest.raises(ValidationError):
        session.history = []  # type: ignore[misc]

    # Better test for frozen:
    with pytest.raises(ValidationError):
        session.user = Identity.anonymous()  # type: ignore[misc]


def test_add_interaction() -> None:
    """Test add_interaction method."""
    session_id = uuid4()
    now = datetime.now(timezone.utc)

    processor = Identity(id="agent-1", name="Agent 1", role="assistant")
    context = create_default_context(session_id, uuid4())

    session = SessionState(
        session_id=session_id,
        context=context,
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
    assert new_session.context == session.context
    assert new_session.processor == session.processor


def test_serialization() -> None:
    """Test JSON serialization."""
    interaction = Interaction(input={"k": "v"}, output={"x": "y"})
    json_str = interaction.to_json()
    # Check key presence without relying on exact whitespace
    assert '"k":"v"' in json_str.replace(" ", "")
    assert '"x":"y"' in json_str.replace(" ", "")


def test_session_context_serialization() -> None:
    """Test serialization of SessionContext."""
    session_id = uuid4()
    agent_id = uuid4()
    trace_id = uuid4()
    span_id = uuid4()

    user_context = UserContext(user_id="user-123", email="test@test.com", tier="pro", locale="fr-FR")

    trace_context = TraceContext(trace_id=trace_id, span_id=span_id, parent_id=None)

    now = datetime.now(timezone.utc)

    context = SessionContext(
        session_id=session_id,
        agent_id=agent_id,
        user=user_context,
        trace=trace_context,
        permissions=["search:read"],
        created_at=now,
    )

    # Test json dump
    json_str = context.to_json()

    # Verify basic fields
    assert str(session_id) in json_str
    assert "user-123" in json_str
    assert "search:read" in json_str
    assert "fr-FR" in json_str

    # Verify UUID serialization
    assert str(trace_id) in json_str
