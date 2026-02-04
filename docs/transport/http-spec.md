# Transport-Layer Specification (CAP Binding)

This document formalizes the **Coreason Agent Protocol (CAP)** that any Coreason-compatible engine must expose. It moves the `coreason-manifest` from strictly defining internal data structures to also defining *how* the outside world talks to an agent.

## Goal

To ensure that any engine (Python, Go, Node.js) implementing this manifest is guaranteed to work with standard Coreason frontends by adhering to a strict "Wire Format".

## Protocols

The Coreason Manifest supports two distinct delivery modes, defined by the `AgentCapability.delivery_mode` field:
1.  **Request-Response:** Standard HTTP JSON response.
2.  **Server-Sent Events (SSE):** Streaming response.

### Endpoint

The default endpoint path is:

`POST /v1/assist`

### Request Format

The request body **MUST** be a JSON object adhering to the `ServiceRequest` schema (the "Envelope").

*   **Schema:** `src/coreason_manifest/definitions/service.py`
*   **Content-Type:** `application/json`

Example:
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "context": {
    "session_id": "123e4567-e89b-12d3-a456-426614174001",
    "agent_id": "...",
    "user": { ... },
    "trace": { ... },
    "permissions": ["..."],
    "created_at": "..."
  },
  "payload": {
    "session_id": "123e4567-e89b-12d3-a456-426614174001",
    "payload": {
      "query": "Hello world"
    }
  }
}
```

### Response Format

The response format depends on the `delivery_mode`.

#### Mode 1: Request-Response (`REQUEST_RESPONSE`)

*   **Content-Type:** `application/json`
*   **Body:** A JSON object matching the `ServiceResponse` schema.

```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "...",
  "output": {
    "summary": "The weather is sunny."
  },
  "metrics": { ... }
}
```

#### Mode 2: Server-Sent Events (`SERVER_SENT_EVENTS`)

*   **Content-Type:** `text/event-stream`
*   **Body:** A stream of `StreamPacket` objects (wrapped in `ServerSentEvent` for wire transmission).

Each event in the stream corresponds to a `StreamPacket` object. The payload of these events follows the **Strict Wire Format** defined in `src/coreason_manifest/definitions/presentation.py`.

*   **Schema:** `src/coreason_manifest/definitions/presentation.py` (`StreamPacket`)
*   **Protocol Spec:** [SSE Wire Protocol Specification](sse-spec.md)

##### The `StreamPacket` Model

The `StreamPacket` wraps every chunk of data, ensuring deterministic parsing for both text deltas and UI events.

```python
class StreamPacket(CoReasonBaseModel):
    stream_id: UUID
    seq: int
    op: StreamOpCode
    t: datetime
    p: Union[str, PresentationEvent, StreamError, Dict[str, Any]]
```

##### Example Stream

```
data: {"stream_id": "...", "seq": 1, "op": "DELTA", "t": "...", "p": "Hello"}

data: {"stream_id": "...", "seq": 2, "op": "EVENT", "t": "...", "p": {"type": "CITATION_BLOCK", ...}}

data: {"stream_id": "...", "seq": 3, "op": "CLOSE", "t": "...", "p": "Done"}
```

## Service Contract & OpenAPI

The `coreason-manifest` includes utility classes to generate the OpenAPI specification for this contract.

### `ServiceContract`

The `ServiceContract` class in `src/coreason_manifest/definitions/service.py` provides a `generate_openapi_path()` method. This method returns the standard OpenAPI definition for the `/assist` endpoint, ensuring that documentation and client generators are always in sync with the manifest.

```python
from coreason_manifest.definitions.service import ServiceContract

contract = ServiceContract()
openapi_path = contract.generate_openapi_path()
```
