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
class StreamHandle(Protocol):
    """Protocol encapsulating the lifecycle of a stream.

    A stream is a first-class citizen with a unique ID, distinct lifecycle,
    and strict state management.
    """

    @property
    @abstractmethod
    def stream_id(self) -> str:
        """The unique identifier for this specific stream instance (UUID)."""
        ...

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Strictly typed boolean indicating if the stream allows new data."""
        ...

    @abstractmethod
    def write(self, chunk: str) -> Awaitable[None]:
        """Async method to emit a token/chunk.

        Raises:
            RuntimeError: If the stream is closed.
        """
        ...

    @abstractmethod
    def close(self) -> Awaitable[None]:
        """Async method to finalize the stream (seal it)."""
        ...

    @abstractmethod
    def abort(self, reason: str) -> Awaitable[None]:
        """Async method to kill the stream with an error."""
        ...


class ResponseHandler(Protocol):
    """Protocol for handling agent responses, decoupling logic from event transport.

    This interface allows agents to emit events and presentation blocks without
    being tied to a specific transport mechanism (e.g., HTTP, WebSocket).
    """

    def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> Awaitable[None]:
        """Emit a raw CloudEvent or GraphEvent."""
        ...

    def thought(self, content: str, status: str = "IN_PROGRESS") -> Awaitable[None]:
        """Emit a thinking block."""
        ...

    def markdown(self, content: str) -> Awaitable[None]:
        """Emit a markdown block."""
        ...

    def data(
        self,
        data: Dict[str, Any],
        title: Optional[str] = None,
        view_hint: str = "JSON",
    ) -> Awaitable[None]:
        """Emit a data block."""
        ...

    def error(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ) -> Awaitable[None]:
        """Emit an error block."""
        ...

    def create_stream(
        self, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Awaitable[StreamHandle]:
        """Create a new stream and return its handle.

        Args:
            title: Optional title for the stream.
            metadata: Optional metadata for the stream.

        Returns:
            A StreamHandle instance to write content to.
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
    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        """Process a request and use the response handler to emit events.

        Args:
            request: The strictly typed input envelope.
            response: The handler for emitting results.
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
