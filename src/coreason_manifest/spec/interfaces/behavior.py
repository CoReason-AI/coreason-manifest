# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from abc import abstractmethod
from typing import Any, Dict, Optional, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from coreason_manifest.spec.common.request import AgentRequest
    from coreason_manifest.spec.common.session import SessionState


@runtime_checkable
class IStreamEmitter(Protocol):
    """Represents a single open channel for streaming tokens (e.g., to a UI)."""

    @abstractmethod
    async def emit_chunk(self, content: str) -> None:
        """Send a partial string."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Signal that this specific stream is finished."""
        ...


@runtime_checkable
class IResponseHandler(Protocol):
    """The 'Callback Object' passed to the agent. This is the Agent's only way to affect the world."""

    @abstractmethod
    async def emit_thought(self, content: str, source: str = "agent") -> None:
        """Publish internal reasoning (Chain-of-Thought)."""
        ...

    @abstractmethod
    async def create_text_stream(self, name: str) -> IStreamEmitter:
        """Request a new output stream. Returns the emitter."""
        ...

    @abstractmethod
    async def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Structured logging."""
        ...

    @abstractmethod
    async def complete(self, outputs: Optional[Dict[str, Any]] = None) -> None:
        """Signal execution success and provide final structured data."""
        ...


@runtime_checkable
class IAgentRuntime(Protocol):
    """The contract the User's Agent Class must fulfill."""

    @abstractmethod
    async def assist(self, session: "SessionState", request: "AgentRequest", handler: IResponseHandler) -> None:
        """The main entry point."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup hook (optional, generally empty in abstract)."""
        ...
