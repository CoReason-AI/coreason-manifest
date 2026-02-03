# Stream Identity and Lifecycle

This document formalizes the concept of **Stream Identity** and the **Stream Lifecycle** within the Coreason framework. It addresses the limitations of implicit streaming (simple `yield`) and introduces a robust, handle-based approach for managing agent responses.

## The Problem: Implicit Streams

In early iterations, streaming was often implicit: an agent would simply `yield` a series of events. While simple, this approach had significant drawbacks:

1.  **Zombie Streams:** There was no explicit "Close" signal. If a generator crashed or hung, the stream remained open indefinitely.
2.  **Routing Ambiguity:** In complex multi-turn or multi-agent scenarios, the UI often struggled to route a specific token to the correct message bubble.
3.  **State Management:** There was no standard way to pause, resume, or abort a specific stream of thought.

## The Solution: Explicit Stream Handles

We treat a "Stream" as a first-class citizen with a unique ID and a distinct lifecycle. This is encapsulated in the `StreamHandle` protocol.

### The Lifecycle

A stream transitions through a strict state machine:

1.  **OPEN:** The stream is created via `ResponseHandler.create_stream()`. It is assigned a unique `stream_id`.
2.  **EMIT:** Content (tokens, chunks) is written to the stream via `write()`.
3.  **CLOSE:** The stream is explicitly sealed via `close()`. No further writes are allowed.
4.  **ABORT:** (Optional) The stream is killed via `abort()` due to an error.

### The `StreamHandle` Protocol

The `StreamHandle` provides a safe, strictly typed interface for interacting with an active stream.

```python
class StreamHandle(Protocol):
    @property
    def stream_id(self) -> str:
        """Unique UUID for this stream."""
        ...

    @property
    def is_active(self) -> bool:
        """True if the stream is open and accepting data."""
        ...

    async def write(self, chunk: str) -> None:
        """Emit content. Raises RuntimeError if closed."""
        ...

    async def close(self) -> None:
        """Seal the stream normally."""
        ...

    async def abort(self, reason: str) -> None:
        """Terminate the stream with an error."""
        ...
```

## Usage Pattern

Agents do not instantiate streams directly. Instead, they request a stream from the `ResponseHandler`.

### 1. Request a Stream

```python
# Typically inside an agent's logic
stream = await response_handler.create_stream(
    title="Drafting Response",
    metadata={"msg_id": "123"}
)
```

### 2. Write Content

```python
await stream.write("Hello, ")
await stream.write("World!")
```

### 3. Close the Stream

**Crucial:** You *must* close the stream.

```python
await stream.close()
```

### Context Manager (Recommended)

Ideally, implementations should support or be wrapped in context managers to ensure closure:

```python
async with await response_handler.create_stream() as stream:
    await stream.write("Safe content")
# Automatically closed here
```

## Benefits

*   **UI Precision:** The frontend receives the `stream_id` in the first event. All subsequent chunks carry this ID, ensuring they end up in the exact right UI element, even if multiple streams are active (e.g., a "Thought" stream and a "Response" stream running in parallel).
*   **Resource Cleanup:** The explicit `close()` signal allows the transport layer (SSE, WebSockets) to flush buffers and release connections immediately.
*   **Error Propagation:** `abort()` allows the agent to signal that a specific stream failed without crashing the entire agent process.
