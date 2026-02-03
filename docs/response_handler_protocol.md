# Response Handler Protocol

The `IResponseHandler` is the core mechanism for an agent to communicate back to the user or the system. It implements the **Inversion of Control** pattern, where the runtime provides a handler to the agent, and the agent calls methods on it.

## The Problem: Coupling

In traditional frameworks, agents often `return` a specific object (like a Flask Response) or `yield` tokens directly. This couples the agent logic to the transport layer (HTTP, WebSocket, CLI).

## The Solution: The `IResponseHandler` Protocol

The `IResponseHandler` is an abstract interface (Python Protocol) that defines *semantic* actions an agent can take, regardless of how they are delivered.

### Interface Definition

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

## Transport Independence

Because `IResponseHandler` is just an interface, the runtime can implement it differently depending on the context:

1.  **HTTP/SSE Server:** The implementation writes JSON chunks to the open HTTP connection.
2.  **WebSocket Server:** The implementation sends WebSocket frames.
3.  **CLI Tool:** The implementation prints formatted text to `stdout`.
4.  **Test Runner:** The implementation collects events into a list for assertion.

## Usage in an Agent

The agent (the "Assisted" component) receives the handler in its `assist` method.

```python
async def assist(self, session: ISession, request: AgentRequest, handler: IResponseHandler):
    # 1. Think
    await handler.emit_thought("I need to search for weather data.")

    # 2. Stream Response
    stream = await handler.create_text_stream("Weather Report")
    await stream.emit_chunk("The weather in ")
    await stream.emit_chunk("San Francisco is sunny.")
    await stream.close()
```
