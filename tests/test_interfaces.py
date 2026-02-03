# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict, Optional, Union
from unittest.mock import MagicMock

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.events import CloudEvent, GraphEvent
from coreason_manifest.definitions.interfaces import AgentInterface, EventSink, ResponseHandler
from coreason_manifest.definitions.request import AgentRequest


class ValidAgent:
    @property
    def manifest(self) -> AgentDefinition:
        return MagicMock(spec=AgentDefinition)

    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        await response.emit_text_block("Hello")


class InvalidAgent:
    """Missing assist method."""

    @property
    def manifest(self) -> AgentDefinition:
        return MagicMock(spec=AgentDefinition)


class ValidResponseHandler:
    async def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> None:
        pass

    async def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        pass

    async def audit(self, actor: str, action: str, resource: str, success: bool) -> None:
        pass

    async def emit_text_block(self, text: str) -> None:
        pass


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


def test_runtime_checks_valid_response_handler() -> None:
    """Test that a class implementing ResponseHandler is recognized."""
    handler = ValidResponseHandler()
    assert isinstance(handler, ResponseHandler)
    assert isinstance(handler, EventSink)


def test_runtime_checks_missing_methods_in_handler() -> None:
    """Test that missing methods cause isinstance to fail."""

    class IncompleteHandler:
        async def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> None:
            pass

        # Missing other methods

    handler = IncompleteHandler()
    assert not isinstance(handler, ResponseHandler)
    assert not isinstance(handler, EventSink)  # Missing log/audit
