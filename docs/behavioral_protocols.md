# Behavioral Protocols

This document defines the "Keystone" interfaces that strictly separate the **Agent Logic** (what the AI does) from the **Runtime Environment** (CLI, Web Server, Test Runner). By coding against these interfaces, developers build agents that can run anywhere.

These protocols establish a contract between the Agent and the Engine, enabling a "Write Once, Run Anywhere" architecture.

## Overview

The system defines three core Python `Protocols`:

1.  **`IStreamEmitter`**: Represents a single output channel (e.g., text stream).
2.  **`IResponseHandler`**: The callback object passed to the agent, providing methods to affect the world (logging, streaming, completing).
3.  **`IAgentRuntime`**: The contract that the User's Agent Class must fulfill to be executable by the engine.

All protocols are `async` and decorated with `@runtime_checkable` to allow `isinstance()` checks at runtime.

## Protocol Definitions

### IStreamEmitter

Represents a single open channel for streaming tokens (e.g., to a UI).

```python
from typing import Protocol, runtime_checkable
from abc import abstractmethod

@runtime_checkable
class IStreamEmitter(Protocol):
    @abstractmethod
    async def emit_chunk(self, content: str) -> None:
        """Send a partial string."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Signal that this specific stream is finished."""
        ...
```

### IResponseHandler

The "Callback Object" passed to the agent. This is the Agent's only way to affect the world. It abstracts away the details of the environment (CLI, REST API, WebSocket).

```python
from typing import Protocol, runtime_checkable, Any, Dict, Optional
from abc import abstractmethod
from coreason_manifest import IStreamEmitter

@runtime_checkable
class IResponseHandler(Protocol):
    @abstractmethod
    async def emit_thought(self, content: str, source: str = "agent") -> None:
        """Publish internal reasoning (Chain-of-Thought)."""
        ...

    @abstractmethod
    async def create_text_stream(self, name: str) -> IStreamEmitter:
        """Request a new output stream. Returns the emitter."""
        ...

    @abstractmethod
    async def log(self, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
        """Structured logging."""
        ...

    @abstractmethod
    async def complete(self, outputs: dict[str, Any] | None = None) -> None:
        """Signal execution success and provide final structured data."""
        ...
```

### IAgentRuntime

The contract the User's Agent Class must fulfill.

```python
from typing import Protocol, runtime_checkable, TYPE_CHECKING
from abc import abstractmethod
from coreason_manifest import IResponseHandler, SessionState, AgentRequest

@runtime_checkable
class IAgentRuntime(Protocol):
    @abstractmethod
    async def assist(self, session: SessionState, request: AgentRequest, handler: IResponseHandler) -> None:
        """The main entry point."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup hook (optional, generally empty in abstract)."""
        ...
```

## Example Implementation

### Implementing an Agent

```python
from coreason_manifest import IAgentRuntime, IResponseHandler, SessionState, AgentRequest

class MyAgent(IAgentRuntime):
    async def assist(self, session: SessionState, request: AgentRequest, handler: IResponseHandler) -> None:
        # Log entry
        await handler.log("info", "Starting processing", {"query": request.query})

        # Stream thought process
        await handler.emit_thought("Analyzing the user query...")

        # Create output stream
        stream = await handler.create_text_stream("main_output")
        await stream.emit_chunk("Hello, ")
        await stream.emit_chunk("World!")
        await stream.close()

        # Complete execution
        await handler.complete({"result": "success"})

    async def shutdown(self) -> None:
        print("Agent shutting down...")
```

### Implementing a Runtime (Handler)

```python
class CLIHandler(IResponseHandler):
    async def emit_thought(self, content: str, source: str = "agent") -> None:
        print(f"[{source.upper()}] {content}")

    async def create_text_stream(self, name: str) -> IStreamEmitter:
        return StdoutEmitter()

    async def log(self, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
        print(f"LOG [{level.upper()}]: {message} {metadata or ''}")

    async def complete(self, outputs: dict[str, Any] | None = None) -> None:
        print(f"DONE: {outputs}")

class StdoutEmitter(IStreamEmitter):
    async def emit_chunk(self, content: str) -> None:
        print(content, end="", flush=True)

    async def close(self) -> None:
        print() # Newline
```
