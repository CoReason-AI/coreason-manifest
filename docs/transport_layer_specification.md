# Transport-Layer Specification

This document formalizes the **Public API Contract** that any Coreason-compatible engine must expose. It moves the `coreason-manifest` from strictly defining internal data structures to also defining *how* the outside world talks to an agent.

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

The request body **MUST** be a JSON object adhering to the `AgentRequest` schema.

*   **Schema:** `src/coreason_manifest/definitions/request.py`
*   **Content-Type:** `application/json`

Example:
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "123e4567-e89b-12d3-a456-426614174001",
  "payload": {
    "query": "Hello world"
  }
}
```

### Response Format

The response format depends on the `delivery_mode`.

#### Mode 1: Request-Response (`REQUEST_RESPONSE`)

*   **Content-Type:** `application/json`
*   **Body:** A JSON object matching the `outputs` schema defined in the Capability.

```json
{
  "summary": "The weather is sunny."
}
```

#### Mode 2: Server-Sent Events (`SERVER_SENT_EVENTS`)

*   **Content-Type:** `text/event-stream`
*   **Body:** A stream of `ServerSentEvent` objects.

Each event in the stream corresponds to a `ServerSentEvent` object, which wraps a standard `CloudEvent`.

*   **Schema:** `src/coreason_manifest/definitions/service.py`

##### The `ServerSentEvent` Model

The `ServerSentEvent` model defines the strict structure of each chunk in the stream.

**Content-Type Discriminators:** The payload within `data` (the CloudEvent) includes a `datacontenttype` field. Consumers should use this MIME type to determine how to parse or render the event (e.g., `application/vnd.coreason.stream+json` for token streams). See [Event Content-Type Discriminators](event_content_types.md) for details.

```python
class ServerSentEvent(CoReasonBaseModel):
    event: str          # The event type (e.g., 'ai.coreason.node.started')
    data: str           # The payload. MUST be a JSON string of the CloudEvent.
    id: Optional[str]   # The unique ID of the event.
```

**Critical Requirement:** The `data` field MUST be a JSON **string**. This is an SSE protocol requirement. The content of this string is the serialized `CloudEvent`.

##### Example Stream

```
event: ai.coreason.node.started
id: evt-001
data: {"specversion": "1.0", "type": "ai.coreason.node.started", "source": "urn:node:1", "datacontenttype": "application/json", "data": {"node_id": "1", "status": "RUNNING"}}

event: ai.coreason.node.stream
id: evt-002
data: {"specversion": "1.0", "type": "ai.coreason.node.stream", "source": "urn:node:1", "datacontenttype": "application/vnd.coreason.stream+json", "data": {"chunk": "Hello"}}

event: ai.coreason.node.completed
id: evt-003
data: {"specversion": "1.0", "type": "ai.coreason.node.completed", "source": "urn:node:1", "datacontenttype": "application/json", "data": {"output_summary": "Hello"}}
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
