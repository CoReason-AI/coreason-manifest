# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Defines the behavioral contract (Protocol) for a Coreason Agent."""

from abc import abstractmethod
from typing import Any, Awaitable, Dict, Optional, Protocol, Union, runtime_checkable

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.events import CloudEvent, GraphEvent
from coreason_manifest.definitions.request import AgentRequest


@runtime_checkable
class EventSink(Protocol):
    """Protocol for emitting internal side-effects (telemetry, logs, audit)."""

    @abstractmethod
    def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> Awaitable[None]:
        """Ingest any strictly typed event."""
        ...

    @abstractmethod
    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Awaitable[None]:
        """Emit a standard log event (which the implementation wraps in a CloudEvent)."""
        ...

    @abstractmethod
    def audit(self, actor: str, action: str, resource: str, success: bool) -> Awaitable[None]:
        """Emit an immutable Audit Log entry."""
        ...


@runtime_checkable
class ResponseHandler(EventSink, Protocol):
    """Protocol for handling user-facing communication and system events.

    Inherits from EventSink to allow agents to emit system events (logs, audits)
    through the same interface used for user responses.
    """

    @abstractmethod
    def emit_text_block(self, text: str) -> Awaitable[None]:
        """Emit a text block to the user UI.

        This is distinct from `log` which emits to system logs (Datadog/Splunk).
        """
        ...


@runtime_checkable
class AgentInterface(Protocol):
    """Protocol defining the standard interface for a Coreason Agent."""

    @property
    @abstractmethod
    def manifest(self) -> AgentDefinition:
        """Accessor for the static configuration/metadata of the agent."""
        ...

    @abstractmethod
    def assist(self, request: AgentRequest, response: ResponseHandler) -> Awaitable[None]:
        """Process a request and use the response handler to emit events.

        Args:
            request: The strictly typed input envelope.
            response: The handler for emitting thoughts, data, artifacts, or final answers.

        Returns:
            None (awaited).
        """
        ...


@runtime_checkable
class LifecycleInterface(Protocol):
    """Protocol defining the lifecycle methods for a Coreason Agent."""

    def startup(self) -> None:
        """Initialize resources (DB connections, model loaders) before serving traffic."""
        ...

    def shutdown(self) -> None:
        """Cleanup resources."""
        ...
