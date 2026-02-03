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
from typing import Any, Awaitable, Dict, List, Optional, Protocol, Union, runtime_checkable

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.events import CloudEvent, GraphEvent
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.presentation import (
    CitationBlock,
    PresentationEvent,
)
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import Interaction
from coreason_manifest.definitions.session import SessionState as Session


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


@runtime_checkable
class EventSink(Protocol):
    """Protocol for emitting internal system events (telemetry, audit, logs).

    This serves as the standard interface for emitting GraphEvents and CloudEvents
    that are not necessarily meant for the user, but for the system.
    """

    @abstractmethod
    def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> Awaitable[None]:
        """The core method to ingest any strictly typed event."""
        ...

    @abstractmethod
    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Awaitable[None]:
        """A helper to emit a standard log event (which the implementation wraps in a CloudEvent)."""
        ...

    @abstractmethod
    def audit(self, actor: str, action: str, resource: str, success: bool) -> Awaitable[None]:
        """A helper to emit an immutable Audit Log entry."""
        ...


@runtime_checkable
class ResponseHandler(EventSink, Protocol):
    """Protocol for handling agent responses, decoupling logic from event transport.

    This interface allows agents to emit events and presentation blocks without
    being tied to a specific transport mechanism (e.g., HTTP, WebSocket).
    """

    @abstractmethod
    def thought(self, content: str, status: str = "IN_PROGRESS") -> Awaitable[None]:
        """Emit a thinking block."""
        ...

    @abstractmethod
    def markdown(self, content: str) -> Awaitable[None]:
        """Emit a markdown block."""
        ...

    @abstractmethod
    def data(
        self,
        data: Dict[str, Any],
        title: Optional[str] = None,
        view_hint: str = "JSON",
    ) -> Awaitable[None]:
        """Emit a data block."""
        ...

    @abstractmethod
    def error(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ) -> Awaitable[None]:
        """Emit an error block."""
        ...

    @abstractmethod
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
class SessionHandle(Protocol):
    """Protocol encapsulating the Active Memory Interface.

    Allows agents to lazily pull history, recall information via semantic search,
    and persist state across sessions.
    """

    @property
    @abstractmethod
    def session_id(self) -> str:
        """The unique identifier for the conversation."""
        ...

    @property
    @abstractmethod
    def identity(self) -> Identity:
        """The identity of the user/actor this session belongs to."""
        ...

    @abstractmethod
    def history(self, limit: int = 10, offset: int = 0) -> Awaitable[List[Interaction]]:
        """Async method to fetch recent turns lazily."""
        ...

    @abstractmethod
    def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> Awaitable[List[str]]:
        """Interface for Semantic Search / Vector DB retrieval.

        This delegates to the Runtime's vector store (Engine), and the Agent does
        not need to know *which* vector DB is being used.
        """
        ...

    @abstractmethod
    def store(self, key: str, value: Any) -> Awaitable[None]:
        """Persist a variable across sessions."""
        ...

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Awaitable[Any]:
        """Retrieve a persisted variable."""
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
    async def assist(self, request: AgentRequest, session: SessionHandle, response: ResponseHandler) -> None:
        """Process a request and use the response handler to emit events.

        Args:
            request: The strictly typed input envelope.
            session: The active memory interface.
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


@runtime_checkable
class IStreamEmitter(Protocol):
    """Abstracts the concept of a streaming response (like Sentient's TextStream)."""

    @abstractmethod
    def emit_chunk(self, content: str) -> Awaitable[None]:
        """Emit a chunk of text."""
        ...

    @abstractmethod
    def close(self) -> Awaitable[None]:
        """Close the stream."""
        ...


@runtime_checkable
class IResponseHandler(Protocol):
    """Defines how an agent communicates back to the user.

    This interface allows agents to emit events and presentation blocks without
    being tied to a specific transport mechanism (e.g., HTTP, WebSocket).
    """

    @abstractmethod
    def emit_event(self, event: PresentationEvent) -> Awaitable[None]:
        """Low-level emission of a raw event wrapper."""
        ...

    @abstractmethod
    def emit_thought(self, content: str) -> Awaitable[None]:
        """Helper to emit a THOUGHT_TRACE event."""
        ...

    @abstractmethod
    def emit_citation(self, citation: CitationBlock) -> Awaitable[None]:
        """Helper to emit a CITATION_BLOCK event."""
        ...

    @abstractmethod
    def create_text_stream(self, name: str) -> Awaitable[IStreamEmitter]:
        """Opens a new stream for token-by-token generation."""
        ...

    @abstractmethod
    def complete(self) -> Awaitable[None]:
        """Signals the end of the generation turn."""
        ...


@runtime_checkable
class IAgentRuntime(Protocol):
    """Defines the strict signature an agent developer must implement."""

    @abstractmethod
    def assist(self, session: Session, request: AgentRequest, handler: IResponseHandler) -> Awaitable[None]:
        """Process a request and use the response handler to emit events.

        Args:
            session: The session context (state).
            request: The agent request envelope.
            handler: The response handler for output.
        """
        ...
