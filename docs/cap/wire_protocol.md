# Coreason Agent Protocol (CAP) - Wire Format

This document defines the **Wire Format** for the Coreason Agent Protocol (CAP). These data contracts ensure consistent communication between components (Lambda, K8s, CLI, Engines) regardless of the underlying transport (HTTP, WebSocket, Queue).

## Request/Response Envelopes

All runtime messages strictly adhere to the following Pydantic models. These models are defined in `coreason_manifest.spec.cap`.

### ServiceRequest

The standard envelope for sending instructions to an Agent.

| Field | Type | Description |
| :--- | :--- | :--- |
| `request_id` | `UUID` | Unique identifier for the request trace. |
| `context` | `Dict[str, Any]` | Runtime context (session ID, user ID, auth tokens). |
| `payload` | `Dict[str, Any]` | The actual arguments for the Agent or Tool. |

**Example JSON:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "user_id": "user_123",
    "session_id": "sess_abc"
  },
  "payload": {
    "query": "What is the status of the project?"
  }
}
```

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

Used for streaming partial results or events during execution.

| Field | Type | Description |
| :--- | :--- | :--- |
| `event` | `str` | Event type (e.g., `token`, `status`, `error`). |
| `data` | `Union[str, Dict]` | The payload of the event. |

**Example JSON:**
```json
{
  "event": "token",
  "data": "The"
}
```

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
