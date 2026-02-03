# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, List
from unittest.mock import MagicMock

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.interfaces import (
    AgentInterface,
    ResponseHandler,
    SessionHandle,
)
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import Interaction


class MockSession:
    """A valid implementation of SessionHandle."""

    @property
    def session_id(self) -> str:
        return "sess-123"

    @property
    def identity(self) -> Identity:
        return Identity.anonymous()

    async def history(self, limit: int = 10, offset: int = 0) -> List[Interaction]:
        return []

    async def recall(
        self, query: str, limit: int = 5, threshold: float = 0.7
    ) -> List[str]:
        return []

    async def store(self, key: str, value: Any) -> None:
        pass

    async def get(self, key: str, default: Any = None) -> Any:
        return default


class ValidAgent:
    @property
    def manifest(self) -> AgentDefinition:
        return MagicMock(spec=AgentDefinition)

    async def assist(
        self, request: AgentRequest, session: SessionHandle, response: ResponseHandler
    ) -> None:
        pass


class InvalidAgent:
    """Missing assist method."""

    @property
    def manifest(self) -> AgentDefinition:
        return MagicMock(spec=AgentDefinition)


def test_runtime_checks_valid_agent() -> None:
    """Test that a class implementing the protocol is recognized."""
    agent = ValidAgent()
    assert isinstance(agent, AgentInterface)


def test_runtime_checks_invalid_agent() -> None:
    """Test that a class missing methods is not recognized."""
    agent = InvalidAgent()
    assert not isinstance(agent, AgentInterface)


def test_type_hint_usage() -> None:
    """Test that the type hint can be used in function signatures."""

    def run_agent(agent: AgentInterface) -> None:
        assert isinstance(agent, AgentInterface)

    valid_agent = ValidAgent()
    run_agent(valid_agent)


def test_session_handle_runtime_check() -> None:
    """Test that a class implementing SessionHandle is recognized."""
    session = MockSession()
    assert isinstance(session, SessionHandle)
