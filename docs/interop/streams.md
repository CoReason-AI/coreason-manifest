# Interoperability: Real-Time Streams

Cognitive agents are inherently asynchronous. Users expect to see thoughts streaming token-by-token, not just a final spinner.

The `coreason-manifest` library defines a strict **Wire Protocol** for real-time communication, modeled as a **Discriminated Union of Envelopes** (`src/coreason_manifest/spec/interop/stream.py`).

---

## The `StreamPacket` Union

All data sent over the wire (WebSocket, SSE, or gRPC stream) must conform to the `StreamPacket` union. This allows clients to use a single switch-statement (or pattern match) to handle all event types.

```python
StreamPacket = Annotated[
    StreamDeltaEnvelope | StreamErrorEnvelope | StreamCloseEnvelope,
    Field(discriminator="op")
]
```

### 1. `StreamDeltaEnvelope` (`op: delta`)
Represents a partial update to a specific stream.
*   **`p` (payload)**: The string fragment (e.g., a token, a word, or a raw byte chunk).
*   **Use Case:** Streaming LLM generation or real-time tool logs.

### 2. `StreamErrorEnvelope` (`op: error`)
Propagates a localized failure asynchronously.
*   **`p` (payload)**: A `StreamError` object containing:
    *   `code`: Integer error code.
    *   `message`: Human-readable description.
    *   `severity`: `low`, `medium`, `high`, `critical`.

### 3. `StreamCloseEnvelope` (`op: close`)
The termination packet. It signals that a specific stream (or the entire connection) has finished.
*   **`p` (payload)**: Often contains the final `ExecutionSnapshot` reference or aggregated statistics (token usage, total duration).

---

## Protocol Design Principles

*   **Thin Envelopes:** The schema minimizes overhead (`op`, `p`) to reduce bandwidth for high-frequency token streams.
*   **Type Safety:** By using a Pydantic discriminated union, both the server (sender) and client (receiver) can validate every frame strictly. Malformed packets are rejected at the edge.
*   **Multiplexing:** While the envelope itself is simple, the transport layer can wrap these packets with `request_id` or `node_id` metadata to multiplex several parallel node streams over a single connection.
