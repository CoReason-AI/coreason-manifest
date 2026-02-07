# Behavioral Protocols (Work Package HH)

This document describes the **Behavioral Protocols** introduced to enable Inversion of Control (IoC) and Hexagonal Architecture within the Coreason ecosystem. By defining strict interfaces for runtime behavior, we decouple the Agent's business logic from the execution environment.

## Context

Traditionally, Agents were often tightly coupled to their runtime environment (e.g., direct stdout writes, specific logging libraries). This made it difficult to run the same Agent in different contexts (CLI, REST API, WebSocket Server, Test Runner) without code changes.

**Behavioral Protocols** solve this by defining strict contracts for how an Agent accepts work and communicates results.

## The Core Protocols

These protocols are defined in `src/coreason_manifest/spec/interfaces/behavior.py`.

### 1. `IAgentRuntime`

This is the primary contract that an Agent implementation must fulfill. It represents the "Agent" as a component that can be executed.

```python
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
```

*   **`assist`**: The core execution method. It receives the current state (`session`), the specific request (`request`), and a callback handler (`handler`) for output.
*   **`shutdown`**: A lifecycle hook for cleanup (closing DB connections, etc.).

### 2. `IResponseHandler`

This interface represents the "Output Port" in Hexagonal Architecture terms. The Agent uses this object to communicate with the outside world. It abstracts away whether the output is going to a console, a websocket, or a message queue.

```python
@runtime_checkable
class IResponseHandler(Protocol):
    """The 'Callback Object' passed to the agent."""

    @abstractmethod
    async def emit_thought(self, content: str, source: str = "agent") -> None:
        """Send a 'thinking' update (internal monologue)."""
        ...

    @abstractmethod
    async def create_text_stream(self, name: str) -> IStreamEmitter:
        """Request a new stream channel. Returns the emitter."""
        ...

    @abstractmethod
    async def log(self, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
        """Structured logging."""
        ...

    @abstractmethod
    async def complete(self, outputs: dict[str, Any] | None = None) -> None:
        """Finalize the execution, optionally passing final structured output."""
        ...
```

### 3. `IStreamEmitter`

This interface represents an individual output stream channel, typically created via `handler.create_text_stream()`.

```python
@runtime_checkable
class IStreamEmitter(Protocol):
    """Represents an open channel for streaming token chunks."""

    @abstractmethod
    async def emit_chunk(self, content: str) -> None:
        """Send a text fragment."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Signal the stream is finished."""
        ...
```

## Usage Pattern

The decoupling allows the same Agent logic to run in diverse environments:

1.  **CLI Runner**: Implements an `IResponseHandler` that prints to stdout/stderr.
2.  **Web Server**: Implements an `IResponseHandler` that pushes Server-Sent Events (SSE) or WebSocket messages.
3.  **Test Runner**: Implements a mock `IResponseHandler` that captures outputs for assertion.

The Agent code remains unchanged:

```python
class MyAgent(IAgentRuntime):
    async def assist(self, session, request, handler):
        await handler.log("info", "Starting task")

        stream = await handler.create_text_stream("reasoning")
        await stream.emit_chunk("Thinking about...")
        await stream.close()

        await handler.complete({"result": 42})

    async def shutdown(self):
        pass
```
