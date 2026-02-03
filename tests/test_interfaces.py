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
from typing import Any, List, cast
from coreason_manifest.definitions.interfaces import (
    IStreamEmitter,
    IResponseHandler,
    ISession,
    IAgentRuntime,
    AgentDefinition
)
from coreason_manifest.definitions.presentation import PresentationEvent, CitationBlock
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import Interaction
from coreason_manifest.definitions.identity import Identity

class MockStreamEmitter:
    """Mock implementation of IStreamEmitter."""
    async def emit_chunk(self, content: str) -> None:
        pass

    async def close(self) -> None:
        pass

class MockHandler:
    """Mock implementation of IResponseHandler."""
    async def emit_event(self, event: PresentationEvent) -> None:
        pass

    async def emit_thought(self, content: str) -> None:
        pass

    async def emit_citation(self, citation: CitationBlock) -> None:
        pass

    async def create_text_stream(self, name: str) -> IStreamEmitter:
        return MockStreamEmitter()

    async def complete(self) -> None:
        pass

class MockSession:
    """Mock implementation of ISession."""
    @property
    def session_id(self) -> str:
        return "test-session"

    @property
    def identity(self) -> Identity:
        return Identity(id="user-1", name="Test User")

    async def history(self, limit: int = 10, offset: int = 0) -> List[Interaction]:
        return []

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> List[str]:
        return []

    async def store(self, key: str, value: Any) -> None:
        pass

    async def get(self, key: str, default: Any = None) -> Any:
        return default

class MyAgent:
    """Mock implementation of IAgentRuntime."""
    @property
    def manifest(self) -> AgentDefinition:
        # Return casted None or mock to avoid heavy instantiation
        return cast(AgentDefinition, None)

    async def assist(self, session: ISession, request: AgentRequest, handler: IResponseHandler) -> None:
        pass

def test_protocols_runtime_check():
    """Verify that the classes satisfy the protocols at runtime."""
    assert isinstance(MockStreamEmitter(), IStreamEmitter)
    assert isinstance(MockHandler(), IResponseHandler)
    assert isinstance(MockSession(), ISession)
    assert isinstance(MyAgent(), IAgentRuntime)

def test_type_checking():
    """Verify type checking concepts (this is mostly for static analysis but runs to ensure no errors)."""
    handler: IResponseHandler = MockHandler()
    session: ISession = MockSession()
    agent: IAgentRuntime = MyAgent()

    assert handler is not None
    assert session is not None
    assert agent is not None
