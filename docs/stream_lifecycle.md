# Stream Identity and Lifecycle

This document formalizes the concept of **Stream Identity** and the **Stream Lifecycle** within the Coreason Agent Framework.

## The Problem: Implicit Streams

Historically, "streaming" in many agent frameworks (including earlier versions of Coreason) was implicit. An agent would simply `yield` a series of tokens or events.

This led to several issues:
1.  **Ambiguity:** If an agent yields a token, which logical "message bubble" does it belong to?
2.  **Zombie Streams:** If an agent crashes or the client disconnects, there was no explicit "Close" signal for a specific stream, leading to hanging resources.
3.  **Multiplexing:** It was difficult to interleave multiple streams (e.g., generating code in one block and explaining it in another) simultaneously.

## The Solution: Streams as First-Class Citizens

We now treat a "Stream" as an explicit object with a unique identity and a strict lifecycle.

### The `IStreamEmitter` Protocol

The `IStreamEmitter` is an object returned by the `IResponseHandler`. It encapsulates the state of a single stream.

```python
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

## Lifecycle States

A stream transitions through a strict state machine:

1.  **OPEN**: Created via `response.create_text_stream()`.
2.  **ACTIVE**: The agent calls `stream.emit_chunk()`. Data flows to the client.
3.  **CLOSED**: The agent calls `stream.close()`. The stream is sealed. No further writes are allowed.

## Usage Pattern

This pattern allows the agent to pass the `IStreamEmitter` to helper functions, decoupling the "streaming logic" from the main "response logic".

```python
async def generate_poem(stream: IStreamEmitter, topic: str):
    """Helper function that just knows how to write to a stream."""
    # ... expensive LLM generation ...
    for token in llm.generate(topic):
        await stream.emit_chunk(token)
    await stream.close()

async def assist(session, request, handler):
    # Main logic decides TO stream
    stream = await handler.create_text_stream("Poem")

    # And delegates the writing
    await generate_poem(stream, "Nature")
```

## UI Routing

On the frontend, the `stream_id` (managed by the Runtime) allows the UI to route tokens to the correct component.

*   **Event:** `ai.coreason.stream.start` -> **UI:** Create new message bubble.
*   **Event:** `ai.coreason.stream.chunk` -> **UI:** Append text to bubble.
*   **Event:** `ai.coreason.stream.end` -> **UI:** Mark bubble as complete (stop loading spinner).
