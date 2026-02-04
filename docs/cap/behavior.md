# Agent Behavior Protocols

The `coreason_manifest` package defines the standard behavioral contracts that all Coreason Agents must implement. These protocols ensure interoperability between Agents, the Engine, and external testing tools.

They are defined in `src/coreason_manifest/definitions/interfaces.py` and are based on Python's `typing.Protocol` for structural subtyping.

## IAgentRuntime

The `IAgentRuntime` protocol defines the core responsibility of an Agent: to accept a request and use a response handler to emit events.

### Definition

```python
@runtime_checkable
class IAgentRuntime(Protocol):
    """Defines the strict signature an agent developer must implement."""

    @abstractmethod
    def assist(
        self, session: Session, request: AgentRequest, handler: IResponseHandler
    ) -> Awaitable[None]:
        """Process a request and use the response handler to emit events.

        Args:
            session: The session context.
            request: The strictly typed input envelope.
            handler: The handler for emitting results.
        """
        ...
```

### Key Components

1.  **`assist`**: The primary entry point for execution.
    *   **Input**: Strictly typed `AgentRequest` envelope.
    *   **Session**: A `Session` (alias for `SessionState`) for [Active Memory](../active_memory_interface.md) access (history, RAG, persistence).
    *   **Output**: None (events are emitted via `handler`).
    *   **Inversion of Control**: Instead of yielding events, the agent calls methods on the provided `IResponseHandler`.

## EventSink

The `EventSink` Protocol defines the standard interface for emitting internal system events, such as telemetry, audit logs, and distributed traces. It serves as the base for `IResponseHandler`.

### Definition

```python
@runtime_checkable
class EventSink(Protocol):
    @abstractmethod
    def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> Awaitable[None]:
        """The core method to ingest any strictly typed event."""
        ...

    @abstractmethod
    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Awaitable[None]:
        """A helper to emit a standard log event."""
        ...

    @abstractmethod
    def audit(self, actor: str, action: str, resource: str, success: bool) -> Awaitable[None]:
        """A helper to emit an immutable Audit Log entry."""
        ...
```

## IResponseHandler

The `IResponseHandler` Protocol decouples the agent's logic from the event transport (e.g., HTTP, WebSocket, SSE). It inherits from `EventSink`, allowing agents to use the same object for both user-facing responses and system logging.

### Definition

```python
@runtime_checkable
class IResponseHandler(EventSink, Protocol):
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
```

## IStreamEmitter

The `IStreamEmitter` Protocol encapsulates the lifecycle of a stream (Open -> Emit -> Close). See [Stream Identity and Lifecycle](../stream_lifecycle.md) for details.

```python
@runtime_checkable
class IStreamEmitter(Protocol):
    @abstractmethod
    def emit_chunk(self, content: str) -> Awaitable[None]:
        """Emit a chunk of text."""
        ...

    @abstractmethod
    def close(self) -> Awaitable[None]:
        """Close the stream."""
        ...
```

## LifecycleInterface

The `LifecycleInterface` protocol defines optional setup and teardown methods for agents that manage resources (e.g., database connections, model loaders).

### Definition

```python
@runtime_checkable
class LifecycleInterface(Protocol):
    def startup(self) -> None:
        """Initialize resources before serving traffic."""
        ...

    def shutdown(self) -> None:
        """Cleanup resources."""
        ...
```

## Usage Example

```python
import asyncio
from typing import Any
from coreason_manifest.definitions.interfaces import IAgentRuntime, IResponseHandler, IStreamEmitter
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import SessionState as Session

class EchoAgent:
    """A simple agent that strictly implements IAgentRuntime."""

    async def assist(self, session: Session, request: AgentRequest, handler: IResponseHandler) -> None:
        # Emit a "thinking" event
        await handler.emit_thought("Processing request...")

        # Create a stream for the output
        stream: IStreamEmitter = await handler.create_text_stream(name="Echo Response")

        try:
            # Simulate streaming chunks
            words = str(request.payload.get("query", "")).split()
            for word in words:
                await stream.emit_chunk(word + " ")
                await asyncio.sleep(0.1)

            # Finalize the stream
            await stream.close()
            await handler.complete()

        except Exception as e:
            await handler.log("ERROR", f"Failed to stream response: {e}")
            # Note: IStreamEmitter doesn't expose abort directly, the handler manages errors via log/emit_event

# Runtime Check
agent = EchoAgent()
assert isinstance(agent, IAgentRuntime)  # True
```
