# Event Content-Type Discriminators

To enable robust and generic consumption of Coreason events, the platform utilizes strict **MIME-type discriminators**. This allows consumers (such as React frontends, Event Routers, or other services) to route and render events based on standard HTTP-like headers, without needing to parse the internal payload or inspect specific event types.

## EventContentType

The `EventContentType` enumeration defines the supported Vendor-Specific MIME types:

*   **JSON (`application/json`)**: The default content type for standard events (e.g., `NODE_STARTED`, `NODE_COMPLETED`).
*   **STREAM (`application/vnd.coreason.stream+json`)**: Specifically for streaming token generation (`NODE_STREAM`). Clients can route these directly to a "Stream Renderer" or text buffer.
*   **ERROR (`application/vnd.coreason.error+json`)**: For semantic error events (`ERROR`). Clients can trigger error boundaries or toaster notifications based on this type.
*   **ARTIFACT (`application/vnd.coreason.artifact+json`)**: For generated files or artifacts (`ARTIFACT_GENERATED`). Clients can trigger file download handlers or previewers.

## CloudEvent Integration

The Coreason Agent Manifest utilizes the standard [CloudEvents v1.0](https://cloudevents.io/) envelope. The `datacontenttype` field of the CloudEvent carries the discriminator.

### Schema

```python
class CloudEvent(CoReasonBaseModel, Generic[T]):
    # ...
    datacontenttype: Union[EventContentType, str] = Field(
        default=EventContentType.JSON,
        description="MIME content type of data"
    )
    # ...
```

## Usage in Streaming (SSE)

When using `SERVER_SENT_EVENTS` delivery mode, each event in the stream is a JSON-serialized CloudEvent. The consumer should inspect `datacontenttype` to determine how to handle the `data` payload.

### Example: Stream Event

```json
{
  "specversion": "1.0",
  "type": "ai.coreason.node.stream",
  "source": "urn:node:123",
  "datacontenttype": "application/vnd.coreason.stream+json",
  "data": {
    "chunk": "Hello "
  }
}
```

### Example: Error Event

```json
{
  "specversion": "1.0",
  "type": "ai.coreason.legacy.error",
  "source": "urn:node:123",
  "datacontenttype": "application/vnd.coreason.error+json",
  "data": {
    "error_message": "Rate limit exceeded",
    "code": 429,
    "domain": "LLM",
    "retryable": true
  }
}
```

## Migration

The `migrate_graph_event_to_cloud_event` utility function automatically maps legacy `GraphEvent` types to the appropriate `datacontenttype`:

*   `NODE_STREAM` -> `application/vnd.coreason.stream+json`
*   `ERROR` -> `application/vnd.coreason.error+json`
*   `ARTIFACT_GENERATED` -> `application/vnd.coreason.artifact+json`
*   All others -> `application/json`
