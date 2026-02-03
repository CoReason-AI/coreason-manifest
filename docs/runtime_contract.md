# Coreason Runtime Contract

This document defines the strictly typed "Runtime Contract" that governs the interaction between a Coreason Agent and the Engine (or any compliant runtime).

It implements the **Inversion of Control** pattern: The Runtime calls the Agent, passing in a `ResponseHandler` that the Agent uses to communicate back.

## Core Protocols

These protocols are defined in `src/coreason_manifest/definitions/interfaces.py`.

### 1. IAgentRuntime

This is the entry point that every Agent must implement.

```python
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

        Args:
            session: The active memory interface (history, recall, store).
            request: The strictly typed input envelope (payload, headers).
            handler: The callback interface for emitting thoughts, data, and streams.
        """
        ...
```

### 2. IResponseHandler

This protocol defines *how* an agent communicates back to the user. It completely decouples the agent logic from the transport layer (HTTP, WebSocket, SSE).

```python
@runtime_checkable
class IResponseHandler(Protocol):
    """Protocol defining how an agent communicates back to the user."""

    @abstractmethod
    def emit_event(self, event: PresentationEvent) -> Awaitable[None]:
        """Low-level emission of a raw event wrapper."""
        ...

    @abstractmethod
    def emit_thought(self, content: str) -> Awaitable[None]:
        """Helper to emit a THOUGHT_TRACE event (inner monologue)."""
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

### 3. IStreamEmitter

This protocol abstracts the concept of a streaming response. A stream is a "first-class citizen" with a unique lifecycle.

```python
@runtime_checkable
class IStreamEmitter(Protocol):
    """Abstracts the concept of a streaming response."""

    @abstractmethod
    def emit_chunk(self, content: str) -> Awaitable[None]:
        """Emit a token/chunk."""
        ...

    @abstractmethod
    def close(self) -> Awaitable[None]:
        """Close the stream."""
        ...
```

### 4. ISession

This protocol defines the Active Memory Interface, allowing agents to access history and persist state.

```python
@runtime_checkable
class ISession(Protocol):
    """Protocol encapsulating the Active Memory Interface."""

    @property
    @abstractmethod
    def session_id(self) -> str: ...

    @property
    @abstractmethod
    def identity(self) -> Identity: ...

    @abstractmethod
    def history(self, limit: int = 10, offset: int = 0) -> Awaitable[List[Interaction]]: ...

    @abstractmethod
    def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> Awaitable[List[str]]: ...

    @abstractmethod
    def store(self, key: str, value: Any) -> Awaitable[None]: ...

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Awaitable[Any]: ...
```

## Example Implementation

```python
class MyAgent:
    def __init__(self, manifest: AgentDefinition):
        self._manifest = manifest

    @property
    def manifest(self) -> AgentDefinition:
        return self._manifest

    async def assist(self, session: ISession, request: AgentRequest, handler: IResponseHandler) -> None:
        # 1. Emit a thought
        await handler.emit_thought("Analyzing request...")

        # 2. Open a stream
        stream = await handler.create_text_stream("response")

        # 3. Stream content
        await stream.emit_chunk("Hello ")
        await stream.emit_chunk("World")

        # 4. Close stream
        await stream.close()

        # 5. Signal completion
        await handler.complete()
```
