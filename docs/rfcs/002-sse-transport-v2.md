# RFC 002: Coreason SSE Wire Protocol

## 1. The Packet Structure

The core unit of transmission is the `StreamPacket`, which wraps every chunk of data sent over Server-Sent Events (SSE). This ensures deterministic parsing on the frontend.

### StreamPacket Fields

*   `stream_id` (UUID): The unique identifier of the stream this packet belongs to.
*   `seq` (int): Sequence number, strictly increasing per stream to handle out-of-order delivery or reconnection.
*   `op` (StreamOpCode): Operation code indicating the type of payload.
    *   `DELTA`: Raw text token (for streaming LLM output).
    *   `EVENT`: A structured `PresentationEvent` (for UI components).
    *   `ERROR`: Stream-level error.
    *   `CLOSE`: Graceful termination.
*   `t` (datetime): Timestamp of emission (UTC).
*   `p` (Union[str, PresentationEvent, Dict[str, Any]]): The Payload. Shortened to 'p' to save bandwidth.

## 2. JSON Serialization Examples

### DELTA Packet

```json
{
  "stream_id": "123e4567-e89b-12d3-a456-426614174000",
  "seq": 1,
  "op": "DELTA",
  "t": "2023-10-27T10:00:00+00:00",
  "p": "Hello"
}
```

### EVENT Packet (Citation)

```json
{
  "stream_id": "123e4567-e89b-12d3-a456-426614174000",
  "seq": 2,
  "op": "EVENT",
  "t": "2023-10-27T10:00:01+00:00",
  "p": {
    "id": "987fcdeb-51a2-11e1-fad2-0242ac130003",
    "timestamp": "2023-10-27T10:00:01+00:00",
    "type": "CITATION_BLOCK",
    "data": {
      "citations": [
        {
          "source_id": "src_1",
          "uri": "https://example.com",
          "title": "Example",
          "confidence": 0.99
        }
      ]
    }
  }
}
```

## 3. Protocol Flow

1.  **Connection:** The client initiates an HTTP GET request to the streaming endpoint.
2.  **Handshake:** The server establishes the SSE connection.
3.  **Transmission:** The server sends a series of `StreamPacket` objects serialized as JSON within SSE `data:` fields.
4.  **Termination:** The server sends a packet with `op=CLOSE` to indicate the end of the stream, then closes the connection.
