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
from typing import Any, Awaitable, List, Protocol, runtime_checkable

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.identity import Identity
from coreason_manifest.definitions.presentation import (
    CitationBlock,
    PresentationEvent,
)
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import Interaction


@runtime_checkable
class IStreamEmitter(Protocol):
    """Abstracts the concept of a streaming response (like Sentient's TextStream)."""

    @abstractmethod
    def emit_chunk(self, content: str) -> Awaitable[None]:
        """Emit a token/chunk."""
        ...

    @abstractmethod
    def close(self) -> Awaitable[None]:
        """Close the stream."""
        ...


@runtime_checkable
class IResponseHandler(Protocol):
    """Protocol defining how an agent communicates back to the user.

    This interface decouples the Agent from the specific Transport (HTTP/WebSocket/SSE).
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
class ISession(Protocol):
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
        """Interface for Semantic Search / Vector DB retrieval."""
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
class IAgentRuntime(Protocol):
    """Protocol defining the strict signature an agent developer must implement."""

    @property
    @abstractmethod
    def manifest(self) -> AgentDefinition:
        """Accessor for the static configuration/metadata of the agent."""
        ...

    @abstractmethod
    def assist(self, session: ISession, request: AgentRequest, handler: IResponseHandler) -> Awaitable[None]:
        """Process a request and use the response handler to emit events.

        This strictly matches the sentient signature but uses Coreason types.
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
