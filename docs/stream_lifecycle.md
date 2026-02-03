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

### The `StreamHandle` Protocol

The `StreamHandle` is an object returned by the `ResponseHandler`. It encapsulates the state of a single stream.

```python
class StreamHandle(Protocol):
    @property
    def stream_id(self) -> str:
        """Unique UUID for this stream instance."""
        ...

    @property
    def is_active(self) -> bool:
        """True if the stream is open and accepting data."""
        ...

    async def write(self, chunk: str) -> None:
        """Emit a chunk of text."""
        ...

    async def close(self) -> None:
        """Seal the stream successfully."""
        ...

    async def abort(self, reason: str) -> None:
        """Kill the stream with an error."""
        ...
```

## Lifecycle States

A stream transitions through a strict state machine:

1.  **OPEN**: Created via `response.create_stream()`. A unique `stream_id` is assigned.
2.  **ACTIVE**: The agent calls `stream.write()`. Data flows to the client.
3.  **CLOSED**: The agent calls `stream.close()`. The stream is sealed. No further writes are allowed.
4.  **ABORTED**: The agent calls `stream.abort()`. The stream is terminated with an error.

**Rule:** Calling `write()` on a `CLOSED` or `ABORTED` stream MUST raise a `RuntimeError`.

## Usage Pattern

This pattern allows the agent to pass the `StreamHandle` to helper functions, decoupling the "streaming logic" from the main "response logic".

```python
async def generate_poem(stream: StreamHandle, topic: str):
    """Helper function that just knows how to write to a stream."""
    # ... expensive LLM generation ...
    for token in llm.generate(topic):
        await stream.write(token)
    await stream.close()

async def assist(request, response):
    # Main logic decides TO stream
    stream = await response.create_stream(title="Poem")

    # And delegates the writing
    await generate_poem(stream, "Nature")
```

## UI Routing

On the frontend, the `stream_id` allows the UI to route tokens to the correct component.

*   **Event:** `ai.coreason.stream.start` (contains `stream_id`, `title`) -> **UI:** Create new message bubble.
*   **Event:** `ai.coreason.stream.chunk` (contains `stream_id`, `chunk`) -> **UI:** Append text to bubble with matching ID.
*   **Event:** `ai.coreason.stream.end` (contains `stream_id`) -> **UI:** Mark bubble as complete (stop loading spinner).

## Error Handling

Separation of concerns is key:
*   **Stream Errors:** `stream.abort("LLM Timeout")` affects *only* that stream content (e.g., shows a red "Error" badge on that specific bubble).
*   **Agent Errors:** `response.error("Database Down")` affects the entire request.
