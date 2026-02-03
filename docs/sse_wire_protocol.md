# SSE Wire Protocol Specification

This document defines the **Strict Wire Format** for streaming data from the Coreason Engine to clients via Server-Sent Events (SSE). It supersedes previous ad-hoc streaming formats.

## Overview

The Coreason SSE Wire Protocol ensures deterministic parsing of streaming data by wrapping every chunk of data in a standardized `StreamPacket`. This allows a single stream to multiplex raw text deltas (for LLM generation) and complex UI events (like citations or tool calls).

## The Packet Structure

The core unit of transmission is the `StreamPacket`.

### Schema

```python
class StreamPacket(CoReasonBaseModel):
    stream_id: UUID
    seq: int
    op: StreamOpCode
    t: datetime
    p: Union[str, PresentationEvent, Dict[str, Any]]
```

### Fields

*   **`stream_id`** (UUID): The unique identifier of the logical stream this packet belongs to.
*   **`seq`** (int): A strictly increasing sequence number per stream. Used to detect dropped packets or handle out-of-order delivery.
*   **`op`** (`StreamOpCode`): The operation code indicating the type of payload.
*   **`t`** (datetime): The UTC timestamp of when the packet was emitted.
*   **`p`** (Union): The payload. The type of this field depends on the `op`.

### Operation Codes (`StreamOpCode`)

| OpCode | Payload Type | Description |
| :--- | :--- | :--- |
| `DELTA` | `str` | A raw text token. Used for streaming prose (e.g., from an LLM). |
| `EVENT` | `PresentationEvent` or `Dict` | A structured event for the UI (e.g., a Citation, Progress Update). |
| `ERROR` | `str` or `Dict` | A stream-level error. |
| `CLOSE` | `Any` (usually `str` reason) | Indicates the stream has finished. No further packets with this `stream_id` will be sent. |

## JSON Serialization Examples

### 1. Text Delta

Used for streaming the main response text.

```json
{
  "stream_id": "123e4567-e89b-12d3-a456-426614174000",
  "seq": 1,
  "op": "DELTA",
  "t": "2023-10-27T10:00:00.000000+00:00",
  "p": "Hello"
}
```

### 2. UI Event (Citation)

Used for inserting rich UI components into the stream.

```json
{
  "stream_id": "123e4567-e89b-12d3-a456-426614174000",
  "seq": 2,
  "op": "EVENT",
  "t": "2023-10-27T10:00:01.000000+00:00",
  "p": {
    "id": "987fcdeb-51a2-11e1-fad2-0242ac130003",
    "timestamp": "2023-10-27T10:00:01.000000+00:00",
    "type": "CITATION_BLOCK",
    "data": {
      "citations": [
        {
          "source_id": "src_1",
          "uri": "https://example.com",
          "title": "Example Source",
          "confidence": 0.99
        }
      ]
    }
  }
}
```

### 3. Stream Close

Indicates the end of the stream.

```json
{
  "stream_id": "123e4567-e89b-12d3-a456-426614174000",
  "seq": 3,
  "op": "CLOSE",
  "t": "2023-10-27T10:00:02.000000+00:00",
  "p": "Stream completed successfully"
}
```

## Protocol Flow

1.  **Connection:** The client initiates an HTTP GET request to the streaming endpoint (e.g., `/v1/assist` with `Accept: text/event-stream`).
2.  **Handshake:** The server responds with `Content-Type: text/event-stream`.
3.  **Transmission:** The server sends `StreamPacket` objects serialized as JSON, each within an SSE `data:` field.
    *   **Event Type:** The SSE `event` field is set to `stream.packet`.
    *   **ID:** The SSE `id` field is set to the `stream_id` to allow resumption.
    *   **Payload:**
        *   `event: stream.packet`
        *   `id: 123e4567-e89b-12d3-a456-426614174000`
        *   `data: {"stream_id": "...", "op": "DELTA", ...}`
4.  **Termination:** The server sends a packet with `op=CLOSE`. The client should then close the connection (or expect the server to close it).

## Frontend Integration

The frontend should implement a parser that:
1.  Listens for SSE events of type `stream.packet` (or generic `message` if using a raw reader).
2.  Parses the `data` string as JSON into a `StreamPacket` object.
3.  Checks the `op` code:
    *   If `DELTA`: Append `packet.p` to the current text buffer.
    *   If `EVENT`: Render the structured component (e.g., insert a citation chip).
    *   If `CLOSE`: Finalize the UI state.
