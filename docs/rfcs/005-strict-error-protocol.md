# RFC 005: Strict Error Protocol for Streaming

**Status:** Accepted
**Created:** 2025-05-20
**Target:** Coreason Agent Protocol (CAP) v1.0

## Abstract

This RFC defines a strict type schema for error reporting in the Coreason SSE wire protocol. It deprecates unstructured string errors and generic dictionary errors in favor of a strictly typed `StreamError` model. This ensures that clients can deterministically decide whether to retry a stream or surface a specific UI error message.

## Motivation

Previously, errors during streaming were sent as either:
1.  Raw strings (e.g., `"Error: Rate limit exceeded"`)
2.  Ad-hoc dictionaries (e.g., `{"error": "timeout", "details": ...}`)

This forced client SDKs to rely on fragile string matching ("grep programming") to implement retry logic. For example, distinguishing between a transient `503 Service Unavailable` and a fatal `401 Unauthorized` required parsing arbitrary text.

By enforcing a strict schema, we enable:
1.  **Automatic Retries:** SDKs can check `severity == TRANSIENT` to retry automatically.
2.  **Type Safety:** The wire format is validated at the boundary.
3.  **Standardization:** All Coreason agents emit errors in the same shape.

## Specification

### 1. New Primitives

We introduce two new primitives in `src/coreason_manifest/definitions/presentation.py`:

#### `ErrorSeverity` (Enum)

| Value | Description | Client Action |
| :--- | :--- | :--- |
| `FATAL` | The stream is dead and cannot be recovered (e.g., Auth failed, Validation error). | Raise exception, do not retry. |
| `TRANSIENT` | The stream was interrupted by a temporary issue (e.g., Timeout, Rate Limit). | Retry immediately (with backoff). |
| `WARNING` | The stream continues, but a minor component failed. | Log warning, continue processing stream. |

#### `StreamError` (Model)

```python
class StreamError(CoReasonBaseModel):
    code: str               # Machine-readable, snake_case (e.g., "rate_limit_exceeded")
    message: str            # Human-readable description
    severity: ErrorSeverity # Severity classification
    details: Optional[Dict[str, Any]] = None # Extra context (e.g., {"retry_after": 60})
```

### 2. Wire Format Update

The `StreamPacket` definition is updated to include `StreamError` in its payload union:

```python
class StreamPacket(CoReasonBaseModel):
    # ...
    op: StreamOpCode
    p: Union[str, PresentationEvent, StreamError, Dict[str, Any]]
```

### 3. Strict Validation Rules

To enforce this protocol, the `StreamPacket` validator implements the following logic when `op == StreamOpCode.ERROR`:

1.  **Reject Strings:** Payloads of type `str` raise a `ValueError`.
2.  **Coerce Dictionaries:** Payloads of type `dict` are strictly validated against the `StreamError` schema and converted to `StreamError` objects.
3.  **Reject Invalid Objects:** Any other type raises a `ValueError`.

## Migration Guide

### For Agent Developers
Instead of sending error strings:
```python
# OLD (Forbidden)
await stream.write_error("Something went wrong")
```

Send structured errors:
```python
# NEW (Required)
from coreason_manifest.definitions.presentation import StreamError, ErrorSeverity

error = StreamError(
    code="internal_error",
    message="Database connection failed",
    severity=ErrorSeverity.TRANSIENT
)
await stream.write_packet(op=StreamOpCode.ERROR, p=error)
```

### For Client SDKs
Clients parsing the stream should switch on `op`:
```python
if packet.op == StreamOpCode.ERROR:
    error: StreamError = packet.p
    if error.severity == ErrorSeverity.TRANSIENT:
        retry_stream()
    else:
        raise FatalError(error.message)
```
