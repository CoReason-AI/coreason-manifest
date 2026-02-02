# Observability: CloudEvents & OpenTelemetry

`coreason_manifest` now uses the [CloudEvents v1.0](https://cloudevents.io/) standard for all event emission, enabling seamless integration with distributed tracing and observability tools like Datadog, Honeycomb, and OpenTelemetry Collectors.

## The CloudEvent Envelope

Every event emitted by the Coreason Engine is wrapped in a standard `CloudEvent` envelope.

### Schema

```json
{
  "specversion": "1.0",
  "type": "ai.coreason.node.started",
  "source": "urn:node:uuid-1234",
  "id": "event-uuid",
  "time": "2023-10-27T10:00:00Z",
  "datacontenttype": "application/json",
  "data": { ... },
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "tracestate": "rojo=00f067aa0ba902b7"
}
```

- **type**: Reverse-DNS event type.
  - `ai.coreason.node.started`
  - `ai.coreason.node.stream`
  - `ai.coreason.node.completed`
- **source**: The producer of the event (e.g., the Node ID).
- **traceparent**: W3C Trace Context header for distributed tracing.

## Distributed Tracing with AgentRequest

Distributed tracing starts at the edge. The `AgentRequest` envelope standardizes the propagation of trace IDs (Root -> Parent -> Child) into the system.

*   **Ingestion:** When an `AgentRequest` is received, the Engine extracts the `root_request_id` and `parent_request_id`.
*   **Propagation:** These IDs are mapped to the W3C `traceparent` header in all subsequent `CloudEvent` emissions.
*   **Visualization:** This lineage allows tools like **Jaeger** or **Arize** to reconstruct the full execution tree, even across asynchronous distributed systems.

See [Agent Request Envelope](agent_request_envelope.md) for implementation details.

## OpenTelemetry GenAI Semantic Conventions

Payloads (`data`) now strictly follow [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/).

### Mappings

| Legacy Field | OTel Attribute | Description |
| :--- | :--- | :--- |
| `input_tokens` | `gen_ai.usage.input_tokens` | Count of input tokens. |
| `model` | `gen_ai.request.model` | The model name (e.g., `gpt-4`). |
| `chunk` | `gen_ai.completion.chunk` | A streamed text chunk. |
| `system` | `gen_ai.system` | The system prompt. |

### Example Payload (`ai.coreason.node.started`)

```json
{
  "node_id": "node-1",
  "status": "RUNNING",
  "gen_ai": {
    "usage": {
      "input_tokens": 150
    },
    "request": {
      "model": "gpt-4"
    }
  }
}
```

## Migration from Legacy `GraphEvent`

A migration utility is provided to convert legacy `GraphEvent` objects to `CloudEvent` format on the fly.

`GraphEvent` is now a discriminated union of specific event types (e.g. `GraphEventNodeStart`, `GraphEventNodeDone`), ensuring strict type safety for payloads.

```python
from coreason_manifest import (
    GraphEvent,
    GraphEventNodeStart,
    migrate_graph_event_to_cloud_event
)

# GraphEvent is a Union type
legacy_event = GraphEventNodeStart(
    event_type="NODE_START",
    # ... fields
)

cloud_event = migrate_graph_event_to_cloud_event(legacy_event)
```

### UI Metadata
Legacy `visual_metadata` and `visual_cue` fields are moved to CloudEvent extensions:
- `com_coreason_ui_cue`: The primary visual cue (e.g., "pulse").
- `com_coreason_ui_metadata`: The full dictionary of UI metadata.

## Reasoning Trace Improvements (v0.10.0)

The `ReasoningTrace` object has been enhanced to better support complex reasoning engines:

*   **Request Lineage**: `ReasoningTrace` now strictly enforces lineage via `request_id` (required), `root_request_id`, and `parent_request_id` fields. This ensures that every trace can be inextricably linked back to the user request that triggered it.
*   **Metadata**: A flexible `metadata` dictionary is available on `ReasoningTrace` to store arbitrary execution context (e.g., `execution_path`, strategies used) without requiring schema changes.
*   **Simplified Steps**: Use `GenAIOperation.thought("content")` to quickly create reasoning steps with auto-generated IDs and default provider settings.
