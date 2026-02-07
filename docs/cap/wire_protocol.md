# Coreason Agent Protocol (CAP) - Wire Format

This document defines the **Wire Format** for the Coreason Agent Protocol (CAP). These data contracts ensure consistent communication between components (Lambda, K8s, CLI, Engines) regardless of the underlying transport (HTTP, WebSocket, Queue).

## Request/Response Envelopes

All runtime messages strictly adhere to the following Pydantic models. These models are defined in `coreason_manifest.spec.cap`.

### ServiceRequest

The standard envelope for sending instructions to an Agent.

| Field | Type | Description |
| :--- | :--- | :--- |
| `request_id` | `UUID` | Unique identifier for the request trace. |
| `context` | `SessionContext` | Metadata about the request (User Identity, Auth, Session). Separated from logic to enable consistent security policies. |
| `payload` | `AgentRequest` | The actual arguments for the Agent's business logic. |

**Example JSON:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "session_id": "sess_abc",
    "user": {
      "id": "user_123",
      "name": "Alice",
      "role": "user"
    }
  },
  "payload": {
    "query": "What is the status of the project?",
    "files": [],
    "conversation_id": "conv_123"
  }
}
```

### SessionContext

Strict context containing authentication and session details.

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | `str` | Unique identifier for the session. |
| `user` | `Identity` | The authenticated user making the request. |
| `agent` | `Optional[Identity]` | The target agent (if applicable). |

### AgentRequest

The strict payload schema used within `ServiceRequest`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `query` | `str` | The user's primary input/instruction. |
| `files` | `List[str]` | List of file URIs or references (default: `[]`). |
| `conversation_id` | `Optional[str]` | ID for continuing a session (default: `None`). |
| `meta` | `Dict[str, Any]` | Extra context like timezone (default: `{}`). |

### ServiceResponse

The synchronous result returned by an Agent service.

| Field | Type | Description |
| :--- | :--- | :--- |
| `request_id` | `UUID` | Corresponds to the request ID. |
| `created_at` | `datetime` | UTC timestamp of completion (ISO 8601). |
| `output` | `Dict[str, Any]` | The result data. |
| `metrics` | `Optional[Dict]` | Execution metrics (latency, tokens used). |

**Example JSON:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-10-27T10:00:00Z",
  "output": {
    "text": "The project is on track."
  },
  "metrics": {
    "duration_ms": 450,
    "tokens": 120
  }
}
```

### StreamPacket

Used for streaming partial results or events during execution. The packet structure is strictly typed to support deterministic handling of data and errors.

| Field | Type | Description |
| :--- | :--- | :--- |
| `op` | `StreamOpCode` | Operation code: `delta`, `event`, `error`, `close`. |
| `p` | `Union` | The payload, strictly typed based on `op`. |

**Ops and Payloads:**

| Op (`op`) | Payload (`p`) Type | Description |
| :--- | :--- | :--- |
| `delta` | `str` | A partial text chunk (token). |
| `event` | `Dict[str, Any]` | A structured event (e.g., tool usage, state change). Ideally adheres to [PresentationEvent schemas](../presentation_schemas.md). |
| `error` | `StreamError` | A strict error object. |
| `close` | `None` | Stream termination signal. |

**Example JSON (Delta):**
```json
{
  "op": "delta",
  "p": "The"
}
```

**Example JSON (Error):**
```json
{
  "op": "error",
  "p": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests",
    "severity": "transient",
    "details": {
      "retry_after": 60
    }
  }
}
```

### StreamError

Strict error model for stream exceptions.

| Field | Type | Description |
| :--- | :--- | :--- |
| `code` | `str` | Machine-readable error code. |
| `message` | `str` | Human-readable description. |
| `severity` | `ErrorSeverity` | `transient` (retryable) or `fatal`. |
| `details` | `Optional[Dict]` | Arbitrary context. |

### HealthCheckResponse

Standard response for system health probes.

| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | `HealthCheckStatus` | `ok`, `degraded`, or `maintenance`. |
| `agent_id` | `UUID` | Unique ID of the serving agent instance. |
| `version` | `str` | Semantic version of the service. |
| `uptime_seconds` | `float` | Seconds since startup. |

**Example JSON:**
```json
{
  "status": "ok",
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "version": "1.0.0",
  "uptime_seconds": 3600.5
}
```

## Standard Data Models

The following "Atomic" models are defined to ensure consistency across the ecosystem, particularly for Chat and UI interactions. They are available in `coreason_manifest`.

### ChatMessage

Represents a single message in a conversation history.

| Field | Type | Description |
| :--- | :--- | :--- |
| `role` | `Role` | `system`, `user`, `assistant`, or `tool`. |
| `content` | `str` | The text content. |
| `name` | `Optional[str]` | Author name (for multi-agent scenarios). |
| `tool_call_id` | `Optional[str]` | ID if responding to a tool call. |
| `timestamp` | `datetime` | UTC timestamp (ISO 8601). |

### PresentationEvent

Polymorphic events for UI rendering (referenced in `StreamPacket` `op=event`). This is a single container with a `type` discriminator and polymorphic `data` payload. See [Standardized Presentation Schemas](../presentation_schemas.md) for full details.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique ID for the event. |
| `timestamp` | `datetime` | UTC timestamp (ISO 8601). |
| `type` | `PresentationEventType` | `citation_block`, `progress_indicator`, `media_carousel`, `markdown_block`, `user_error`, `thought_trace`. |
| `data` | `Union` | The specific payload for the event type. |

#### CitationBlock (`type: citation_block`)

Payload is a `CitationBlock` object containing a list of `CitationItem`s.

| Field | Type | Description |
| :--- | :--- | :--- |
| `items` | `List[CitationItem]` | List of citations. |

**CitationItem:**
| Field | Type | Description |
| :--- | :--- | :--- |
| `source_id` | `str` | ID of the source. |
| `uri` | `AnyUrl` | Source URI. |
| `title` | `str` | Title of the source. |
| `snippet` | `Optional[str]` | Relevant text snippet. |

#### MediaCarousel (`type: media_carousel`)

Payload is a `MediaCarousel` object containing a list of `MediaItem`s.

| Field | Type | Description |
| :--- | :--- | :--- |
| `items` | `List[MediaItem]` | List of media items. |

**MediaItem:**
| Field | Type | Description |
| :--- | :--- | :--- |
| `url` | `AnyUrl` | Media URL. |
| `mime_type` | `str` | MIME type (e.g., `image/png`). |
| `alt_text` | `Optional[str]` | Alt text. |

#### ProgressUpdate (`type: progress_indicator`)

Payload is a `ProgressUpdate` object.

| Field | Type | Description |
| :--- | :--- | :--- |
| `label` | `str` | Progress label. |
| `status` | `Literal` | `running`, `complete`, `failed`. |
| `progress_percent` | `Optional[float]` | 0.0 to 1.0. |

#### MarkdownBlock (`type: markdown_block`)

Payload is a `MarkdownBlock` object.

| Field | Type | Description |
| :--- | :--- | :--- |
| `content` | `str` | Markdown text. |

#### User Error (`type: user_error`)

Payload is a dictionary (see Semantic Error Handling for standard fields).

#### Thought Trace (`type: thought_trace`)

Payload is a dictionary containing reasoning steps.

## OpenAPI Generation

The `coreason_manifest` package provides a utility to generate an OpenAPI 3.1 Path Item Object that strictly adheres to the Service Request/Response contracts defined above.

This is useful for exposing Agents as standard REST APIs.

### Usage

```python
import json
from coreason_manifest import ServiceContract

# Generate the OpenAPI Path Item
openapi_spec = ServiceContract.generate_openapi()

print(json.dumps(openapi_spec, indent=2))
```

This generates a definition for a `POST` operation that accepts a `ServiceRequest` and returns a `ServiceResponse`.
