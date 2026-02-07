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
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.request import AgentRequest
from coreason_manifest.spec.common.session import SessionState
from coreason_manifest.spec.interfaces.behavior import (
    IAgentRuntime,
    IResponseHandler,
    IStreamEmitter,
)

# --- Mock Implementations for Testing ---


class MockStreamEmitter:
    def __init__(self, name: str):
        self.name = name
        self.content: list[str] = []
        self.closed = False

    async def emit_chunk(self, content: str) -> None:
        self.content.append(content)

    async def close(self) -> None:
        self.closed = True


class MockResponseHandler:
    def __init__(self) -> None:
        self.thoughts: list[str] = []
        self.logs: list[tuple[str, str, dict[str, Any] | None]] = []
        self.streams: dict[str, MockStreamEmitter] = {}
        self.completed_output: dict[str, Any] | None = None

    async def emit_thought(self, content: str, source: str = "agent") -> None:
        self.thoughts.append(f"[{source}] {content}")

    async def create_text_stream(self, name: str) -> IStreamEmitter:
        emitter = MockStreamEmitter(name)
        self.streams[name] = emitter
        return emitter

    async def log(self, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
        self.logs.append((level, message, metadata))

    async def complete(self, outputs: dict[str, Any] | None = None) -> None:
        self.completed_output = outputs


class ComplexAgent(IAgentRuntime):
    async def assist(self, session: SessionState, request: AgentRequest, handler: IResponseHandler) -> None:
        _ = session  # Unused
        await handler.log("info", "Starting complex task", {"query": request.query})
        await handler.emit_thought("Thinking about the problem...")

        stream = await handler.create_text_stream("main")
        await stream.emit_chunk("Part 1")
        await stream.emit_chunk(" and Part 2")
        await stream.close()

        await handler.complete({"status": "done"})

    async def shutdown(self) -> None:
        pass


class PartialAgent:
    """Implements assist but missing shutdown."""

    async def assist(self, session: SessionState, request: AgentRequest, handler: IResponseHandler) -> None:
        pass


class InheritedAgent(ComplexAgent):
    """Inherits from a valid agent."""


# --- Tests ---


def test_edge_case_runtime_checkable_partial_implementation() -> None:
    """
    Edge Case: Verify runtime_checkable behavior on partial implementation.
    PartialAgent implements assist but misses shutdown, so it should FAIL isinstance check.
    """
    agent = PartialAgent()
    assert not isinstance(agent, IAgentRuntime)


def test_edge_case_inheritance() -> None:
    """
    Edge Case: Verify that a subclass of a compliant agent is also compliant.
    """
    agent = InheritedAgent()
    assert isinstance(agent, IAgentRuntime)


@pytest.mark.asyncio
async def test_complex_interaction_flow() -> None:
    """
    Complex Case: Simulate a full agent interaction and verify side effects on the handler.
    """
    # Setup Context
    handler = MockResponseHandler()
    agent = ComplexAgent()

    session = SessionState(
        agent_id="agent-123", user_id="user-456", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)
    )

    request = AgentRequest(query="Solve world hunger", session_id=session.id)

    # Execute
    await agent.assist(session, request, handler)

    # Verify Logs
    assert len(handler.logs) == 1
    assert handler.logs[0] == ("info", "Starting complex task", {"query": "Solve world hunger"})

    # Verify Thoughts
    assert len(handler.thoughts) == 1
    assert handler.thoughts[0] == "[agent] Thinking about the problem..."

    # Verify Streams
    assert "main" in handler.streams
    stream = handler.streams["main"]
    assert stream.content == ["Part 1", " and Part 2"]
    assert stream.closed is True

    # Verify Completion
    assert handler.completed_output == {"status": "done"}


def test_mixin_composition() -> None:
    """
    Edge Case: Verify that an agent composed of mixins can satisfy the protocol.
    """

    class AssistMixin:
        async def assist(self, session: SessionState, request: AgentRequest, handler: IResponseHandler) -> None:
            pass

    class ShutdownMixin:
        async def shutdown(self) -> None:
            pass

    class ComposedAgent(AssistMixin, ShutdownMixin):
        pass

    agent = ComposedAgent()
    assert isinstance(agent, IAgentRuntime)


def test_agent_request_broken_lineage_validation() -> None:
    """
    Edge Case: Verify AgentRequest validation for broken lineage.
    If parent_request_id is present, root_request_id MUST be present.
    """
    # This should fail because parent is set but root is None
    # Note: AgentRequest validator usually auto-roots if root is None, BUT
    # the logic says: if parent is not None and root is None -> raise ValueError
    # Before the auto-rooting logic which sets root = request_id.

    with pytest.raises(ValidationError) as excinfo:
        AgentRequest(
            query="test",
            parent_request_id=uuid4(),
            root_request_id=None,  # explicitly passing None, or omitting it if default is None
        )
    assert "Broken Lineage" in str(excinfo.value)
