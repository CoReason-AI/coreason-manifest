# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import AsyncIterator, Union
from unittest.mock import MagicMock

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.events import CloudEvent, GraphEvent
from coreason_manifest.definitions.interfaces import AgentInterface
from coreason_manifest.definitions.request import AgentRequest


class ValidAgent:
    @property
    def manifest(self) -> AgentDefinition:
        return MagicMock(spec=AgentDefinition)

    async def assist(
        self, request: AgentRequest
    ) -> AsyncIterator[Union[CloudEvent, GraphEvent]]:
        yield MagicMock(spec=GraphEvent)


class InvalidAgent:
    """Missing assist method."""
    @property
    def manifest(self) -> AgentDefinition:
        return MagicMock(spec=AgentDefinition)


def test_runtime_checks_valid_agent():
    """Test that a class implementing the protocol is recognized."""
    agent = ValidAgent()
    assert isinstance(agent, AgentInterface)


def test_runtime_checks_invalid_agent():
    """Test that a class missing methods is not recognized."""
    agent = InvalidAgent()
    assert not isinstance(agent, AgentInterface)


def test_type_hint_usage():
    """Test that the type hint can be used in function signatures."""
    def run_agent(agent: AgentInterface) -> None:
        assert isinstance(agent, AgentInterface)

    valid_agent = ValidAgent()
    run_agent(valid_agent)
