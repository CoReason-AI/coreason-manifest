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
from pydantic import ValidationError

from coreason_manifest import (
    ArtifactEvent,
    ChatMessage,
    CitationEvent,
    PresentationEventType,
    Role,
)


def test_chat_message_serialization():
    """Test ChatMessage serialization with standard ISO timestamp."""
    msg = ChatMessage(role=Role.USER, content="Hello")
    dumped = msg.dump()

    assert dumped["role"] == "user"
    assert dumped["content"] == "Hello"
    assert "name" not in dumped
    assert "timestamp" in dumped
    # CoReasonBaseModel serializes datetime with Z suffix
    assert dumped["timestamp"].endswith("Z")


def test_role_validation():
    """Test Role validation rejects invalid roles."""
    with pytest.raises(ValidationError):
        ChatMessage(role="moderator", content="Hello")  # type: ignore


def test_presentation_polymorphism():
    """Test polymorphism for presentation events."""
    events = [
        CitationEvent(uri="https://example.com", text="Example"),
        ArtifactEvent(artifact_id="123", mime_type="text/csv"),
    ]

    assert events[0].type == PresentationEventType.CITATION
    assert events[1].type == PresentationEventType.ARTIFACT

    dumped_citation = events[0].dump()
    dumped_artifact = events[1].dump()

    assert dumped_citation["type"] == "citation"
    assert dumped_artifact["type"] == "artifact"


def test_immutability():
    """Test that models are immutable."""
    msg = ChatMessage(role=Role.USER, content="Hello")
    with pytest.raises(ValidationError):
        setattr(msg, "content", "New")  # noqa: B010

    citation = CitationEvent(uri="http://a", text="b")
    with pytest.raises(ValidationError):
        setattr(citation, "text", "c")  # noqa: B010
