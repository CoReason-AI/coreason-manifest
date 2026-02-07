# Stream Identity & Lifecycle

This document defines the protocols and data structures for treating output streams as first-class citizens within the Coreason ecosystem. This capability, introduced in Work Package O, enables "Explicit, Multiplexed Stream Management," supporting advanced UI patterns like Generative UI and parallel multi-modal outputs.

## Overview

Traditionally, agents emit a single, implicit stream of tokens. The Stream Identity & Lifecycle specification upgrades this to allow multiple, named streams to be emitted concurrently. Each stream has a unique identity, a defined lifecycle (`START` -> `STREAM` -> `END`), and a specific content type.

### Key Concepts

1.  **Stream Identity**: A unique `stream_id` distinguishes one flow of content from another.
2.  **Lifecycle**: Explicit events signal the opening and closing of streams.
3.  **Multiplexing**: Multiple streams can be active simultaneously (e.g., a "thinking" stream and a "code" stream).
4.  **Backward Compatibility**: If no stream is specified, the system defaults to a stream ID of `"default"`.

## Data Models

### Stream Reference

A `StreamReference` defines the metadata for a stream.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `stream_id` | `str` | *Required* | Unique logical identifier for the stream. |
| `name` | `Optional[str]` | `None` | Human-readable label (e.g., "Reasoning", "Terminal"). |
| `content_type` | `str` | `"text/plain"` | MIME type of the content (e.g., `application/json`). |

### Stream State

The lifecycle state of a stream is tracked via the `StreamState` enum:

*   `OPEN`: The stream has started and is accepting chunks.
*   `CLOSED`: The stream has finished successfully.
*   `FAILED`: The stream terminated abruptly due to an error.

## Graph Events

The internal event graph has been updated to support these primitives.

### `STREAM_START` (`GraphEventStreamStart`)

Signals the creation of a new stream.

```json
{
  "event_type": "STREAM_START",
  "stream_id": "thought_process",
  "name": "Reasoning Trace",
  "content_type": "text/markdown",
  "run_id": "...",
  "trace_id": "...",
  "node_id": "..."
}
```

### `NODE_STREAM` (`GraphEventNodeStream`)

Carries a chunk of content for a specific stream.

```json
{
  "event_type": "NODE_STREAM",
  "stream_id": "thought_process",
  "chunk": "The user is asking for...",
  "run_id": "...",
  "trace_id": "...",
  "node_id": "..."
}
```
*Note: If `stream_id` is omitted in the JSON payload, it deserializes to `"default"`.*

### `STREAM_END` (`GraphEventStreamEnd`)

Signals the normal closure of a stream.

```json
{
  "event_type": "STREAM_END",
  "stream_id": "thought_process",
  "run_id": "...",
  "trace_id": "...",
  "node_id": "..."
}
```

## Runtime Interface (`IStreamEmitter`)

The `IStreamEmitter` protocol defines the contract for runtime components that generate streams. It is part of the **Behavioral Protocols** suite defined in `coreason_manifest.spec.interfaces.behavior`.

```python
from typing import Protocol, runtime_checkable
from abc import abstractmethod

@runtime_checkable
class IStreamEmitter(Protocol):
    """Represents an open channel for streaming token chunks back to the client."""

    @abstractmethod
    async def emit_chunk(self, content: str) -> None:
        """Send a text fragment."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Signal the stream is finished."""
        ...
```

## Usage Examples

### Multiplexing Scenario

An agent might generate a "Thinking" stream and a "Code" stream simultaneously.

**Sequence:**
1.  `STREAM_START(id="thinking", name="Thought", content_type="text/markdown")`
2.  `NODE_STREAM(id="thinking", chunk="I need to calculate...")`
3.  `STREAM_START(id="code", name="Python", content_type="text/x-python")`
4.  `NODE_STREAM(id="code", chunk="def calculate():...")`
5.  `NODE_STREAM(id="thinking", chunk="Now running the code...")`
6.  `STREAM_END(id="code")`
7.  `STREAM_END(id="thinking")`

### Backward Compatibility

Legacy agents emitting simple tokens produce events that look like this:

`NODE_STREAM(chunk="Hello")` -> deserializes to `stream_id="default"`.

This ensures that existing UIs and consumers that ignore `stream_id` continue to function by rendering the "default" stream.
