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

The `IStreamEmitter` is an object returned by the `IResponseHandler.create_text_stream()`. It encapsulates the lifecycle of a single output stream.

```python
class IStreamEmitter(Protocol):
    async def emit_chunk(self, content: str) -> None:
        """Emit a chunk of text."""
        ...

    async def close(self) -> None:
        """Close the stream."""
        ...
```

## Lifecycle States

A stream transitions through a strict state machine managed by the Runtime implementation:

1.  **OPEN**: Created via `handler.create_text_stream()`.
2.  **ACTIVE**: The agent calls `stream.emit_chunk()`. Data flows to the client.
3.  **CLOSED**: The agent calls `stream.close()`. The stream is sealed. No further writes are allowed.

**Note:** Unlike the older `StreamHandle`, `IStreamEmitter` simplifies the interface. Error handling (aborting) is typically managed by emitting error events via the `IResponseHandler` rather than manipulating the stream handle directly in this abstraction layer.

## Usage Pattern

This pattern allows the agent to pass the `IStreamEmitter` to helper functions, decoupling the "streaming logic" from the main "response logic".

```python
async def generate_poem(stream: IStreamEmitter, topic: str):
    """Helper function that just knows how to write to a stream."""
    # ... expensive LLM generation ...
    for token in llm.generate(topic):
        await stream.emit_chunk(token)
    await stream.close()

async def assist(session: Session, request: AgentRequest, handler: IResponseHandler) -> None:
    # Main logic decides TO stream
    stream = await handler.create_text_stream(name="Poem")

    try:
        # And delegates the writing
        await generate_poem(stream, "Nature")
    except Exception as e:
        # Handle errors at the handler level
        await handler.log("ERROR", str(e))
        await stream.close() # Ensure closure
    finally:
        await handler.complete()
```

## UI Routing

On the frontend, the stream allows the UI to route tokens to the correct component.

*   **Event:** `ai.coreason.stream.start` (contains `stream_id`, `name`) -> **UI:** Create new message bubble.
*   **Event:** `ai.coreason.stream.chunk` (contains `stream_id`, `chunk`) -> **UI:** Append text to bubble with matching ID.
*   **Event:** `ai.coreason.stream.end` (contains `stream_id`) -> **UI:** Mark bubble as complete (stop loading spinner).

## Error Handling

Separation of concerns is key:
*   **Stream Errors:** If a stream fails midway, closing it and logging an error allows the client to gracefully handle the partial content.
*   **Agent Errors:** `handler.emit_event(ErrorEvent(...))` affects the entire interaction state.
