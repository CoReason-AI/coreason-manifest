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
from typing import Optional

from coreason_manifest.definitions.interfaces import (
    IAgentRuntime,
    IResponseHandler,
    IStreamEmitter,
)
from coreason_manifest.definitions.presentation import CitationBlock, PresentationEvent
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import SessionState as Session


class MockStreamEmitter:
    async def emit_chunk(self, content: str) -> None:
        pass

    async def close(self) -> None:
        pass


class MockResponseHandler:
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


class MockAgentRuntime:
    async def assist(
        self, session: Session, request: AgentRequest, handler: IResponseHandler
    ) -> None:
        pass


def test_stream_emitter_protocol() -> None:
    emitter = MockStreamEmitter()
    assert isinstance(emitter, IStreamEmitter)


def test_response_handler_protocol() -> None:
    handler = MockResponseHandler()
    assert isinstance(handler, IResponseHandler)


def test_agent_runtime_protocol() -> None:
    agent = MockAgentRuntime()
    assert isinstance(agent, IAgentRuntime)
