# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import TYPE_CHECKING, Any, Awaitable, Dict, Optional, Protocol, runtime_checkable
from abc import abstractmethod

if TYPE_CHECKING:
    from coreason_manifest.spec.common.request import AgentRequest
    from coreason_manifest.spec.common.session import SessionState


@runtime_checkable
class IStreamEmitter(Protocol):
    """Represents an open channel for streaming token chunks back to the client."""

    @abstractmethod
    async def emit_chunk(self, content: str) -> None:
        """Send a text fragment."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Signal the stream is finished."""
        ...


@runtime_checkable
class IResponseHandler(Protocol):
    """The 'Callback Object' passed to the agent. The agent uses this to talk to the outside world."""

    @abstractmethod
    async def emit_thought(self, content: str, source: str = "agent") -> None:
        """Send a 'thinking' update (internal monologue)."""
        ...

    @abstractmethod
    async def create_text_stream(self, name: str) -> IStreamEmitter:
        """Request a new stream channel. Returns the emitter."""
        ...

    @abstractmethod
    async def log(self, level: str, message: str, metadata: Optional[Dict] = None) -> None:
        """Structured logging."""
        ...

    @abstractmethod
    async def complete(self, outputs: Optional[Dict[str, Any]] = None) -> None:
        """Finalize the execution, optionally passing final structured output."""
        ...


@runtime_checkable
class IAgentRuntime(Protocol):
    """The contract the Agent class itself must fulfill."""

    @abstractmethod
    async def assist(self, session: "SessionState", request: "AgentRequest", handler: IResponseHandler) -> None:
        """The main entry point."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup hook."""
        ...
